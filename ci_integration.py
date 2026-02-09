#!/usr/bin/env python3
"""
ci_integration.py - Integrate build automation with CI/CD platforms
"""

import os
import sys
from build_automation import BuildAutomation

def get_ci_environment():
    """Detect CI/CD environment"""
    if os.getenv('JENKINS_HOME'):
        return 'jenkins'
    elif os.getenv('GITLAB_CI'):
        return 'gitlab'
    elif os.getenv('GITHUB_ACTIONS'):
        return 'github'
    else:
        return 'local'

def setup_ci_config():
    """Setup configuration based on CI environment"""
    ci_env = get_ci_environment()
    
    config = {
        'app_name': os.getenv('APP_NAME', 'myapp'),
        'docker_registry': os.getenv('DOCKER_REGISTRY', 'localhost:5000'),
        'port': int(os.getenv('APP_PORT', '8000')),
        'replicas': int(os.getenv('REPLICAS', '3'))
    }
    
    print(f"🔧 Running in {ci_env} environment")
    return config

def main():
    """Main CI/CD execution"""
    # Get branch info
    branch = os.getenv('GIT_BRANCH', os.getenv('CI_COMMIT_BRANCH', 'unknown'))
    print(f"🌿 Building branch: {branch}")
    
    # Only build and push on main/master branch
    if branch in ['main', 'master']:
        builder = BuildAutomation()
        success = builder.run_build()
        
        if success:
            print("✅ CI/CD build successful")
            sys.exit(0)
        else:
            print("❌ CI/CD build failed")
            sys.exit(1)
    else:
        print(f"ℹ️  Skipping build for branch: {branch}")
        sys.exit(0)

if __name__ == "__main__":
    main()
