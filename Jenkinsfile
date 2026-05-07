pipeline {
    agent any

    stages {

        stage('Build Docker Image') {
            steps {
                dir('emailcrawler') {
                    sh 'docker build -t emailscrapy-app .'
                }
            }
        }

        stage('Remove Old Container') {
            steps {
                sh '''
                docker stop emailscrapy-container || true
                docker rm emailscrapy-container || true
                '''
            }
        }

        stage('Run Scrapy Spider') {
            steps {
                sh '''
                docker run --name emailscrapy-container emailscrapy-app
                '''
            }
        }

        stage('Copy Output Files') {
            steps {
                sh '''
                docker cp emailscrapy-container:/app/extracted_emails.txt .
                docker cp emailscrapy-container:/app/report.txt .
                '''
            }
        }

        stage('Display Extracted Emails') {
            steps {
                sh '''
                echo "========== EXTRACTED EMAILS =========="
                cat extracted_emails.txt || true
                echo "======================================"
                '''
            }
        }

        stage('Display Report') {
            steps {
                sh '''
                echo "=============== REPORT ==============="
                cat report.txt || true
                echo "======================================"
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '*.txt', allowEmptyArchive: true
        }
    }
}
