#!/usr/bin/env python3
"""
Deployment Readiness Test
Tests the application for deployment readiness
"""

import subprocess
import requests
import time
import sys
from datetime import datetime

class DeploymentTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = []
        
    def test_result(self, test_name, success, message=""):
        """Record test result"""
        status = "PASS" if success else "FAIL"
        self.results.append({
            'test': test_name,
            'status': status,
            'message': message
        })
        print(f"[{status}] {test_name}: {message}")
        return success
    
    def test_server_responsiveness(self):
        """Test server responds quickly"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200 and response_time < 5.0:
                return self.test_result("Server Responsiveness", True, 
                                      f"Response time: {response_time:.2f}s")
            else:
                return self.test_result("Server Responsiveness", False,
                                      f"Slow response: {response_time:.2f}s")
        except Exception as e:
            return self.test_result("Server Responsiveness", False, str(e))
    
    def test_all_critical_pages(self):
        """Test all critical pages load"""
        critical_pages = [
            "/",
            "/pricing", 
            "/payment-flow?plan=standard",
            "/login",
            "/register"
        ]
        
        all_passed = True
        for page in critical_pages:
            try:
                response = requests.get(f"{self.base_url}{page}", timeout=10)
                if response.status_code == 200:
                    self.test_result(f"Page {page}", True, "Loads correctly")
                else:
                    self.test_result(f"Page {page}", False, f"Status: {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.test_result(f"Page {page}", False, str(e))
                all_passed = False
        
        return all_passed
    
    def test_payment_flow_functionality(self):
        """Test payment flow page works"""
        try:
            # Test standard plan
            response1 = requests.get(f"{self.base_url}/payment-flow?plan=standard")
            standard_ok = response1.status_code == 200 and "Standard" in response1.text
            
            # Test premium plan  
            response2 = requests.get(f"{self.base_url}/payment-flow?plan=premium")
            premium_ok = response2.status_code == 200 and "Premium" in response2.text
            
            if standard_ok and premium_ok:
                return self.test_result("Payment Flow", True, "Both plan types work")
            else:
                return self.test_result("Payment Flow", False, "Plan pages have issues")
                
        except Exception as e:
            return self.test_result("Payment Flow", False, str(e))
    
    def test_error_handling(self):
        """Test error page handling"""
        try:
            response = requests.get(f"{self.base_url}/nonexistent-page")
            if response.status_code == 404:
                return self.test_result("Error Handling", True, "404 pages handled correctly")
            else:
                return self.test_result("Error Handling", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            return self.test_result("Error Handling", False, str(e))
    
    def test_static_assets(self):
        """Test static assets are accessible"""
        try:
            response = requests.get(f"{self.base_url}/static/js/payment-flow.js")
            if response.status_code == 200:
                return self.test_result("Static Assets", True, "JavaScript files accessible")
            else:
                return self.test_result("Static Assets", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.test_result("Static Assets", False, str(e))
    
    def test_security_basics(self):
        """Test basic security measures"""
        try:
            # Test that admin pages require authentication
            response = requests.get(f"{self.base_url}/admin")
            if response.status_code in [302, 401, 403]:  # Redirect or auth required
                return self.test_result("Security", True, "Admin pages protected")
            elif response.status_code == 200:
                # Check if it's a redirect page (Flask login redirect)
                if 'redirecting' in response.text.lower() and 'login' in response.text.lower():
                    return self.test_result("Security", True, "Admin pages redirect to login")
                else:
                    return self.test_result("Security", False, "Admin pages accessible without authentication")
            else:
                return self.test_result("Security", False, f"Unexpected response: {response.status_code}")
        except Exception as e:
            return self.test_result("Security", False, str(e))
    
    def run_deployment_tests(self):
        """Run all deployment readiness tests"""
        print("=" * 60)
        print("DEPLOYMENT READINESS TEST")
        print("=" * 60)
        print(f"Testing: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        tests = [
            self.test_server_responsiveness,
            self.test_all_critical_pages,
            self.test_payment_flow_functionality,
            self.test_error_handling,
            self.test_static_assets,
            self.test_security_basics
        ]
        
        for test in tests:
            test()
        
        # Generate report
        print("\n" + "=" * 60)
        print("DEPLOYMENT READINESS REPORT")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        total = len(self.results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        failed = [r for r in self.results if r['status'] == 'FAIL']
        if failed:
            print("\nFAILED TESTS:")
            for test in failed:
                print(f"  ❌ {test['test']}: {test['message']}")
        
        # Deployment recommendation
        print("\n" + "="*60)
        if passed == total:
            print("✅ DEPLOYMENT APPROVED")
            print("All tests passed. Application is ready for deployment.")
        elif passed >= total * 0.8:  # 80% pass rate
            print("⚠️  DEPLOYMENT WITH CAUTION")
            print("Most tests passed, but some issues detected.")
            print("Review failed tests before deploying.")
        else:
            print("❌ DEPLOYMENT NOT RECOMMENDED")
            print("Multiple critical issues detected.")
            print("Fix failing tests before deployment.")
        
        return passed == total

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    tester = DeploymentTest(base_url)
    success = tester.run_deployment_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()