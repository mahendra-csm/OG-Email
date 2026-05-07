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

        stage('Show Logs') {
            steps {
                sh '''
                docker logs emailscrapy-container || true
                '''
            }
        }
    }
}
