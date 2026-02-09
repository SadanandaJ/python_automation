How to Use These Scripts\
Step 1: Setup\
Copy# Install required packages\
pip install -r requirements.txt

# Make scripts executable
chmod +x build_automation.py deploy_to_k8s.py\
Step 2: Configure\
Edit build_config.json with your settings:

Docker registry URL\
Application name and port\
Replica count\
Environment variables\
Step 3: Run Build\
Copy# Run the build automation\
python build_automation.py\
This will:

✅ Run unit tests\
🐳 Build Docker image\
📤 Push to registry\
📝 Generate Kubernetes manifests\
📦 Create build metadata\
Step 4: Deploy\
Copy# Deploy to Kubernetes\
python deploy_to_k8s.py\
🎯 Key Features Explained\
Version Management: Automatically uses git commit hash or timestamp\
Testing Integration: Runs pytest before building\
Docker Image Building: Creates optimized container images\
Registry Push: Pushes images to your container registry\
K8s Manifest Generation: Auto-generates deployment and service YAML\
Build Metadata: Tracks build information for auditing\
Error Handling: Graceful failures with clear error messages\
CI/CD Ready: Easy integration with Jenkins, GitLab, GitHub Actions

📋 Setup Instructions\
GitHub Actions Setup:
Add Repository Secrets (Settings → Secrets and variables → Actions):

KUBE_CONFIG: <base64 encoded kubeconfig file>\
SLACK_WEBHOOK: <your slack webhook URL>\
Enable GitHub Container Registry:

Go to Settings → Actions → General\
Check "Read and write permissions"\
Push code - workflow triggers automatically!

GitLab CI Setup:
Add CI/CD Variables (Settings → CI/CD → Variables):

KUBE_CONTEXT: <your kubernetes context>\
DOCKER_REGISTRY: registry.gitlab.com\
CI_REGISTRY_USER: gitlab-ci-token\
CI_REGISTRY_PASSWORD: $CI_JOB_TOKEN\
Configure GitLab Runner with Docker and kubectl

Push code - pipeline starts automatically!

Jenkins Setup:
Install Required Plugins:

Docker Pipeline\
Kubernetes CLI\
Pipeline\
Git\
Add Credentials:

docker-registry-credentials: Username/password for Docker registry\
kubeconfig-credentials: Kubernetes config file\
Create Pipeline Job:

New Item → Pipeline\
Pipeline → Definition: "Pipeline script from SCM"\
SCM: Git, add your repository URL\
Script Path: Jenkinsfile\
Configure Webhook in your Git repository to trigger builds

🎯 What Each CI/CD Platform Does:
Feature	GitHub Actions	GitLab CI	Jenkins\
Trigger	Push/PR	Push/MR	Webhook/Poll\
Test	✅ pytest + coverage	✅ pytest + coverage	✅ pytest + coverage\
Build	✅ Docker + GHCR	✅ Docker + Registry	✅ Docker + Registry\
Deploy	✅ kubectl	✅ kubectl	✅ kubectl\
Approval	Environment protection	Manual job	Input step\
Artifacts	Upload/Download	GitLab artifacts	Archive artifacts\
🔐 Security Best Practices:
Never commit secrets - use CI/CD variables\
Use image scanning - add Trivy or Snyk\
Enable branch protection - require reviews\
Use namespaces - isolate environments\
Rotate credentials - regularly update tokens\
📊 Monitoring Your Pipelines:
All three platforms provide:

✅ Build logs\
✅ Test reports\
✅ Coverage reports\
✅ Deployment status\
✅ Notifications (Slack/Email)
