pipeline {

    agent any

    stages {

        stage('Build Docker Image') {

            steps {

                dir('emailcrawler') {

                    sh '''
                    docker build -t emailscrapy-app .
                    '''
                }
            }
        }

        stage('Run Scrapy Spider') {

            steps {

                dir('emailcrawler') {

                    sh '''
                    docker stop emailscrapy-container || true
                    docker rm emailscrapy-container || true

                    docker run --name emailscrapy-container emailscrapy-app

                    docker cp emailscrapy-container:/app/extracted_emails.txt .

                    echo "========== EXTRACTED EMAILS =========="
                    cat extracted_emails.txt || true
                    echo "======================================"

                    echo "============= REPORT ================="
                    cat report.txt || true
                    echo "======================================"
                    '''
                }
            }
        }

        stage('Cleanup Memory') {

            steps {

                sh '''
                docker container prune -f
                docker image prune -af
                docker builder prune -af
                '''
            }
        }
    }
}
