pipeline {

    agent any

    options {
        disableConcurrentBuilds()
    }

    stages {

        stage('Run Scrapy Spider') {

            steps {

                dir('emailcrawler') {

                    sh '''
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
