pipeline {
    agent any

    stages {

        stage('Clone') {
            steps {
                echo 'Pulling latest code from GitHub'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t emailscrapy-app .'
            }
        }

        stage('Stop Old Container') {
            steps {
                sh '''
                docker stop emailscrapy-container || true
                docker rm emailscrapy-container || true
                '''
            }
        }

        stage('Run New Container') {
            steps {
                sh '''
                docker run -d \
                -p 80:80 \
                --name emailscrapy-container \
                emailscrapy-app
                '''
            }
        }
    }
}
