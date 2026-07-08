// ============================================================
// FutureKawa - Pipeline CI/CD Jenkins
// ============================================================
//
// Prerequis sur l'agent Jenkins :
//   - Un agent Windows portant le label defini par le parametre AGENT_LABEL
//     (par defaut "windows").
//   - Python 3.11+ installe et accessible dans le PATH de l'agent, ou expose
//     via la variable d'environnement PYTHON (voir bloc "environment"
//     ci-dessous) si l'executable ne s'appelle pas simplement "python".
//   - Docker Desktop (ou Docker Engine) avec le plugin Compose v2 installes
//     et demarres : le pipeline pilote la stack via `docker compose
//     build/up/down`.
//   - curl disponible dans le PATH (utilise pour attendre que les API et le
//     frontend soient prets avant de lancer les tests d'integration).
//   - Google Chrome installe sur l'agent si le parametre RUN_UI_TESTS est a
//     true : les tests Selenium tournent en mode headless et le driver
//     Chrome est telecharge automatiquement par webdriver-manager, mais le
//     navigateur lui-meme doit deja etre present sur la machine.
//
// Secrets / identifiants (a fournir via les variables d'environnement du job
// Jenkins, ou via des "Credentials" Jenkins injectees en variables
// d'environnement - ne jamais les coder en dur ici) :
//   - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD : acces au serveur SMTP
//     utilise pour les emails d'alerte.
//   - ALERT_EMAIL_TO : adresse de repli generique pour les alertes.
//   - ALERT_EMAIL_TO_BRESIL, ALERT_EMAIL_TO_EQUATEUR, ALERT_EMAIL_TO_COLOMBIE :
//     adresses specifiques par pays (utilisees en priorite, avec repli sur
//     ALERT_EMAIL_TO si absentes - voir backend-country/app/email_service.py).
//   Si ces variables sont absentes de l'environnement Jenkins, le pipeline
//   fonctionne quand meme (l'envoi d'email echoue silencieusement cote
//   backend), mais ne constitue alors pas un test representatif de l'envoi
//   reel des emails.
//
// Parametres du job (modifiables sans toucher a ce fichier) :
//   - RUN_UI_TESTS (booleen, defaut true) : active/desactive la stage de
//     tests Selenium. A desactiver sur un agent sans navigateur Chrome.
//   - AGENT_LABEL (texte, defaut "windows") : label de l'agent Jenkins a
//     utiliser, pour rejouer ce pipeline sur un autre pool d'agents.
//
// Interpretation des artefacts publies en fin de build :
//   - reports/unit.xml, reports/api.xml, reports/ui.xml : resultats JUnit de
//     chaque suite de tests (tests unitaires, tests API/MQTT, tests
//     Selenium), publies via l'etape `junit` et visibles dans l'onglet
//     "Test Result" du build.
//   - reports/coverage-unit.xml, reports/coverage-api.xml,
//     reports/coverage-ui.xml : rapports de couverture de code (format
//     Cobertura), a consommer par un plugin de couverture Jenkins. Seule la
//     couverture issue des tests unitaires (qui importent directement le
//     code de backend-country) est pleinement representative : les tests
//     API/MQTT et UI s'executent contre la stack Dockerisee via HTTP/MQTT et
//     mesurent donc surtout la couverture des fichiers de test eux-memes.
//   - flake8-report.txt : sortie brute de l'analyse statique flake8, utile
//     pour lister les violations en cas d'echec de la stage "Qualite de
//     code" (la stage est desormais bloquante : tout code non nul de flake8
//     fait echouer le build).
//   - artifacts/*.tar : images Docker (backend-country, backend-central,
//     frontend) exportees et taguees avec le numero de build, pour permettre
//     un `docker load` et un deploiement manuel sur un autre environnement.

pipeline {
    agent { label "${params.AGENT_LABEL}" }

    parameters {
        booleanParam(
            name: 'RUN_UI_TESTS',
            defaultValue: true,
            description: 'Executer la stage de tests UI Selenium (necessite Chrome sur l\'agent).'
        )
        string(
            name: 'AGENT_LABEL',
            defaultValue: 'windows',
            description: 'Label de l\'agent Jenkins sur lequel executer ce pipeline.'
        )
    }

    environment {
        // Permet de surcharger l'executable Python sans modifier ce fichier
        // (utile si l'agent expose "python3" ou un chemin complet).
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
                // Genere le fichier .env consomme par docker-compose.yml a
                // partir des variables d'environnement/credentials du job
                // Jenkins (voir bloc de commentaires en tete de fichier).
                bat '''
                (
                    echo SMTP_HOST=%SMTP_HOST%
                    echo SMTP_PORT=%SMTP_PORT%
                    echo SMTP_USER=%SMTP_USER%
                    echo SMTP_PASSWORD=%SMTP_PASSWORD%
                    echo ALERT_EMAIL_TO=%ALERT_EMAIL_TO%
                    echo ALERT_EMAIL_TO_BRESIL=%ALERT_EMAIL_TO_BRESIL%
                    echo ALERT_EMAIL_TO_EQUATEUR=%ALERT_EMAIL_TO_EQUATEUR%
                    echo ALERT_EMAIL_TO_COLOMBIE=%ALERT_EMAIL_TO_COLOMBIE%
                ) > .env
                '''
            }
        }

        stage('Qualite de code') {
            steps {
                // Analyse statique bloquante : tout code de retour non nul
                // (au moins une violation) fait echouer cette stage, et donc
                // le build. Le rapport est tout de meme archive (voir bloc
                // "post") pour permettre de lister les violations.
                bat '''
                %PYTHON% -m pip install --quiet flake8
                %PYTHON% -m flake8 backend-country backend-central --max-line-length=120 > flake8-report.txt
                '''
            }
        }

        stage('Tests unitaires') {
            steps {
                // Tests unitaires : importent directement le code Python de
                // backend-country (pas de Docker), la couverture mesuree ici
                // est donc representative du code applicatif reel.
                bat '''
                %PYTHON% -m pip install --quiet -r backend-country\\requirements.txt -r tests\\requirements.txt
                if not exist reports mkdir reports
                %PYTHON% -m pytest tests\\unit -v --junitxml=reports\\unit.xml --cov=. --cov-report=xml:reports\\coverage-unit.xml
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
                    if %ERRORLEVEL% EQU 0 (
                        curl -sf http://localhost:3000 >nul 2>&1
                        if %ERRORLEVEL% EQU 0 goto ready
                    )
                )

                if %ELAPSED% GEQ %TIMEOUT% (
                    echo Timeout en attente des API/frontend.
                    exit /b 1
                )

                timeout /t 5 /nobreak >nul
                set /a ELAPSED+=5
                goto waitloop

                :ready
                echo API et frontend disponibles.
                '''
            }
        }

        stage('Tests API/MQTT') {
            steps {
                // Inclut au moins deux tests d'integration MQTT reels
                // (paho-mqtt, un par broker Mosquitto pays) dans
                // tests/api/test_mqtt_integration.py.
                bat '''
                %PYTHON% -m pip install --quiet -r tests\\requirements.txt
                if not exist reports mkdir reports
                %PYTHON% -m pytest tests\\api -v --junitxml=reports\\api.xml --cov=. --cov-report=xml:reports\\coverage-api.xml
                '''
            }
        }

        stage('Tests UI') {
            when {
                expression { return params.RUN_UI_TESTS }
            }
            steps {
                // Tests Selenium en headless Chrome contre la stack demarree
                // ci-dessus. Desactivable via le parametre RUN_UI_TESTS sur
                // un agent sans navigateur disponible.
                bat '''
                %PYTHON% -m pip install --quiet -r tests\\requirements.txt
                if not exist reports mkdir reports
                %PYTHON% -m pytest tests\\ui -v -m ui --junitxml=reports\\ui.xml --cov=. --cov-report=xml:reports\\coverage-ui.xml
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
