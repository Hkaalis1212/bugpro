#!/usr/bin/env python3
"""
Quick setup script for Bug Reporting System
Helps diagnose and fix common GitHub repository issues
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ required. Current version:", sys.version)
        return False
    print("✅ Python version:", sys.version.split()[0])
    return True

def check_files():
    """Check if essential files exist"""
    required_files = ['app.py', 'main.py', 'models.py']
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_requirements():
    """Check requirements file"""
    req_files = ['requirements_for_github.txt', 'requirements.txt']
    found = False
    
    for req_file in req_files:
        if os.path.exists(req_file):
            print(f"✅ {req_file} found")
            found = True
            break
    
    if not found:
        print("❌ No requirements file found")
    
    return found

def check_env_file():
    """Check environment configuration"""
    if os.path.exists('.env'):
        print("✅ .env file found")
        return True
    elif os.path.exists('.env.example'):
        print("⚠️  .env.example found but no .env file")
        print("   Copy .env.example to .env and configure your values")
        return False
    else:
        print("❌ No environment file found")
        return False

def install_dependencies():
    """Install Python dependencies"""
    req_file = 'requirements_for_github.txt' if os.path.exists('requirements_for_github.txt') else 'requirements.txt'
    
    if not os.path.exists(req_file):
        print("❌ No requirements file to install from")
        return False
    
    try:
        print(f"Installing dependencies from {req_file}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', req_file])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def test_imports():
    """Test if main modules can be imported"""
    try:
        import flask
        print("✅ Flask import successful")
        
        # Test app import
        from app import app
        print("✅ App import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        from app import app, db
        with app.app_context():
            # Try to create tables
            db.create_all()
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure DATABASE_URL is set correctly in .env")
        return False

def create_env_template():
    """Create .env file from template if it doesn't exist"""
    if not os.path.exists('.env') and os.path.exists('.env.example'):
        try:
            shutil.copy('.env.example', '.env')
            print("✅ Created .env from template")
            print("   Please edit .env with your actual values")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env: {e}")
            return False
    return True

def main():
    """Run complete setup check"""
    print("🔧 Bug Reporting System Setup Check")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_files),
        ("Requirements File", check_requirements),
        ("Environment File", check_env_file),
    ]
    
    # Run basic checks
    all_passed = True
    for name, check_func in checks:
        print(f"\n{name}:")
        if not check_func():
            all_passed = False
    
    # If basic checks pass, continue with setup
    if all_passed:
        print("\n" + "=" * 40)
        print("🚀 Running Setup Steps")
        
        # Create .env if needed
        create_env_template()
        
        # Install dependencies
        if install_dependencies():
            # Test imports
            if test_imports():
                # Test database
                test_database_connection()
        
        print("\n" + "=" * 40)
        print("🎉 Setup complete!")
        print("\nTo run the application:")
        print("  python main.py")
        print("\nTo access the app:")
        print("  http://localhost:5000")
        
    else:
        print("\n❌ Setup issues found. Please fix the above problems and run again.")
        print("\nCommon solutions:")
        print("1. Make sure you're in the correct directory")
        print("2. Ensure all files were cloned properly")
        print("3. Check Python version (3.11+ required)")

if __name__ == "__main__":
    main()