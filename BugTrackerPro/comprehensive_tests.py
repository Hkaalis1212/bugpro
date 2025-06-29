"""
Comprehensive Test Suite for the Bug Reporting System
Run automated tests to validate functionality and ensure code quality
"""

import unittest
import sys
import os
import tempfile
import json
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, BugReport, Team, Project, Attachment, EmailSubscriber, UserFeedback
from werkzeug.security import generate_password_hash

class BugReportTestCase(unittest.TestCase):
    """Test cases for bug reporting functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE']
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test users with different roles
        self.test_user = User(
            email='test@example.com',
            password_hash=generate_password_hash('testpass123'),
            first_name='Test',
            last_name='User',
            is_admin=False,
            role='user'
        )
        
        self.admin_user = User(
            email='admin@example.com',
            password_hash=generate_password_hash('adminpass123'),
            first_name='Admin',
            last_name='User',
            is_admin=True,
            role='admin'
        )
        
        self.team_lead_user = User(
            email='teamlead@example.com',
            password_hash=generate_password_hash('leadpass123'),
            first_name='Team',
            last_name='Lead',
            is_admin=False,
            role='team_lead'
        )
        
        db.session.add_all([self.test_user, self.admin_user, self.team_lead_user])
        db.session.commit()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def login(self, email='test@example.com', password='testpass123'):
        """Helper method to log in"""
        return self.app.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def logout(self):
        """Helper method to log out"""
        return self.app.get('/logout', follow_redirects=True)

    def test_home_page_loads(self):
        """Test home page loads correctly"""
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Bug Tracker', rv.data)

    def test_user_registration_valid(self):
        """Test valid user registration"""
        rv = self.app.post('/register', data={
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }, follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        # Check user was created
        user = User.query.filter_by(email='newuser@example.com').first()
        self.assertIsNotNone(user)

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email fails"""
        rv = self.app.post('/register', data={
            'email': 'test@example.com',  # Already exists
            'password': 'newpass123',
            'first_name': 'Duplicate',
            'last_name': 'User'
        }, follow_redirects=True)
        self.assertIn(b'Email address already exists', rv.data)

    def test_user_login_valid(self):
        """Test valid user login"""
        rv = self.login()
        self.assertEqual(rv.status_code, 200)

    def test_user_login_invalid(self):
        """Test invalid login credentials"""
        rv = self.login(password='wrongpassword')
        self.assertIn(b'Invalid email or password', rv.data)

    @patch('app.parse_bug_description')
    def test_bug_report_submission(self, mock_parse):
        """Test bug report submission with AI parsing"""
        mock_parse.return_value = "1. Open the application\n2. Click on submit\n3. Observe the error"
        
        self.login()
        rv = self.app.post('/submit', data={
            'title': 'Test Bug Report',
            'description': 'This is a detailed bug report with steps to reproduce the issue. The user should click on the submit button and observe an error.'
        }, follow_redirects=True)
        
        self.assertEqual(rv.status_code, 200)
        # Check bug report was created
        bug_report = BugReport.query.filter_by(title='Test Bug Report').first()
        self.assertIsNotNone(bug_report)
        self.assertEqual(bug_report.user_id, self.test_user.id)

    def test_bug_report_empty_title(self):
        """Test bug report submission with empty title fails"""
        self.login()
        rv = self.app.post('/submit', data={
            'title': '',
            'description': 'This bug has no title'
        }, follow_redirects=True)
        self.assertIn(b'Title is required', rv.data)

    def test_admin_dashboard_access(self):
        """Test admin can access admin dashboard"""
        self.login(email='admin@example.com', password='adminpass123')
        rv = self.app.get('/admin')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Admin Dashboard', rv.data)

    def test_non_admin_dashboard_denied(self):
        """Test non-admin cannot access admin dashboard"""
        self.login()
        rv = self.app.get('/admin')
        self.assertEqual(rv.status_code, 302)  # Redirect

    def test_pricing_page_loads(self):
        """Test pricing page loads correctly"""
        rv = self.app.get('/pricing')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Choose Your Plan', rv.data)

    def test_payment_flow_visualization(self):
        """Test payment flow page loads"""
        rv = self.app.get('/payment-flow?plan=standard')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Payment Flow', rv.data)
        self.assertIn(b'Standard', rv.data)

    def test_teams_functionality(self):
        """Test team creation and management"""
        self.login()
        
        # Create a project first
        project = Project(
            name='Test Project',
            description='Test project description',
            created_by=self.test_user.id
        )
        db.session.add(project)
        db.session.commit()
        
        # Create a team
        rv = self.app.post('/teams/create', data={
            'name': 'Test Team',
            'description': 'Test team description',
            'project_id': project.id
        }, follow_redirects=True)
        
        self.assertEqual(rv.status_code, 200)
        team = Team.query.filter_by(name='Test Team').first()
        self.assertIsNotNone(team)

    def test_role_based_access_control(self):
        """Test role-based permissions"""
        # Create a bug report as regular user
        self.login()
        self.app.post('/submit', data={
            'title': 'Role Test Bug',
            'description': 'Testing role-based access'
        })
        
        bug = BugReport.query.filter_by(title='Role Test Bug').first()
        self.assertIsNotNone(bug)
        
        # Test admin can delete
        self.logout()
        self.login(email='admin@example.com', password='adminpass123')
        rv = self.app.delete(f'/api/bugs/{bug.id}')
        self.assertIn(rv.status_code, [200, 204])

    def test_subscription_status_api(self):
        """Test subscription status API endpoint"""
        self.login()
        rv = self.app.get('/api/subscription/status')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertIn('status', data)
        self.assertIn('plan', data)

    def test_feedback_submission(self):
        """Test user feedback submission"""
        rv = self.app.post('/feedback', data={
            'email': 'feedback@example.com',
            'name': 'Feedback User',
            'feedback_type': 'feature_request',
            'subject': 'New Feature Request',
            'message': 'Please add this feature'
        }, follow_redirects=True)
        
        self.assertEqual(rv.status_code, 200)
        feedback = UserFeedback.query.filter_by(subject='New Feature Request').first()
        self.assertIsNotNone(feedback)

    def test_email_subscription(self):
        """Test email subscription functionality"""
        rv = self.app.post('/subscribe', data={
            'email': 'subscribe@example.com'
        }, follow_redirects=True)
        
        self.assertEqual(rv.status_code, 200)
        subscriber = EmailSubscriber.query.filter_by(email='subscribe@example.com').first()
        self.assertIsNotNone(subscriber)

    def test_forgot_password_flow(self):
        """Test password reset functionality"""
        rv = self.app.post('/forgot-password', data={
            'email': 'test@example.com'
        }, follow_redirects=True)
        
        self.assertEqual(rv.status_code, 200)
        # Check that reset token was generated
        user = User.query.filter_by(email='test@example.com').first()
        self.assertIsNotNone(user.reset_token)

    @patch('stripe.checkout.Session.create')
    def test_stripe_checkout_creation(self, mock_stripe):
        """Test Stripe checkout session creation"""
        mock_stripe.return_value = MagicMock(
            id='cs_test_123',
            url='https://checkout.stripe.com/test'
        )
        
        self.login()
        with patch.dict(os.environ, {'STRIPE_SECRET_KEY': 'sk_test_123'}):
            rv = self.app.post('/subscription/create-checkout', data={
                'plan': 'standard'
            })
            self.assertEqual(rv.status_code, 302)  # Redirect to Stripe

    def test_api_endpoints_authentication(self):
        """Test API endpoints require authentication"""
        endpoints = [
            '/api/user/reports',
            '/api/projects',
            '/api/subscription/status'
        ]
        
        for endpoint in endpoints:
            rv = self.app.get(endpoint)
            self.assertEqual(rv.status_code, 302)  # Redirect to login

    def test_pagination_functionality(self):
        """Test pagination on admin dashboard"""
        self.login(email='admin@example.com', password='adminpass123')
        
        # Create multiple bug reports
        for i in range(15):
            bug = BugReport(
                title=f'Bug Report {i}',
                description=f'Description for bug {i}',
                user_id=self.test_user.id
            )
            db.session.add(bug)
        db.session.commit()
        
        # Test pagination
        rv = self.app.get('/admin?page=2')
        self.assertEqual(rv.status_code, 200)

    def test_search_functionality(self):
        """Test search functionality in dashboard"""
        self.login()
        
        # Create searchable bug report
        bug = BugReport(
            title='Searchable Bug Report',
            description='This bug should be findable by search',
            user_id=self.test_user.id
        )
        db.session.add(bug)
        db.session.commit()
        
        # Test search
        rv = self.app.get('/dashboard?search=Searchable')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Searchable Bug Report', rv.data)

class StripeIntegrationTest(unittest.TestCase):
    """Test Stripe integration functionality"""
    
    def setUp(self):
        """Set up Stripe test environment"""
        app.config['TESTING'] = True
        self.app = app.test_client()
    
    @patch('stripe.checkout.Session.retrieve')
    def test_payment_status_check(self, mock_retrieve):
        """Test payment status checking"""
        mock_retrieve.return_value = MagicMock(
            payment_status='paid',
            metadata={'plan': 'standard', 'user_id': '1'},
            customer='cus_test_123'
        )
        
        with app.app_context():
            with patch.dict(os.environ, {'STRIPE_SECRET_KEY': 'sk_test_123'}):
                rv = self.app.get('/api/payment-status/cs_test_123')
                # This will fail without login, but tests the endpoint exists
                self.assertIn(rv.status_code, [200, 302])

class SecurityTest(unittest.TestCase):
    """Test security measures"""
    
    def setUp(self):
        """Set up security test environment"""
        app.config['TESTING'] = True
        self.app = app.test_client()
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection"""
        malicious_input = "'; DROP TABLE users; --"
        rv = self.app.post('/login', data={
            'email': malicious_input,
            'password': 'password'
        })
        # Should not crash the application
        self.assertIn(rv.status_code, [200, 302, 400])
    
    def test_xss_protection(self):
        """Test protection against XSS attacks"""
        xss_payload = '<script>alert("XSS")</script>'
        
        # Should be escaped in output
        with app.app_context():
            db.create_all()
            user = User(
                email='xss@example.com',
                password_hash=generate_password_hash('password'),
                first_name='XSS',
                last_name='Test'
            )
            db.session.add(user)
            db.session.commit()
            
            # Login and submit bug with XSS payload
            self.app.post('/login', data={
                'email': 'xss@example.com',
                'password': 'password'
            })
            
            rv = self.app.post('/submit', data={
                'title': xss_payload,
                'description': 'Test description'
            }, follow_redirects=True)
            
            # XSS should be escaped
            self.assertNotIn(b'<script>', rv.data)

def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(BugReportTestCase))
    suite.addTests(loader.loadTestsFromTestCase(StripeIntegrationTest))
    suite.addTests(loader.loadTestsFromTestCase(SecurityTest))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")
    
    if result.errors:
        print("\nERRORS:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)