#!/usr/bin/env python3
"""
build_automation.py - Automate Python application builds and artifact generation
"""

import os
import sys
import subprocess
import json
import hashlib
from datetime import datetime
from pathlib import Path

class BuildAutomation:
    def __init__(self, config_file="build_config.json"):
        """Initialize build automation with configuration"""
        self.config = self.load_config(config_file)
        self.build_dir = Path(self.config.get('build_dir', 'build'))
        self.app_name = self.config.get('app_name', 'myapp')
        self.version = self.get_version()
        
    def load_config(self, config_file):
        """Load build configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file {config_file} not found, using defaults")
            return {}
    
    def get_version(self):
        """Generate version from git commit or timestamp"""
        try:
            # Try to get git commit hash
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            # Fallback to timestamp
            return datetime.now().strftime('%Y%m%d%H%M%S')
    
    def run_tests(self):
        """Run unit tests before building"""
        print("🧪 Running unit tests...")
        try:
            subprocess.run(
                ['pytest', 'tests/', '-v', '--cov=.'],
                check=True
            )
            print("✅ Tests passed!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Tests failed! Build aborted.")
            return False
        except FileNotFoundError:
            print("⚠️  pytest not found, skipping tests")
            return True
    
    def install_dependencies(self):
        """Install production dependencies"""
        print("📦 Installing dependencies...")
        try:
            subprocess.run(
                ['pip', 'install', '-r', 'requirements.txt', '--no-cache-dir'],
                check=True
            )
            print("✅ Dependencies installed!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False
    
    def build_docker_image(self):
        """Build Docker image for the application"""
        image_tag = f"{self.app_name}:{self.version}"
        print(f"🐳 Building Docker image: {image_tag}")
        
        try:
            subprocess.run(
                ['docker', 'build', '-t', image_tag, '.'],
                check=True
            )
            
            # Also tag as latest
            subprocess.run(
                ['docker', 'tag', image_tag, f"{self.app_name}:latest"],
                check=True
            )
            
            print(f"✅ Docker image built: {image_tag}")
            return image_tag
        except subprocess.CalledProcessError:
            print("❌ Docker build failed")
            return None
    
    def push_to_registry(self, image_tag):
        """Push Docker image to container registry"""
        registry = self.config.get('docker_registry', 'localhost:5000')
        full_image = f"{registry}/{image_tag}"
        
        print(f"📤 Pushing image to registry: {full_image}")
        
        try:
            # Tag for registry
            subprocess.run(
                ['docker', 'tag', image_tag, full_image],
                check=True
            )
            
            # Push to registry
            subprocess.run(
                ['docker', 'push', full_image],
                check=True
            )
            
            print(f"✅ Image pushed: {full_image}")
            return full_image
        except subprocess.CalledProcessError:
            print("❌ Failed to push image")
            return None
    
    def generate_kubernetes_manifests(self, image_name):
        """Generate Kubernetes deployment manifests"""
        print("📝 Generating Kubernetes manifests...")
        
        self.build_dir.mkdir(exist_ok=True)
        
        # Deployment manifest
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': f"{self.app_name}-deployment",
                'labels': {'app': self.app_name}
            },
            'spec': {
                'replicas': self.config.get('replicas', 3),
                'selector': {
                    'matchLabels': {'app': self.app_name}
                },
                'template': {
                    'metadata': {
                        'labels': {'app': self.app_name, 'version': self.version}
                    },
                    'spec': {
                        'containers': [{
                            'name': self.app_name,
                            'image': image_name,
                            'ports': [{'containerPort': self.config.get('port', 8000)}],
                            'env': self.config.get('env_vars', []),
                            'resources': {
                                'requests': {
                                    'memory': '256Mi',
                                    'cpu': '250m'
                                },
                                'limits': {
                                    'memory': '512Mi',
                                    'cpu': '500m'
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        # Service manifest
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f"{self.app_name}-service"
            },
            'spec': {
                'selector': {'app': self.app_name},
                'ports': [{
                    'protocol': 'TCP',
                    'port': 80,
                    'targetPort': self.config.get('port', 8000)
                }],
                'type': 'LoadBalancer'
            }
        }
        
        # Write manifests to files
        deployment_file = self.build_dir / 'deployment.yaml'
        service_file = self.build_dir / 'service.yaml'
        
        import yaml
        with open(deployment_file, 'w') as f:
            yaml.dump(deployment, f)
        
        with open(service_file, 'w') as f:
            yaml.dump(service, f)
        
        print(f"✅ Manifests generated in {self.build_dir}/")
        return [deployment_file, service_file]
    
    def create_build_metadata(self, image_name):
        """Create build metadata file"""
        metadata = {
            'app_name': self.app_name,
            'version': self.version,
            'image': image_name,
            'build_time': datetime.now().isoformat(),
            'git_commit': self.get_git_info()
        }
        
        metadata_file = self.build_dir / 'build_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Build metadata saved to {metadata_file}")
        return metadata_file
    
    def get_git_info(self):
        """Get current git information"""
        try:
            commit = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            branch = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            return {
                'commit': commit,
                'branch': branch
            }
        except:
            return {}
    
    def run_build(self):
        """Execute complete build pipeline"""
        print(f"\n🚀 Starting build for {self.app_name} v{self.version}\n")
        
        # Step 1: Run tests
        if not self.run_tests():
            return False
        
        # Step 2: Install dependencies (optional, usually done in Docker)
        # self.install_dependencies()
        
        # Step 3: Build Docker image
        image_tag = self.build_docker_image()
        if not image_tag:
            return False
        
        # Step 4: Push to registry
        full_image = self.push_to_registry(image_tag)
        if not full_image:
            return False
        
        # Step 5: Generate Kubernetes manifests
        self.generate_kubernetes_manifests(full_image)
        
        # Step 6: Create build metadata
        self.create_build_metadata(full_image)
        
        print(f"\n✅ Build completed successfully!")
        print(f"📦 Artifact: {full_image}")
        print(f"📁 Build directory: {self.build_dir}/")
        
        return True

# Main execution
if __name__ == "__main__":
    builder = BuildAutomation()
    success = builder.run_build()
    sys.exit(0 if success else 1)
