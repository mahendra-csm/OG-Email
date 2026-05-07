import scrapy
import re
import unicodedata
from urllib.parse import urlparse
# import winsound  # Windows built-in for notification sounds

# ─────────────────────────────────────────────
# Optional imports — install with:
#   pip install rapidfuzz dnspython
# ─────────────────────────────────────────────
try:
    from rapidfuzz import process, fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    print("[WARN] rapidfuzz not installed. Fuzzy domain correction disabled.")

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    print("[WARN] dnspython not installed. MX record validation disabled.")


# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9]"                    # must start with alphanumeric
    r"[a-zA-Z0-9_.+\-]*"               # local part body
    r"@"
    r"[a-zA-Z0-9]"                     # domain must start with alphanumeric
    r"[a-zA-Z0-9\-]*"                  # domain body
    r"(\.[a-zA-Z0-9\-]+)*"             # sub-domains
    r"\.[a-zA-Z]{2,}$"                 # TLD: at least 2 alpha chars
)

# Hardcoded domain typo corrections (fast-path before fuzzy matching)
DOMAIN_CORRECTIONS = {
    'gmal.com': 'gmail.com', 'gmil.com': 'gmail.com', 'gmail.con': 'gmail.com',
    'gmail.co': 'gmail.com', 'gmail.om': 'gmail.com', 'gmail.cim': 'gmail.com',
    'gmail.cm': 'gmail.com', 'gamil.com': 'gmail.com', 'gnail.com': 'gmail.com',
    'gmaill.com': 'gmail.com', 'gmali.com': 'gmail.com', 'gail.com': 'gmail.com',
    'gemail.com': 'gmail.com', 'gimail.com': 'gmail.com',
    'yahoo.con': 'yahoo.com', 'yahoo.co': 'yahoo.com', 'yahoo.cim': 'yahoo.com',
    'yaho.com': 'yahoo.com', 'yahooo.com': 'yahoo.com', 'yhoo.com': 'yahoo.com',
    'ymail.con': 'ymail.com',
    'rediffmail.con': 'rediffmail.com', 'rediffmail.co': 'rediffmail.com',
    'reddifmail.com': 'rediffmail.com', 'redifmail.com': 'rediffmail.com',
    'outlook.con': 'outlook.com', 'outlook.co': 'outlook.com',
    'hotmail.con': 'hotmail.com', 'hotmail.co': 'hotmail.com',
    'hotmai.com': 'hotmail.com', 'hotmal.com': 'hotmail.com',
    'icloud.con': 'icloud.com', 'icloud.co': 'icloud.com',
    'protonmail.con': 'protonmail.com',
}

# Known valid domains used for fuzzy matching and MX skip
KNOWN_DOMAINS = [
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'rediffmail.com',
    'icloud.com', 'protonmail.com', 'ymail.com', 'yahoo.in', 'yahoo.co.in',
    'live.com', 'msn.com', 'me.com', 'aol.com', 'zoho.com', 'mail.com',
    'gmx.com', 'tutanota.com', 'fastmail.com',
]

# Generic/placeholder local parts — exact and prefix-based
GENERIC_EXACT = {
    'yourmail', 'test', 'example', 'admin', 'info', 'contact', 'support',
    'instagram', 'facebook', 'twitter', 'noreply', 'no-reply', 'user', 'demo',
    'sample', 'mail', 'email', 'hello', 'welcome', 'abc', 'xyz', 'donotreply',
    'do-not-reply', 'postmaster', 'webmaster', 'sales', 'marketing', 'hr',
    'jobs', 'careers', 'billing', 'accounts', 'service', 'helpdesk', 'mailer',
    'newsletter', 'notifications', 'notify', 'alerts', 'bounce', 'bounces',
    'spam', 'junk', 'trash', 'null', 'none', 'na', 'notavailable', 'unknown',
    'temp', 'temporary', 'fake', 'invalid', 'test1', 'test2', 'user1', 'user2',
}

GENERIC_PREFIXES = (
    'noreply', 'no-reply', 'donotreply', 'do-not-reply', 'test', 'admin',
    'info', 'support', 'demo', 'sample', 'mailer', 'newsletter', 'notify',
    'notification', 'alert', 'bounce', 'spam', 'temp', 'fake',
)

# Cache for MX lookups so we don't query the same domain twice
_mx_cache = {}


# ──────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def clean_string(s):
    """Remove hidden/non-printable unicode characters and normalize."""
    if not isinstance(s, str):
        return s
    s = unicodedata.normalize('NFKC', s)
    s = ''.join(c for c in s if c.isprintable())
    return s.strip()


def is_generic_local(local):
    """Return True if the local part looks like a placeholder/generic address."""
    local = local.lower().strip()
    if local in GENERIC_EXACT:
        return True
    if local.startswith(GENERIC_PREFIXES):
        return True
    # All digits → likely fake (e.g. 123@gmail.com)
    if local.isdigit():
        return True
    # Very short (1 char) local parts
    if len(local) < 2:
        return True
    return False


def correct_domain(domain):
    """
    Apply layered domain correction:
      1. Hardcoded typo map (fast)
      2. .eda.in → .edu.in suffix fix
      3. Fuzzy matching against known domains (if rapidfuzz available)
    """
    domain = domain.lower().strip()

    # Layer 1: hardcoded corrections
    if domain in DOMAIN_CORRECTIONS:
        return DOMAIN_CORRECTIONS[domain]

    # Layer 2: suffix pattern fix
    if domain.endswith('.eda.in'):
        domain = domain[:-7] + '.edu.in'

    # Layer 3: fuzzy match (only for domains that look slightly off)
    if RAPIDFUZZ_AVAILABLE:
        result = process.extractOne(domain, KNOWN_DOMAINS, scorer=fuzz.ratio)
        if result:
            match, score, _ = result
            # Only auto-correct if very close (≥88%) to avoid false positives
            if score >= 88 and domain != match:
                return match
                
    return domain


def correct_email(email):
    """Clean hidden chars, strip whitespace, and fix domain typos."""
    if not isinstance(email, str):
        return email
    email = clean_string(email)
    if '@' not in email:
        return email
    local, domain = email.split('@', 1)
    domain = correct_domain(domain)
    return f"{local}@{domain}"


def domain_has_mx(domain):
    """Check if a domain has valid MX records (with caching)."""
    if not DNS_AVAILABLE:
        return True  # Can't verify, so don't drop it
    domain = domain.lower()
    if domain in _mx_cache:
        return _mx_cache[domain]
    try:
        dns.resolver.resolve(domain, 'MX', lifetime=5)
        _mx_cache[domain] = True
    except Exception:
        _mx_cache[domain] = False
    return _mx_cache[domain]


def is_valid_email(email):
    """
    Full multi-layer email validation:
      1. Type & empty check
      2. Hidden character clean
      3. Single @ check
      4. Regex structure check
      5. Local part checks (generic, length, chars)
      6. Domain checks (format, TLD length, double dots, hyphens)
      7. MX record check (if dnspython installed)
    """
    if not isinstance(email, str):
        return False

    email = clean_string(email)
    if not email:
        return False

    # Must have exactly one @
    if email.count('@') != 1:
        return False

    local, domain = email.split('@')

    if not local or not domain:
        return False

    # Reject double dots anywhere
    if '..' in email:
        return False

    # Regex structural check
    if not EMAIL_REGEX.match(email):
        return False

    # Local part: generic/placeholder check
    if is_generic_local(local):
        return False

    # Local part: max length (RFC 5321)
    if len(local) > 64:
        return False

    # Domain: no leading/trailing hyphens on any label
    for label in domain.split('.'):
        if label.startswith('-') or label.endswith('-'):
            return False
        if not label:  # catches domain starting/ending with dot
            return False

    # TLD must be at least 2 chars (already in regex, double-checking)
    tld = domain.rsplit('.', 1)[-1]
    if len(tld) < 2:
        return False

    # Full email max length (RFC 5321)
    if len(email) > 254:
        return False

    # MX record validation for unknown/suspicious domains
    # Skip MX check for well-known domains (speed optimisation)
    if domain.lower() not in KNOWN_DOMAINS:
        if not domain_has_mx(domain):
            return False

    return True


class EmailSpider(scrapy.Spider):
    name = "email_spider"

    def __init__(self, *args, **kwargs):
        super(EmailSpider, self).__init__(*args, **kwargs)
        self.visited_urls = set()
        self.allowed_domains = set()
        self.all_valid_emails = set()  # Store all valid unique emails
        self.emails_per_url = {}  # Track emails count per base URL
        self.domain_to_base_url = {}  # Map domain to original base URL
        self.start_urls = self.load_start_urls()
        # Clear the output files at start
        with open("extracted_emails.txt", "w", encoding="utf-8") as f:
            f.write("")
        with open("report.txt", "w", encoding="utf-8") as f:
            f.write("")

    def load_start_urls(self):
        """ Load websites from 'websites.txt' - supports multiple URLs """
        with open("websites.txt", "r", encoding="utf-8") as f:
            urls = [url.strip() for url in f.readlines() if url.strip() and not url.strip().startswith('#')]
        
        # Initialize tracking for each URL
        for url in urls:
            domain = urlparse(url).netloc
            self.allowed_domains.add(domain)
            self.domain_to_base_url[domain] = url
            self.emails_per_url[url] = set()  # Track unique emails per base URL
        
        print(f"[INFO] Loaded {len(urls)} URL(s) to crawl: {urls}")
        return urls

    # File extensions to skip (non-text content)
    SKIP_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.rar', '.7z', '.tar', '.gz',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
        '.css', '.js', '.woff', '.woff2', '.ttf', '.eot',
    }

    # Maximum URL length to prevent spider traps
    MAX_URL_LENGTH = 500

    def _should_skip_url(self, url):
        """Check if URL points to non-text content or is a spider trap"""
        # Skip overly long URLs (spider trap indicator)
        if len(url) > self.MAX_URL_LENGTH:
            return True
        
        parsed = urlparse(url.lower())
        path = parsed.path
        
        # Skip file extensions
        if any(path.endswith(ext) for ext in self.SKIP_EXTENSIONS):
            return True
        
        # Detect repeating path segments (spider trap)
        if self._has_repeating_segments(path):
            return True
        
        return False

    def _has_repeating_segments(self, path):
        """Detect if a URL path contains repeating segments (spider trap)"""
        segments = [s for s in path.split('/') if s]
        if len(segments) < 4:
            return False
        
        # Check for any segment appearing more than twice
        from collections import Counter
        segment_counts = Counter(segments)
        for segment, count in segment_counts.items():
            if count > 2 and len(segment) > 2:  # Ignore tiny segments like 'a'
                return True
        
        return False

    def parse(self, response):
        """ Extract emails and follow valid links """
        parsed_url = urlparse(response.url)
        domain = parsed_url.netloc

        if domain not in self.allowed_domains:
            return  # Ignore external domains

        # Skip non-text responses (images, PDFs, etc.) using path-based check
        if self._should_skip_url(response.url):
            return

        # Check content-type header
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore').lower()
        
        # Skip binary content types
        binary_types = ['image/', 'video/', 'audio/', 'application/pdf', 'application/zip', 
                        'application/octet-stream', 'font/', 'application/javascript']
        if any(bt in content_type for bt in binary_types):
            return

        self.visited_urls.add(response.url)

        # Extract potential emails using regex (with safe text access)
        try:
            page_text = response.text
        except AttributeError:
            return  # Response is not text-based, skip it
        except AttributeError:
            return  # Response is not text-based, skip it

        potential_emails = set(re.findall(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", 
            page_text
        ))
        
        # Process each email: clean, correct domain typos, validate
        valid_emails = set()
        for email in potential_emails:
            # Step 1: Clean and correct the email
            corrected_email = correct_email(email.lower().strip())
            
            # Step 2: Validate strictly
            if is_valid_email(corrected_email):
                valid_emails.add(corrected_email)
        
        # Add to global set (avoids duplicates across all pages)
        new_emails = valid_emails - self.all_valid_emails
        if new_emails:
            self.all_valid_emails.update(new_emails)
            self.save_emails(new_emails)
            
            # Track emails per base URL for report
            base_url = self.domain_to_base_url.get(domain)
            if base_url:
                self.emails_per_url[base_url].update(new_emails)
            
            # print(f"[OK] Found {len(new_emails)} valid emails from {response.url}")
            for email in sorted(new_emails):
                print(f"[EMAIL FOUND] {email}", flush=True)

        # Follow subdomain links (skip non-text files)
        for href in response.css("a::attr(href)").getall():
            absolute_url = response.urljoin(href)
            parsed_url = urlparse(absolute_url)
            
            # Skip URLs that point to non-text files
            if self._should_skip_url(absolute_url):
                continue

            if parsed_url.netloc in self.allowed_domains and absolute_url not in self.visited_urls:
                yield scrapy.Request(absolute_url, callback=self.parse)

    def save_emails(self, emails):
        """ Save extracted emails to 'extracted_emails.txt' - only emails, no URLs """
        with open("extracted_emails.txt", "a", encoding="utf-8") as f:
            for email in sorted(emails):
                f.write(email + "\n")

    def closed(self, reason):
        """ Called when spider finishes - print summary and generate report """
        # Generate report.txt
        self.generate_report()
        
        print(f"\n{'='*60}")
        print(f"Crawling complete!")
        print(f"Total unique valid emails extracted: {len(self.all_valid_emails)}")
        print(f"Total pages visited: {len(self.visited_urls)}")
        print(f"Emails saved to: extracted_emails.txt")
        print(f"Report saved to: report.txt")
        print(f"{'='*60}")
        
        # Play notification sound to alert user that extraction is complete
        self.play_notification_sound()

    def play_notification_sound(self):
        # """Play a continuous notification sound for 5 seconds when crawling finishes"""
        # try:
        #     # Play continuous alternating beeps for 5 seconds total
        #     # Each cycle: 200ms + 200ms = 400ms, so 12-13 cycles = ~5 seconds
        #     for _ in range(12):
        #         winsound.Beep(800, 200)   # Low tone
        #         winsound.Beep(1200, 200)  # High tone
            
        #     # Final long beep to signal completion
        #     winsound.Beep(1000, 500)
            
        #     print("mail extraction complete! 🔔\n[NOTIFICATION] E")
        # except Exception as e:
        
        print("\n[INFO] Email extraction completed successfully.")

    def generate_report(self):
        """ Generate report.txt with email count per URL """
        from datetime import datetime
        
        with open("report.txt", "w", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write("           EMAIL EXTRACTION REPORT\n")
            f.write("="*60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            f.write("URL-WISE EMAIL COUNT:\n")
            f.write("-"*60 + "\n")
            
            total_emails = 0
            for url in self.start_urls:
                email_count = len(self.emails_per_url.get(url, set()))
                total_emails += email_count
                f.write(f"\n* URL: {url}\n")
                f.write(f"   Emails Extracted: {email_count}\n")
            
            f.write("\n" + "="*60 + "\n")
            f.write("SUMMARY:\n")
            f.write("-"*60 + "\n")
            f.write(f"Total URLs Crawled    : {len(self.start_urls)}\n")
            f.write(f"Total Pages Visited   : {len(self.visited_urls)}\n")
            f.write(f"Total Unique Emails   : {len(self.all_valid_emails)}\n")
            f.write("="*60 + "\n")
        
        print("\n[INFO] Report generated: report.txt")
