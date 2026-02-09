How to Use These Scripts\
Step 1: Setup\
Copy# Install required packages\
pip install -r requirements.txt\

# Make scripts executable\
chmod +x build_automation.py deploy_to_k8s.py\
Step 2: Configure\
Edit build_config.json with your settings:\

Docker registry URL\
Application name and port\
Replica count\
Environment variables\
Step 3: Run Build\
Copy# Run the build automation\
python build_automation.py\
This will:\

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
CI/CD Ready: Easy integration with Jenkins, GitLab, GitHub Actions\
