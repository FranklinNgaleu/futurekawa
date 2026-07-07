pipeline {
    agent { label 'windows' }

    environment {
        PYTHON = "${env.PYTHON ?: 'python'}"
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
                ) > .env
                '''
            }
        }

        stage('Qualite de code') {
            steps {
                bat '''
                %PYTHON% -m pip install --quiet flake8
                %PYTHON% -m flake8 backend-country backend-central --max-line-length=120 --exit-zero > flake8-report.txt
                '''
            }
        }

        stage('Tests unitaires') {
            steps {
                bat '''
                %PYTHON% -m pip install --quiet -r backend-country\\requirements.txt -r tests\\requirements.txt
                if not exist reports mkdir reports
                %PYTHON% -m pytest tests\\unit -v --junitxml=reports\\unit.xml
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
                bat '''
                set TIMEOUT=60
                set ELAPSED=0

                :waitloop
                curl -sf http://localhost:8000/health >nul 2>&1
                if %ERRORLEVEL% EQU 0 (
                    curl -sf http://localhost:8001/health >nul 2>&1
                    if %ERRORLEVEL% EQU 0 goto ready
                )

                if %ELAPSED% GEQ %TIMEOUT% (
                    echo Timeout en attente des APIs.
                    exit /b 1
                )

                timeout /t 5 /nobreak >nul
                set /a ELAPSED+=5
                goto waitloop

                :ready
                echo APIs disponibles.
                '''
            }
        }

        stage('Tests API/MQTT') {
            steps {
                bat '''
                %PYTHON% -m pip install --quiet -r tests\\requirements.txt
                if not exist reports mkdir reports
                %PYTHON% -m pytest tests\\api -v --junitxml=reports\\api.xml --cov=. --cov-report=xml:reports\\coverage.xml
                '''
            }
        }

        stage('Packaging') {
            steps {
                bat '''
                if not exist artifacts mkdir artifacts

                docker tag futurekawa/backend-country:latest futurekawa/backend-country:%BUILD_NUMBER%
                docker tag futurekawa/backend-central:latest futurekawa/backend-central:%BUILD_NUMBER%
                docker tag futurekawa/frontend:latest futurekawa/frontend:%BUILD_NUMBER%

                docker save futurekawa/backend-country:%BUILD_NUMBER% -o artifacts\\backend-country.tar
                docker save futurekawa/backend-central:%BUILD_NUMBER% -o artifacts\\backend-central.tar
                docker save futurekawa/frontend:%BUILD_NUMBER% -o artifacts\\frontend.tar
                '''
            }
        }
    }

    post {
        always {
            junit 'reports/*.xml'
            archiveArtifacts artifacts: 'artifacts/*.tar, reports/*, flake8-report.txt', allowEmptyArchive: true

            bat 'docker compose down'
            bat 'if exist .env del /f /q .env'
        }
    }
}
