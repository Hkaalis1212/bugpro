#!/usr/bin/env python3
"""
Master Test Runner
Combines unit tests, integration tests, and browser automation
"""

import sys
import subprocess
import os
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*50}")
    print(f"🔧 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 COMPREHENSIVE TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests_to_run = [
        ("python comprehensive_tests.py", "Unit & Integration Tests"),
        ("python run_tests.py all", "Browser Automation Tests (if available)"),
    ]
    
    results = {}
    
    for command, description in tests_to_run:
        success = run_command(command, description)
        results[description] = success
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Ready for deployment.")
        return 0
    else:
        print("💥 SOME TESTS FAILED! Please fix before deployment.")
        return 1

if __name__ == '__main__':
    sys.exit(main())