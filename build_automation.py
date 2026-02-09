#!/usr/bin/env python3
"""
Enhanced build_automation.py with CI/CD integration
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

class CIAwareBuildAutomation:
    def __init__(self):
        self.ci_env = self.detect_ci_environment()
        self.config = self.load_ci_config()
        self.app_name = self.config.get('app_name', 'myapp')
        self.version = self.get_version()
        self.build_dir = Path('build')
        
    def detect_ci_environment(self):
        """Detect which CI/CD platform is running"""
        if os.getenv('GITHUB_ACTIONS'):
            return 'github_actions'
        elif os.getenv('GITLAB_CI'):
            return 'gitlab_ci'
        elif os.getenv('JENKINS_HOME'):
            return 'jenkins'
        else:
            return 'local'
    
    def load_ci_config(self):
        """Load configuration from environment variables or config file"""
        config = {}
        
        # Common configurations
        config['app_name'] = os.getenv('APP_NAME', 'myapp')
        config['docker_registry'] = os.getenv('DOCKER_REGISTRY', 'localhost:5000')
        config['port'] = int(os.getenv('APP_PORT', '8000'))
        config['replicas'] = int(os.getenv('REPLICAS', '3'))
        
        # CI-specific configurations
        if self.ci_env == 'github_actions':
            config['image_tag'] = f"{config['docker_registry']}/{config['app_name']}:{os.getenv('GITHUB_SHA', 'latest')[:7]}"
            config['branch'] = os.getenv('GITHUB_REF_NAME', 'unknown')
        elif self.ci_env == 'gitlab_ci':
            config['image_tag'] = f"{config['docker_registry']}:{os.getenv('CI_COMMIT_SHORT_SHA', 'latest')}"
            config['branch'] = os.getenv('CI_COMMIT_BRANCH', 'unknown')
        elif self.ci_env == 'jenkins':
            git_commit = os.getenv('GIT_COMMIT_SHORT', 'latest')
            config['image_tag'] = f"{config['docker_registry']}/{config['app_name']}:{git_commit}"
            config['branch'] = os.getenv('GIT_BRANCH', 'unknown')
        
        return config
    
    def get_version(self):
        """Get version from CI environment or git"""
        if self.ci_env == 'github_actions':
            return os.getenv('GITHUB_SHA', 'unknown')[:7]
        elif self.ci_env == 'gitlab_ci':
            return os.getenv('CI_COMMIT_SHORT_SHA', 'unknown')
        elif self.ci_env == 'jenkins':
            return os.getenv('GIT_COMMIT_SHORT', 'unknown')
        else:
            try:
                result = subprocess.run(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            except:
                return datetime.now().strftime('%Y%m%d%H%M%S')
    
    def generate_kubernetes_manifests(self):
        """Generate Kubernetes deployment manifests with CI-aware image tags"""
        print(f"📝 Generating Kubernetes manifests for {self.ci_env}...")
        
        self.build_dir.mkdir(exist_ok=True)
        
        # Use IMAGE_PLACEHOLDER for CI/CD pipelines to replace later
        image_name = self.config.get('image_tag', 'IMAGE_PLACEHOLDER')
        
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': f"{self.app_name}-deployment",
                'labels': {
                    'app': self.app_name,
                    'version': self.version,
                    'managed-by': f'ci-{self.ci_env}'
                }
            },
            'spec': {
                'replicas': self.config.get('replicas', 3),
                'selector': {
                    'matchLabels': {'app': self.app_name}
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': self.app_name,
                            'version': self.version
                        },
                        'annotations': {
                            'prometheus.io/scrape': 'true',
                            'prometheus.io/port': str(self.config.get('port', 8000))
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': self.app_name,
                            'image': image_name,
                            'imagePullPolicy': 'Always',
                            'ports': [{
                                'name': 'http',
                                'containerPort': self.config.get('port', 8000),
                                'protocol': 'TCP'
                            }],
                            'env': [
                                {'name': 'ENVIRONMENT', 'value': 'production'},
                                {'name': 'VERSION', 'value': self.version}
                            ],
                            'resources': {
                                'requests': {
                                    'memory': '256Mi',
                                    'cpu': '250m'
                                },
                                'limits': {
                                    'memory': '512Mi',
                                    'cpu': '500m'
                                }
                            },
                            'livenessProbe': {
                                'httpGet': {
                                    'path': '/health',
                                    'port': 'http'
                                },
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': '/ready',
                                    'port': 'http'
                                },
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5
                            }
                        }]
                    }
                }
            }
        }
        
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f"{self.app_name}-service",
                'labels': {'app': self.app_name}
            },
            'spec': {
                'selector': {'app': self.app_name},
                'ports': [{
                    'name': 'http',
                    'protocol': 'TCP',
                    'port': 80,
                    'targetPort': 'http'
                }],
                'type': 'LoadBalancer'
            }
        }
        
        # Write manifests
        import yaml
        
        deployment_file = self.build_dir / 'deployment.yaml'
        service_file = self.build_dir / 'service.yaml'
        
        with open(deployment_file, 'w') as f:
            yaml.dump(deployment, f, default_flow_style=False)
        
        with open(service_file, 'w') as f:
            yaml.dump(service, f, default_flow_style=False)
        
        print(f"✅ Manifests generated in {self.build_dir}/")
        print(f"   - Deployment: {deployment_file}")
        print(f"   - Service: {service_file}")
        
        return [deployment_file, service_file]
    
    def create_build_info(self):
        """Create build information file"""
        build_info = {
            'app_name': self.app_name,
            'version': self.version,
            'ci_environment': self.ci_env,
            'build_time': datetime.now().isoformat(),
            'branch': self.config.get('branch', 'unknown'),
            'image_tag': self.config.get('image_tag', 'unknown')
        }
        
        info_file = self.build_dir / 'build-info.json'
        with open(info_file, 'w') as f:
            json.dump(build_info, f, indent=2)
        
        print(f"✅ Build info saved to {info_file}")
        return info_file
    
    def run(self):
        """Execute build process"""
        print(f"\n🚀 Starting CI/CD build on {self.ci_env}")
        print(f"📦 App: {self.app_name}")
        print(f"🏷️  Version: {self.version}")
        print(f"🌿 Branch: {self.config.get('branch', 'unknown')}\n")
        
        self.generate_kubernetes_manifests()
        self.create_build_info()
        
        print(f"\n✅ Build automation complete!")
        return True

if __name__ == "__main__":
    builder = CIAwareBuildAutomation()
    success = builder.run()
    sys.exit(0 if success else 1)
