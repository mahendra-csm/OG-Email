# EC2 automation for daily email extraction

This repository already supports the workflow you described:

1. You update `emailcrawler/websites.txt` in GitHub.
2. The crawler runs automatically.
3. Fresh results are written to:
   - `emailcrawler/extracted_emails.txt`
   - `emailcrawler/report.txt`
4. Old output is replaced on every run.

## Option A: GitHub-hosted runner

The included GitHub Actions workflow runs on `ubuntu-latest` whenever `emailcrawler/websites.txt` changes.

## Option B: EC2 self-hosted runner

If you want the job to execute on your EC2 instance instead:

1. Launch an Ubuntu EC2 instance.
2. Install Python 3.11, Git, and the dependencies from `requirements.txt`.
3. Register the EC2 instance as a GitHub self-hosted runner for this repository.
4. Change the workflow `runs-on` value from `ubuntu-latest` to your self-hosted label.

## Daily flow

For the simplest process, keep using the same file name:

- upload/edit `emailcrawler/websites.txt`
- wait for the workflow to finish
- download the updated `emailcrawler/extracted_emails.txt`

## Notes

- The crawler clears output files at the beginning of each run, so yesterday’s data is removed automatically.
- The workflow only commits output changes, so the repo stays clean when no new emails are found.