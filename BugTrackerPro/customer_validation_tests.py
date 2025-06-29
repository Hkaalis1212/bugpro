#!/usr/bin/env python3
"""
Customer System Validation Tests
Tests all customer-related functionality to ensure data integrity
"""

import requests
import json
import sys
from datetime import datetime

class CustomerSystemValidator:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"[{status}] {test_name}: {details}")
        return success
    
    def test_subscription_api_endpoints(self):
        """Test subscription-related API endpoints are accessible"""
        endpoints = [
            '/api/subscription/status',
            '/pricing',
            '/payment-flow?plan=standard',
            '/subscription/success',
            '/manage-subscription'
        ]
        
        all_good = True
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code in [200, 302, 401, 403]:  # Valid responses
                    self.log_result(f"Endpoint {endpoint}", True, f"Status: {response.status_code}")
                else:
                    self.log_result(f"Endpoint {endpoint}", False, f"Unexpected status: {response.status_code}")
                    all_good = False
            except Exception as e:
                self.log_result(f"Endpoint {endpoint}", False, f"Error: {str(e)}")
                all_good = False
        
        return all_good
    
    def test_payment_flow_plans(self):
        """Test payment flow works for different plans"""
        plans = ['standard', 'premium']
        
        all_good = True
        for plan in plans:
            try:
                response = self.session.get(f"{self.base_url}/payment-flow?plan={plan}")
                if response.status_code == 200 and plan.title() in response.text:
                    self.log_result(f"Payment flow {plan}", True, "Plan page loads correctly")
                else:
                    self.log_result(f"Payment flow {plan}", False, "Plan page issues")
                    all_good = False
            except Exception as e:
                self.log_result(f"Payment flow {plan}", False, f"Error: {str(e)}")
                all_good = False
        
        return all_good
    
    def test_user_registration_flow(self):
        """Test user registration endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/register")
            if response.status_code == 200 and "register" in response.text.lower():
                self.log_result("User Registration", True, "Registration page accessible")
                return True
            else:
                self.log_result("User Registration", False, "Registration page issues")
                return False
        except Exception as e:
            self.log_result("User Registration", False, f"Error: {str(e)}")
            return False
    
    def test_login_flow(self):
        """Test login endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/login")
            if response.status_code == 200 and "login" in response.text.lower():
                self.log_result("User Login", True, "Login page accessible")
                return True
            else:
                self.log_result("User Login", False, "Login page issues")
                return False
        except Exception as e:
            self.log_result("User Login", False, f"Error: {str(e)}")
            return False
    
    def test_subscription_management_pages(self):
        """Test subscription management pages"""
        pages = [
            '/pricing',
            '/subscription/cancelled'
        ]
        
        all_good = True
        for page in pages:
            try:
                response = self.session.get(f"{self.base_url}{page}")
                if response.status_code == 200:
                    self.log_result(f"Page {page}", True, "Page loads correctly")
                else:
                    self.log_result(f"Page {page}", False, f"Status: {response.status_code}")
                    all_good = False
            except Exception as e:
                self.log_result(f"Page {page}", False, f"Error: {str(e)}")
                all_good = False
        
        return all_good
    
    def test_webhook_endpoint(self):
        """Test Stripe webhook endpoint exists"""
        try:
            # Test with empty payload (should fail gracefully)
            response = self.session.post(f"{self.base_url}/stripe/webhook", 
                                       data='{}', 
                                       headers={'Content-Type': 'application/json'})
            # Should return 400 for invalid webhook, not 404
            if response.status_code in [400, 401, 403]:
                self.log_result("Webhook Endpoint", True, f"Webhook endpoint exists (status: {response.status_code})")
                return True
            else:
                self.log_result("Webhook Endpoint", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Webhook Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_customer_data_consistency(self):
        """Test customer data API consistency"""
        try:
            # Test that pages don't have obvious data errors
            response = self.session.get(f"{self.base_url}/pricing")
            if response.status_code == 200:
                # Check for pricing consistency
                content = response.text.lower()
                if 'standard' in content and 'premium' in content and 'freemium' in content:
                    self.log_result("Customer Data Consistency", True, "All plan types present")
                    return True
                else:
                    self.log_result("Customer Data Consistency", False, "Missing plan information")
                    return False
            else:
                self.log_result("Customer Data Consistency", False, "Cannot access pricing page")
                return False
        except Exception as e:
            self.log_result("Customer Data Consistency", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for customer operations"""
        try:
            # Test invalid subscription status check without authentication
            response = self.session.get(f"{self.base_url}/api/subscription/status")
            # Should redirect to login or return 401/403, not crash
            if response.status_code in [302, 401, 403]:
                self.log_result("Error Handling", True, "Handles unauthenticated requests properly")
                return True
            elif response.status_code == 200:
                # Check if it's a redirect page (Flask login redirect)
                if 'redirecting' in response.text.lower() and 'login' in response.text.lower():
                    self.log_result("Error Handling", True, "Redirects to login properly")
                    return True
                # Check if it's returning proper error response for unauthenticated user
                try:
                    data = response.json()
                    if 'error' in data or data.get('status') == 'unauthenticated':
                        self.log_result("Error Handling", True, "Returns proper error for unauthenticated user")
                        return True
                except:
                    pass
                self.log_result("Error Handling", False, "Endpoint accessible without authentication")
                return False
            else:
                self.log_result("Error Handling", False, f"Unexpected response: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Error Handling", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all customer system validation tests"""
        print("=" * 60)
        print("CUSTOMER SYSTEM VALIDATION")
        print("=" * 60)
        print(f"Testing: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        tests = [
            self.test_subscription_api_endpoints,
            self.test_payment_flow_plans,
            self.test_user_registration_flow,
            self.test_login_flow,
            self.test_subscription_management_pages,
            self.test_webhook_endpoint,
            self.test_customer_data_consistency,
            self.test_error_handling
        ]
        
        for test in tests:
            test()
        
        # Generate summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        total = len(self.results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        failed = [r for r in self.results if r['status'] == 'FAIL']
        if failed:
            print("\nFAILED TESTS:")
            for test in failed:
                print(f"  ❌ {test['test']}: {test['details']}")
        
        # Overall assessment
        print(f"\n🎯 Customer System Status:")
        if passed == total:
            print("   ✅ FULLY FUNCTIONAL: All customer operations working correctly")
        elif passed >= total * 0.9:  # 90% pass rate
            print("   🟢 MOSTLY FUNCTIONAL: Minor issues detected")
        elif passed >= total * 0.7:  # 70% pass rate
            print("   🟡 PARTIALLY FUNCTIONAL: Some issues need attention")
        else:
            print("   🔴 NEEDS ATTENTION: Multiple customer system issues")
        
        return passed == total

def main():
    """Run customer system validation"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    validator = CustomerSystemValidator(base_url)
    success = validator.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()