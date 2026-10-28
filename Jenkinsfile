pipeline {
    agent any

    environment {
        IMAGE_NAME = 'tejaswani2028/inventory-management-system'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker version'
                bat 'docker build -t %IMAGE_NAME%:%BUILD_NUMBER% .'
                bat 'docker tag %IMAGE_NAME%:%BUILD_NUMBER% %IMAGE_NAME%:latest'
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )
                ]) {
                    bat '''
                        @echo off
                        echo Logging in to Docker Hub...
                        docker login -u "%DOCKER_USER%" --password-stdin < nul
                    '''
                    powershell '''
                        $ErrorActionPreference = "Stop"
                        $env:DOCKER_PASS | docker login -u "$env:DOCKER_USER" --password-stdin
                        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                        docker push "$env:IMAGE_NAME`:$env:BUILD_NUMBER"
                        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                        docker push "$env:IMAGE_NAME`:latest"
                        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'kubeconfig',
                        variable: 'KUBECONFIG_FILE'
                    )
                ]) {
                    powershell '''
                        $env:KUBECONFIG = $env:KUBECONFIG_FILE

                        kubectl apply -f k8s/
                        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

                        kubectl set image deployment/inventory-app "inventory-app=$env:IMAGE_NAME`:$env:BUILD_NUMBER"
                        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

                        kubectl rollout status deployment/inventory-app --timeout=120s
                        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                    '''
                }
            }
        }
    }
}