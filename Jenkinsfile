pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Récupération du code source'
                checkout scm
            }
        }

        stage('Build Docker Images') {
            steps {
                echo 'Build des images Docker'
                bat 'docker compose build'
            }
        }

        stage('Start Services') {
            steps {
                echo 'Démarrage des services FutureKawa'
                bat 'docker compose up -d'
            }
        }

        stage('Wait for APIs') {
            steps {
                echo 'Attente du démarrage des APIs'
                bat 'powershell -Command "Start-Sleep -Seconds 15"'
            }
        }

        stage('Run API Tests') {
            steps {
                echo 'Exécution des tests API'
                bat 'pip install -r tests/requirements.txt'
                bat 'pytest tests/api -v'
            }
        }
    }

    post {
        always {
            echo 'Arrêt des conteneurs Docker'
            bat 'docker compose down'
        }

        success {
            echo 'Pipeline terminé avec succès'
        }

        failure {
            echo 'Pipeline échoué'
        }
    }
}