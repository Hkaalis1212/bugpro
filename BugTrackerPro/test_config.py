"""
Test Configuration and Utilities
"""

import os
import tempfile
import pytest
from app import app, db
from models import User, BugReport, Team, Project
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    """Create test client"""
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE']
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

@pytest.fixture
def auth_user(client):
    """Create and return authenticated test user"""
    user = User(
        email='test@example.com',
        password_hash=generate_password_hash('testpass123'),
        first_name='Test',
        last_name='User',
        role='user'
    )
    db.session.add(user)
    db.session.commit()
    
    # Login
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    return user

@pytest.fixture
def admin_user(client):
    """Create and return admin user"""
    admin = User(
        email='admin@example.com',
        password_hash=generate_password_hash('adminpass123'),
        first_name='Admin',
        last_name='User',
        role='admin',
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    return admin

class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_bug_report(user_id, title="Test Bug", description="Test description"):
        """Create a test bug report"""
        bug = BugReport(
            title=title,
            description=description,
            user_id=user_id
        )
        db.session.add(bug)
        db.session.commit()
        return bug
    
    @staticmethod
    def create_project(user_id, name="Test Project"):
        """Create a test project"""
        project = Project(
            name=name,
            description="Test project description",
            created_by=user_id
        )
        db.session.add(project)
        db.session.commit()
        return project
    
    @staticmethod
    def create_team(user_id, project_id, name="Test Team"):
        """Create a test team"""
        team = Team(
            name=name,
            description="Test team description",
            created_by=user_id,
            project_id=project_id
        )
        db.session.add(team)
        db.session.commit()
        return team