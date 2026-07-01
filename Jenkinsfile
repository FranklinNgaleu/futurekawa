pipeline {
    agent any

    environment {
        SMTP_HOST = 'smtp.gmail.com'
        SMTP_PORT = '587'
        SMTP_USER = credentials('smtp_user')
        SMTP_PASSWORD = credentials('smtp_password')
        ALERT_EMAIL_TO = credentials('smtp_user')
        SONAR_TOKEN = credentials('sonar-token')
        SONAR_HOST_URL = 'http://localhost:9000'
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
                bat '"C:\\Users\\frank\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" -m pip install -r tests/requirements.txt'
                bat '"C:\\Users\\frank\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" -m pytest tests/api -v --cov=. --cov-report=xml'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                bat '''
                docker run --rm ^
                -e SONAR_HOST_URL=http://host.docker.internal:9000 ^
                -e SONAR_TOKEN=%SONAR_TOKEN% ^
                -v "%cd%:/usr/src" ^
                sonarsource/sonar-scanner-cli
                '''
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