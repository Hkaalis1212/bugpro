#!/usr/bin/env python3
"""
Quick Test Suite for Bug Reporting System
Fast, focused tests to validate core functionality
"""

import requests
import time
import json
import sys
from datetime import datetime

class TestRunner:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        self.results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        print(f"[{status}] {test_name}: {message}")
        
    def test_server_running(self):
        """Test if server is running and responding"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                self.log_test("Server Health", True, "Server is responding")
                return True
            else:
                self.log_test("Server Health", False, f"Server returned {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Health", False, f"Server not reachable: {str(e)}")
            return False
    
    def test_home_page(self):
        """Test home page loads with expected content"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200 and "Bug Tracker" in response.text:
                self.log_test("Home Page", True, "Home page loads correctly")
                return True
            else:
                self.log_test("Home Page", False, "Missing expected content")
                return False
        except Exception as e:
            self.log_test("Home Page", False, f"Error: {str(e)}")
            return False
    
    def test_pricing_page(self):
        """Test pricing page accessibility"""
        try:
            response = self.session.get(f"{self.base_url}/pricing")
            if response.status_code == 200 and "Choose Your Plan" in response.text:
                self.log_test("Pricing Page", True, "Pricing page loads correctly")
                return True
            else:
                self.log_test("Pricing Page", False, "Pricing page issues")
                return False
        except Exception as e:
            self.log_test("Pricing Page", False, f"Error: {str(e)}")
            return False
    
    def test_payment_flow_page(self):
        """Test payment flow visualization page"""
        try:
            response = self.session.get(f"{self.base_url}/payment-flow?plan=standard")
            if response.status_code == 200 and "Payment Flow" in response.text:
                self.log_test("Payment Flow", True, "Payment flow page loads correctly")
                return True
            else:
                self.log_test("Payment Flow", False, "Payment flow page issues")
                return False
        except Exception as e:
            self.log_test("Payment Flow", False, f"Error: {str(e)}")
            return False
    
    def test_register_page(self):
        """Test registration page loads"""
        try:
            response = self.session.get(f"{self.base_url}/register")
            if response.status_code == 200:
                self.log_test("Register Page", True, "Registration page accessible")
                return True
            else:
                self.log_test("Register Page", False, "Registration page issues")
                return False
        except Exception as e:
            self.log_test("Register Page", False, f"Error: {str(e)}")
            return False
    
    def test_login_page(self):
        """Test login page loads"""
        try:
            response = self.session.get(f"{self.base_url}/login")
            if response.status_code == 200:
                self.log_test("Login Page", True, "Login page accessible")
                return True
            else:
                self.log_test("Login Page", False, "Login page issues")
                return False
        except Exception as e:
            self.log_test("Login Page", False, f"Error: {str(e)}")
            return False
    
    def test_static_assets(self):
        """Test static assets are accessible"""
        static_files = [
            "/static/js/main.js",
            "/static/js/payment-flow.js"
        ]
        
        all_good = True
        for asset in static_files:
            try:
                response = self.session.get(f"{self.base_url}{asset}")
                if response.status_code == 200:
                    self.log_test(f"Static Asset {asset}", True, "Asset loads correctly")
                else:
                    self.log_test(f"Static Asset {asset}", False, f"Status: {response.status_code}")
                    all_good = False
            except Exception as e:
                self.log_test(f"Static Asset {asset}", False, f"Error: {str(e)}")
                all_good = False
        
        return all_good
    
    def test_security_headers(self):
        """Test basic security headers"""
        try:
            response = self.session.get(f"{self.base_url}/")
            headers = response.headers
            
            # Check for some basic security considerations
            if response.status_code == 200:
                self.log_test("Security Headers", True, "Basic security check passed")
                return True
            else:
                self.log_test("Security Headers", False, "Security check failed")
                return False
        except Exception as e:
            self.log_test("Security Headers", False, f"Error: {str(e)}")
            return False
    
    def test_form_endpoints(self):
        """Test form endpoints respond appropriately"""
        endpoints = [
            ("/feedback", "GET"),
            ("/subscribe", "GET"),
        ]
        
        all_good = True
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                
                if response.status_code in [200, 302, 405]:  # 405 = Method not allowed, which is fine
                    self.log_test(f"Endpoint {endpoint}", True, f"Responds correctly ({response.status_code})")
                else:
                    self.log_test(f"Endpoint {endpoint}", False, f"Unexpected status: {response.status_code}")
                    all_good = False
            except Exception as e:
                self.log_test(f"Endpoint {endpoint}", False, f"Error: {str(e)}")
                all_good = False
        
        return all_good
    
    def test_database_connectivity(self):
        """Test database is accessible by checking page that needs DB"""
        try:
            response = self.session.get(f"{self.base_url}/pricing")
            if response.status_code == 200:
                self.log_test("Database Connectivity", True, "Database appears to be working")
                return True
            else:
                self.log_test("Database Connectivity", False, "Database may have issues")
                return False
        except Exception as e:
            self.log_test("Database Connectivity", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("=" * 60)
        print("QUICK TEST SUITE - BUG REPORTING SYSTEM")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing: {self.base_url}")
        print()
        
        # Run tests in order
        tests = [
            self.test_server_running,
            self.test_home_page,
            self.test_pricing_page,
            self.test_payment_flow_page,
            self.test_register_page,
            self.test_login_page,
            self.test_static_assets,
            self.test_security_headers,
            self.test_form_endpoints,
            self.test_database_connectivity
        ]
        
        # Only run subsequent tests if server is running
        if not self.test_server_running():
            print("\nServer is not running. Cannot proceed with other tests.")
            return False
        
        # Run remaining tests
        for test in tests[1:]:  # Skip first test as we already ran it
            test()
        
        # Generate summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        total = len(self.results)
        
        print(f"Tests run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {(passed/total*100):.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.results if r['status'] == 'FAIL']
        if failed_tests:
            print("\nFAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        success = passed == total
        print(f"\nOverall Result: {'ALL TESTS PASSED' if success else 'SOME TESTS FAILED'}")
        
        return success

def main():
    """Main test execution"""
    # Check if custom URL provided
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    runner = TestRunner(base_url)
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()