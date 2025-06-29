from app import db
from datetime import datetime, timedelta
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')  # user, team_lead, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_plan = db.Column(db.String(20), default='freemium')
    subscription_status = db.Column(db.String(20), default='active')
    subscription_end_date = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(100))
    reports_this_month = db.Column(db.Integer, default=0)
    github_username = db.Column(db.String(100))
    github_token = db.Column(db.String(255))
    github_connected_at = db.Column(db.DateTime)
    
    # Password reset fields
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expires = db.Column(db.DateTime)
    
    # Relationship with bug reports
    bug_reports = db.relationship('BugReport', foreign_keys='BugReport.user_id', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_admin': self.is_admin,
            'role': self.role,
            'subscription_plan': self.subscription_plan,
            'subscription_status': self.subscription_status,
            'subscription_end_date': self.subscription_end_date.isoformat() if self.subscription_end_date else None,
            'reports_this_month': self.reports_this_month,
            'plan_limits': self.get_plan_limits(),
            'can_submit_report': self.can_submit_report(),
            'github_username': self.github_username,
            'github_connected_at': self.github_connected_at.isoformat() if self.github_connected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'full_name': f"{self.first_name} {self.last_name}".strip()
        }
    
    def get_plan_limits(self):
        """Get the limits for the user's current subscription plan"""
        plans = {
            'freemium': {
                'reports_per_month': 5,
                'max_file_size': 5 * 1024 * 1024,  # 5MB
                'ai_analysis': False,
                'priority_support': False,
                'file_attachments': 1
            },
            'standard': {
                'reports_per_month': 50,
                'max_file_size': 25 * 1024 * 1024,  # 25MB
                'ai_analysis': True,
                'priority_support': False,
                'file_attachments': 5
            },
            'premium': {
                'reports_per_month': -1,  # unlimited
                'max_file_size': 100 * 1024 * 1024,  # 100MB
                'ai_analysis': True,
                'priority_support': True,
                'file_attachments': 10
            }
        }
        return plans.get(self.subscription_plan, plans['freemium'])
    
    def can_submit_report(self):
        """Check if user can submit a new report based on their plan"""
        # Check subscription status first
        if self.subscription_status not in ['active', 'trialing']:
            return False
            
        limits = self.get_plan_limits()
        if limits['reports_per_month'] == -1:  # unlimited
            return True
        
        # Ensure reports_this_month is not None
        current_reports = self.reports_this_month or 0
        return current_reports < limits['reports_per_month']
    
    def increment_report_count(self):
        """Increment the user's monthly report count"""
        if self.can_submit_report():
            # Ensure reports_this_month is not None
            if self.reports_this_month is None:
                self.reports_this_month = 0
            self.reports_this_month += 1
            db.session.commit()
            return True
        return False
    
    def generate_reset_token(self):
        """Generate a secure password reset token"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        db.session.commit()
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        if self.reset_token != token:
            return False
        if self.reset_token_expires < datetime.utcnow():
            return False
        return True
    
    def reset_password(self, new_password):
        """Reset password and clear reset token"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(new_password)
        self.reset_token = None
        self.reset_token_expires = None
        db.session.commit()
    
    def can_view_bug(self, bug):
        """Check if user can view a specific bug report"""
        if self.is_admin or self.role == 'admin':
            return True
        if bug.user_id == self.id:
            return True
        if self.role == 'team_lead' and bug.team_id:
            # Check if user is team lead of the bug's team
            from models import TeamMember
            team_membership = TeamMember.query.filter_by(
                user_id=self.id, 
                team_id=bug.team_id, 
                role='lead'
            ).first()
            return team_membership is not None
        return False
    
    def can_assign_bugs(self):
        """Check if user can assign bugs to others"""
        return self.is_admin or self.role in ['admin', 'team_lead']
    
    def can_delete_bug(self, bug):
        """Check if user can delete a specific bug report"""
        if self.is_admin or self.role == 'admin':
            return True
        if bug.user_id == self.id:
            return True
        return False
    
    def can_edit_bug(self, bug):
        """Check if user can edit a specific bug report"""
        if self.is_admin or self.role == 'admin':
            return True
        if bug.user_id == self.id:
            return True
        if self.role == 'team_lead' and bug.team_id:
            # Check if user is team lead of the bug's team
            try:
                from models import TeamMember
                team_membership = TeamMember.query.filter_by(
                    user_id=self.id, 
                    team_id=bug.team_id, 
                    role='lead'
                ).first()
                return team_membership is not None
            except:
                return False
        return False


class BugReport(db.Model):
    __tablename__ = 'bug_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    parsed_steps = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reproducibility_score = db.Column(db.Numeric(5,2), default=0)
    reproducibility_confidence = db.Column(db.String(20), default='unknown')
    recording_path = db.Column(db.String(255))
    exported_to_github = db.Column(db.Boolean, default=False)
    exported_to_jira = db.Column(db.Boolean, default=False)
    github_issue_url = db.Column(db.String(255))
    jira_issue_url = db.Column(db.String(255))
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    assigned_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    github_repo = db.Column(db.String(255))  # owner/repo format
    ai_explanation = db.Column(db.Text)  # ChatGPT explanation
    
    # Relationship with attachments
    attachments = db.relationship('Attachment', backref='bug_report', lazy=True, cascade='all, delete-orphan')
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_bugs')
    team = db.relationship('Team', backref='bug_reports')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'parsed_steps': self.parsed_steps,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id,
            'user_name': f"{self.user.first_name} {self.user.last_name}" if self.user else "Anonymous",
            'attachments': [attachment.to_dict() for attachment in self.attachments],
            'reproducibility_score': float(self.reproducibility_score) if self.reproducibility_score else 0,
            'reproducibility_confidence': self.reproducibility_confidence,
            'recording_path': self.recording_path,
            'exported_to_github': self.exported_to_github,
            'exported_to_jira': self.exported_to_jira,
            'github_issue_url': self.github_issue_url,
            'jira_issue_url': self.jira_issue_url,
            'assigned_to': self.assigned_to,
            'assigned_user_name': f"{self.assigned_user.first_name} {self.assigned_user.last_name}".strip() if self.assigned_user else None,
            'assigned_user_email': self.assigned_user.email if self.assigned_user else None,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'team_id': self.team_id,
            'team_name': self.team.name if self.team else None,
            'priority': self.priority,
            'status': self.status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'github_repo': self.github_repo,
            'ai_explanation': self.ai_explanation
        }


class Attachment(db.Model):
    __tablename__ = 'attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)  # Base64 encoded content
    bug_report_id = db.Column(db.Integer, db.ForeignKey('bug_reports.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_size': self.file_size,
            'bug_report_id': self.bug_report_id
        }


class EmailSubscriber(db.Model):
    __tablename__ = 'email_subscribers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    source = db.Column(db.String(50), default='website')  # website, admin_invite, etc.
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'subscribed_at': self.subscribed_at.isoformat() if self.subscribed_at else None,
            'is_active': self.is_active,
            'source': self.source
        }


class UserFeedback(db.Model):
    __tablename__ = 'user_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100))
    feedback_type = db.Column(db.String(50), nullable=False)  # pain_point, feature_request, bug_report, general
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'feedback_type': self.feedback_type,
            'subject': self.subject,
            'message': self.message,
            'priority': self.priority,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'user_id': self.user_id
        }


class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'project_id': self.project_id,
            'is_active': self.is_active,
            'member_count': len([m for m in self.members if m.is_active])
        }


class TeamMember(db.Model):
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # admin, member, viewer
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    github_username = db.Column(db.String(100))  # For GitHub integration
    
    # Relationships
    user = db.relationship('User', backref='team_memberships')
    
    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'is_active': self.is_active,
            'github_username': self.github_username,
            'user_name': f"{self.user.first_name} {self.user.last_name}".strip() if self.user else None,
            'user_email': self.user.email if self.user else None
        }


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    github_repo = db.Column(db.String(255))  # Default repo for this project
    
    # Relationships
    bug_reports = db.relationship('BugReport', backref='project', lazy=True)
    teams = db.relationship('Team', backref='project', lazy=True, foreign_keys='Team.project_id')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'is_active': self.is_active,
            'github_repo': self.github_repo,
            'bug_count': len(self.bug_reports),
            'team_count': len([t for t in self.teams if t.is_active])
        }