// Jenkins Pipeline for Python DevOps Build and Deployment

pipeline {
    agent any
    
    environment {
        APP_NAME = 'myapp'
        DOCKER_REGISTRY = 'your-registry.example.com'
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/${APP_NAME}"
        PYTHON_VERSION = '3.11'
        KUBE_NAMESPACE = 'production'
        DOCKER_CREDENTIALS_ID = 'docker-registry-credentials'
        KUBE_CREDENTIALS_ID = 'kubeconfig-credentials'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "Checking out code..."
                    checkout scm
                    
                    // Get git information
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                    
                    env.GIT_BRANCH = sh(
                        script: "git rev-parse --abbrev-ref HEAD",
                        returnStdout: true
                    ).trim()
                    
                    echo "Building commit: ${env.GIT_COMMIT_SHORT} on branch: ${env.GIT_BRANCH}"
                }
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                script {
                    echo "Setting up Python ${PYTHON_VERSION}..."
                    sh """
                        python3 --version
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install pytest pytest-cov pyyaml
                    """
                }
            }
        }
        
        stage('Lint and Code Quality') {
            steps {
                script {
                    echo "Running code quality checks..."
                    sh """
                        . venv/bin/activate
                        pip install flake8 black pylint
                        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
                        black --check . || true
                    """
                }
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                script {
                    echo "Running unit tests..."
                    sh """
                        . venv/bin/activate
                        pytest tests/ -v --cov=. --cov-report=xml --cov-report=html --cov-report=term
                    """
                }
            }
            post {
                always {
                    // Publish test results
                    junit allowEmptyResults: true, testResults: '**/test-results/*.xml'
                    
                    // Publish coverage report
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                script {
                    echo "Running security scans..."
                    sh """
                        . venv/bin/activate
                        pip install bandit safety
                        bandit -r . -f json -o bandit-report.json || true
                        safety check || true
                    """
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                }
            }
        }
        
        stage('Build Docker Image') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                script {
                    echo "Building Docker image..."
                    
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "${DOCKER_CREDENTIALS_ID}") {
                        def customImage = docker.build(
                            "${DOCKER_IMAGE}:${env.GIT_COMMIT_SHORT}",
                            "--build-arg BUILD_DATE=\$(date -u +'%Y-%m-%dT%H:%M:%SZ') " +
                            "--build-arg VCS_REF=${env.GIT_COMMIT_SHORT} " +
                            "."
                        )
                        
                        // Push image with commit SHA tag
                        customImage.push()
                        
                        // Also push as latest
                        customImage.push('latest')
                        
                        echo "Docker image pushed: ${DOCKER_IMAGE}:${env.GIT_COMMIT_SHORT}"
                    }
                }
            }
        }
        
        stage('Generate Kubernetes Manifests') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                script {
                    echo "Generating Kubernetes manifests..."
                    sh """
                        . venv/bin/activate
                        python build_automation.py
                        ls -la build/
                    """
                }
            }
            post {
                success {
                    archiveArtifacts artifacts: 'build/**/*', fingerprint: true
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    echo "Deploying to staging environment..."
                    
                    withKubeConfig([credentialsId: "${KUBE_CREDENTIALS_ID}"]) {
                        sh """
                            kubectl create namespace staging --dry-run=client -o yaml | kubectl apply -f -
                            
                            # Update image in deployment
                            sed -i 's|IMAGE_PLACEHOLDER|${DOCKER_IMAGE}:${env.GIT_COMMIT_SHORT}|g' build/deployment.yaml
                            
                            kubectl apply -f build/ -n staging
                            kubectl rollout status deployment/${APP_NAME}-deployment -n staging --timeout=5m
                            kubectl get pods -n staging -l app=${APP_NAME}
                        """
                    }
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Manual approval for production
                    input message: 'Deploy to production?', ok: 'Deploy'
                    
                    echo "Deploying to production environment..."
                    
                    withKubeConfig([credentialsId: "${KUBE_CREDENTIALS_ID}"]) {
                        sh """
                            kubectl create namespace production --dry-run=client -o yaml | kubectl apply -f -
                            
                            # Update image in deployment
                            sed -i 's|IMAGE_PLACEHOLDER|${DOCKER_IMAGE}:${env.GIT_COMMIT_SHORT}|g' build/deployment.yaml
                            
                            # Apply manifests
                            kubectl apply -f build/ -n production
                            
                            # Wait for rollout
                            kubectl rollout status deployment/${APP_NAME}-deployment -n production --timeout=10m
                            
                            # Show deployment status
                            kubectl get pods -n production -l app=${APP_NAME}
                            kubectl get services -n production -l app=${APP_NAME}
                        """
                    }
                }
            }
        }
        
        stage('Verify Deployment') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "Verifying deployment health..."
                    
                    withKubeConfig([credentialsId: "${KUBE_CREDENTIALS_ID}"]) {
                        sh """
                            # Get service endpoint
                            SERVICE_IP=\$(kubectl get service ${APP_NAME}-service -n production -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
                            
                            # Health check
                            curl -f http://\$SERVICE_IP/health || exit 1
                            
                            echo "Health check passed!"
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up workspace
            cleanWs()
        }
        
        success {
            script {
                echo "✅ Pipeline completed successfully!"
                
                // Send Slack notification (if configured)
                // slackSend(
                //     color: 'good',
                //     message: "Build ${env.BUILD_NUMBER} succeeded for ${env.JOB_NAME}",
                //     channel: '#devops'
                // )
            }
        }
        
        failure {
            script {
                echo "❌ Pipeline failed!"
                
                // Send Slack notification (if configured)
                // slackSend(
                //     color: 'danger',
                //     message: "Build ${env.BUILD_NUMBER} failed for ${env.JOB_NAME}",
                //     channel: '#devops'
                // )
            }
        }
    }
}
