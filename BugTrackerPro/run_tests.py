#!/usr/bin/env python3
"""
Test runner for the bug reporting system
Includes the login flow automation you provided
"""

import asyncio
import json
import sys
from test_automation import run_replay, test_login_flow, test_bug_submission_flow, test_admin_dashboard_flow, test_onboarding_tutorial

def main():
    """Main test runner"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        # Run the specific login test case you provided
        login_actions = [
            {"action": "click", "selector": "#login"},
            {"action": "type", "selector": "#email", "value": "test@example.com"},
            {"action": "type", "selector": "#password", "value": "password123"},
            {"action": "click", "selector": "#submit"}
        ]
        
        print("Running your specific login test case...")
        result = asyncio.run(run_replay(login_actions))
        
        if result['success']:
            print("✅ Login test completed successfully")
        else:
            print("❌ Login test failed")
            for error in result['errors']:
                print(f"   Error: {error}")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "all":
        # Run all test suites
        print("🚀 Running complete test suite...")
        
        tests = [
            ("Login Flow", test_login_flow),
            ("Bug Submission", test_bug_submission_flow), 
            ("Admin Dashboard", test_admin_dashboard_flow),
            ("Onboarding Tutorial", test_onboarding_tutorial)
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} test...")
            result = asyncio.run(test_func())
            results[test_name] = result
            
            if result['success']:
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
                for error in result['errors']:
                    print(f"   Error: {error}")
        
        # Summary
        passed = sum(1 for r in results.values() if r['success'])
        total = len(results)
        print(f"\n📊 Test Summary: {passed}/{total} tests passed")
        
    else:
        print("Bug Reporting System Test Runner")
        print("Usage:")
        print("  python run_tests.py login    # Run your specific login test")
        print("  python run_tests.py all      # Run all test suites")
        print("\nExample with custom actions:")
        print('  python test_automation.py \'[{"action": "click", "selector": "#login"}]\'')

if __name__ == "__main__":
    main()