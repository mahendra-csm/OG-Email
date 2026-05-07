pipeline {
    agent any
    options {
        disableConcurrentBuilds()
    }

    stages {

        stage('Clone Repository') {
            steps {
                git 'https://github.com/Karim-786/EmailScrapy-OG.git'
            }
        }

        stage('Run Scrapy Spider') {

            steps {

                dir('emailcrawler') {

                    sh '''
                    docker stop emailscrapy-container || true
                     docker rm -f emailscrapy-container || true

                    docker run --name emailscrapy-container emailscrapy-app

                    docker cp emailscrapy-container:/app/extracted_emails.txt .

                    echo "========== EXTRACTED EMAILS =========="
                    cat extracted_emails.txt || true
                    echo "======================================"
                    '''
                }
            }
        }
    }
}
