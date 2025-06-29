"""
Integration Test Suite
Tests the complete application flow including Stripe integration
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_tests import run_all_tests
from test_automation import test_login_flow, test_bug_submission_flow, test_admin_dashboard_flow

class IntegrationTestRunner:
    """Comprehensive integration test runner"""
    
    def __init__(self):
        self.unit_test_results = None
        self.browser_test_results = {}
        
    def run_unit_tests(self):
        """Run unit test suite"""
        print("🔧 Running Unit Tests...")
        self.unit_test_results = run_all_tests()
        return self.unit_test_results
    
    async def run_browser_tests(self):
        """Run browser automation tests"""
        print("🌐 Running Browser Automation Tests...")
        
        tests = [
            ("Login Flow", test_login_flow),
            ("Bug Submission", test_bug_submission_flow), 
            ("Admin Dashboard", test_admin_dashboard_flow)
        ]
        
        for test_name, test_func in tests:
            print(f"📋 Running {test_name} test...")
            try:
                result = await test_func()
                self.browser_test_results[test_name] = result
                
                if result.get('success', False):
                    print(f"✅ {test_name} test PASSED")
                else:
                    print(f"❌ {test_name} test FAILED")
                    if 'errors' in result:
                        for error in result['errors']:
                            print(f"   Error: {error}")
            except Exception as e:
                print(f"❌ {test_name} test ERROR: {e}")
                self.browser_test_results[test_name] = {'success': False, 'error': str(e)}
        
        return self.browser_test_results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        # Unit test results
        print(f"Unit Tests: {'PASSED' if self.unit_test_results else 'FAILED'}")
        
        # Browser test results
        browser_passed = sum(1 for r in self.browser_test_results.values() 
                           if r.get('success', False))
        browser_total = len(self.browser_test_results)
        print(f"Browser Tests: {browser_passed}/{browser_total} passed")
        
        # Overall status
        overall_success = (self.unit_test_results and 
                         browser_passed == browser_total)
        
        print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        if not overall_success:
            print("\nRecommendations:")
            if not self.unit_test_results:
                print("- Fix unit test failures before deployment")
            if browser_passed < browser_total:
                print("- Review browser automation test failures")
                print("- Check UI elements and selectors")
        
        return overall_success

async def run_integration_tests():
    """Run complete integration test suite"""
    runner = IntegrationTestRunner()
    
    # Run unit tests
    unit_success = runner.run_unit_tests()
    
    # Run browser tests
    await runner.run_browser_tests()
    
    # Generate report
    overall_success = runner.generate_report()
    
    return overall_success

if __name__ == '__main__':
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)