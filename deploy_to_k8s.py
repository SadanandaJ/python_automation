#!/usr/bin/env python3
"""
deploy_to_k8s.py - Deploy application to Kubernetes cluster
"""

import subprocess
import json
from pathlib import Path

class KubernetesDeployer:
    def __init__(self, namespace='default'):
        self.namespace = namespace
        self.build_dir = Path('build')
    
    def check_cluster_connection(self):
        """Verify kubectl can connect to cluster"""
        print("🔍 Checking cluster connection...")
        try:
            result = subprocess.run(
                ['kubectl', 'cluster-info'],
                capture_output=True,
                check=True
            )
            print("✅ Connected to Kubernetes cluster")
            return True
        except subprocess.CalledProcessError:
            print("❌ Cannot connect to Kubernetes cluster")
            return False
    
    def create_namespace(self):
        """Create namespace if it doesn't exist"""
        print(f"📦 Creating namespace: {self.namespace}")
        subprocess.run(
            ['kubectl', 'create', 'namespace', self.namespace],
            capture_output=True
        )
    
    def apply_manifests(self):
        """Apply Kubernetes manifests"""
        print("🚀 Deploying to Kubernetes...")
        
        manifests = list(self.build_dir.glob('*.yaml'))
        
        for manifest in manifests:
            print(f"   Applying {manifest.name}...")
            subprocess.run(
                ['kubectl', 'apply', '-f', str(manifest), '-n', self.namespace],
                check=True
            )
        
        print("✅ Deployment complete!")
    
    def wait_for_rollout(self, deployment_name):
        """Wait for deployment to complete"""
        print(f"⏳ Waiting for rollout of {deployment_name}...")
        subprocess.run(
            ['kubectl', 'rollout', 'status', f'deployment/{deployment_name}',
             '-n', self.namespace],
            check=True
        )
        print("✅ Rollout complete!")
    
    def get_service_info(self, service_name):
        """Get service endpoint information"""
        print(f"📡 Getting service info for {service_name}...")
        result = subprocess.run(
            ['kubectl', 'get', 'service', service_name, '-n', self.namespace,
             '-o', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        service = json.loads(result.stdout)
        return service
    
    def deploy(self, app_name):
        """Execute complete deployment"""
        if not self.check_cluster_connection():
            return False
        
        self.create_namespace()
        self.apply_manifests()
        self.wait_for_rollout(f"{app_name}-deployment")
        
        service_info = self.get_service_info(f"{app_name}-service")
        print(f"\n✅ Deployment successful!")
        print(f"🌐 Service: {service_info['metadata']['name']}")
        
        return True

if __name__ == "__main__":
    deployer = KubernetesDeployer(namespace='production')
    deployer.deploy('myapp')
