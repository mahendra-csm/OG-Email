pipeline {

    agent any

    options {
        disableConcurrentBuilds()
    }

    stages {

        stage('Run Email Spider') {

            steps {

                dir('emailcrawler') {

                    sh '''
                    echo "========== CLEAN OLD CONTAINER =========="

                    docker rm -f emailscrapy-container || true

                    echo "========== BUILD IMAGE =========="

                    docker build -t emailscrapy-app .

                    echo "========== RUN SCRAPY SPIDER =========="

                    docker run --name emailscrapy-container emailscrapy-app

                    echo "========== COPY OUTPUT FILES =========="

                    docker cp emailscrapy-container:/app/extracted_emails.txt .

                    docker cp emailscrapy-container:/app/report.txt .

                    echo "========== EXTRACTED EMAILS =========="

                    cat extracted_emails.txt || true

                    echo "========== REPORT =========="

                    cat report.txt || true
                    '''
                }
            }
        }
    }

    post {

        always {

            archiveArtifacts artifacts: 'emailcrawler/*.txt', allowEmptyArchive: true
        }

        success {

            echo 'Pipeline completed successfully.'
        }

        failure {

            echo 'Pipeline failed.'
        }
    }
}
