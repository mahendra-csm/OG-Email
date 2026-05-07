pipeline {
    agent any

    stages {

        stage('Clone Repository') {
            steps {
                git 'https://github.com/Karim-786/EmailScrapy-OG.git'
            }
        }

        stage('Move To Scrapy Folder') {
            steps {
                dir('emailcrawler') {

                    sh '''
                    docker build -t emailscrapy-app .

                    docker stop emailscrapy-container || true
                    docker rm emailscrapy-container || true

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

    post {
        always {
            archiveArtifacts artifacts: 'emailcrawler/extracted_emails.txt', allowEmptyArchive: true
        }
    }
}
