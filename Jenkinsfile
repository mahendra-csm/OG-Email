pipeline {
    agent any

    stages {

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
                    '''
                }
            }
        }
    }
}
