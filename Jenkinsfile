pipeline {
    agent any

    environment {
        SMTP_HOST = 'smtp.gmail.com'
        SMTP_PORT = '587'
        SMTP_USER = credentials('smtp_user')
        SMTP_PASSWORD = credentials('smtp_password')
        ALERT_EMAIL_TO = credentials('smtp_user')
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare .env') {
            steps {
                bat '''
                (
                echo SMTP_HOST=%SMTP_HOST%
                echo SMTP_PORT=%SMTP_PORT%
                echo SMTP_USER=%SMTP_USER%
                echo SMTP_PASSWORD=%SMTP_PASSWORD%
                echo ALERT_EMAIL_TO=%ALERT_EMAIL_TO%
                ) > backend-country\\.env
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                bat 'docker compose build'
            }
        }

        stage('Start Services') {
            steps {
                bat 'docker compose up -d'
            }
        }

        stage('Wait for APIs') {
            steps {
                bat 'powershell -Command "Start-Sleep -Seconds 20"'
            }
        }

        stage('Run Tests') {
            steps {
                bat 'python -m pip install -r tests/requirements.txt'
                bat 'python -m pytest tests/api -v'
            }
        }
    }

    post {
        always {
            bat 'docker compose down'

            bat '''
            if exist backend-country\\.env (
                del backend-country\\.env
            )
            '''
        }

        success {
            echo 'Pipeline terminé avec succès'
        }

        failure {
            echo 'Pipeline échoué'
        }
    }
}