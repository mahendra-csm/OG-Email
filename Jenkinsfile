pipeline {
    agent any

    stages {

        stage('Pull Code') {
            steps {
                echo 'Pulling latest code from GitHub'
            }
        }

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
    }
}
