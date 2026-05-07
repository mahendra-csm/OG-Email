pipeline {
    agent any

    stages {

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t emailscrapy-app .'
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

        stage('Copy Extracted Files') {
            steps {
                sh '''
                docker cp emailscrapy-container:/app/emailcrawler/extracted_emails.txt .
                docker cp emailscrapy-container:/app/emailcrawler/report.txt .
                '''
            }
        }

        stage('Show Extracted Emails') {
            steps {
                sh '''
                echo "================ EXTRACTED EMAILS ================"
                cat extracted_emails.txt || true
                echo "================================================="
                '''
            }
        }

        stage('Show Report') {
            steps {
                sh '''
                echo "================ REPORT ================"
                cat report.txt || true
                echo "========================================"
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
