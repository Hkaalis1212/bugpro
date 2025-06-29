#!/usr/bin/env python3
"""
Customer Data Audit Script
Validates all customer/user data integrity and relationships
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, BugReport, Team, Project, Attachment, EmailSubscriber, UserFeedback
from datetime import datetime

class CustomerDataAuditor:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.stats = {}
    
    def log_issue(self, severity, message, details=None):
        """Log data integrity issue"""
        issue = {
            'severity': severity,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        if severity == 'ERROR':
            self.issues.append(issue)
            print(f"❌ ERROR: {message}")
        elif severity == 'WARNING':
            self.warnings.append(issue)
            print(f"⚠️  WARNING: {message}")
        else:
            print(f"ℹ️  INFO: {message}")
        
        if details:
            print(f"   Details: {details}")
    
    def audit_user_data(self):
        """Audit user data integrity"""
        print("\n🔍 Auditing User Data...")
        
        users = User.query.all()
        self.stats['total_users'] = len(users)
        
        subscription_counts = {}
        role_counts = {}
        status_counts = {}
        
        for user in users:
            # Check required fields
            if not user.email:
                self.log_issue('ERROR', f'User {user.id} missing email')
            
            if not user.first_name or not user.last_name:
                self.log_issue('WARNING', f'User {user.id} missing name fields')
            
            # Check email format
            if user.email and '@' not in user.email:
                self.log_issue('ERROR', f'User {user.id} has invalid email format: {user.email}')
            
            # Check subscription data consistency
            if user.subscription_plan not in ['freemium', 'standard', 'premium']:
                self.log_issue('ERROR', f'User {user.id} has invalid subscription plan: {user.subscription_plan}')
            
            if user.subscription_status not in ['active', 'cancelled', 'past_due', 'trialing', 'cancel_at_period_end']:
                self.log_issue('ERROR', f'User {user.id} has invalid subscription status: {user.subscription_status}')
            
            # Check role consistency
            if user.role not in ['user', 'team_lead', 'admin']:
                self.log_issue('ERROR', f'User {user.id} has invalid role: {user.role}')
            
            if user.is_admin and user.role != 'admin':
                self.log_issue('WARNING', f'User {user.id} is_admin=True but role={user.role}')
            
            # Check report count validity
            if user.reports_this_month < 0:
                self.log_issue('ERROR', f'User {user.id} has negative report count: {user.reports_this_month}')
            
            # Check plan limits vs actual usage
            limits = user.get_plan_limits()
            if limits['reports_per_month'] != -1 and user.reports_this_month > limits['reports_per_month']:
                self.log_issue('WARNING', f'User {user.id} exceeded monthly limit: {user.reports_this_month}/{limits["reports_per_month"]}')
            
            # Collect statistics
            subscription_counts[user.subscription_plan] = subscription_counts.get(user.subscription_plan, 0) + 1
            role_counts[user.role] = role_counts.get(user.role, 0) + 1
            status_counts[user.subscription_status] = status_counts.get(user.subscription_status, 0) + 1
        
        self.stats['subscription_distribution'] = subscription_counts
        self.stats['role_distribution'] = role_counts
        self.stats['status_distribution'] = status_counts
        
        print(f"   Users audited: {len(users)}")
        print(f"   Subscription distribution: {subscription_counts}")
        print(f"   Role distribution: {role_counts}")
    
    def audit_bug_reports(self):
        """Audit bug report data integrity"""
        print("\n🐛 Auditing Bug Reports...")
        
        reports = BugReport.query.all()
        self.stats['total_reports'] = len(reports)
        
        orphaned_reports = 0
        reports_by_user = {}
        
        for report in reports:
            # Check required fields
            if not report.title:
                self.log_issue('ERROR', f'Bug report {report.id} missing title')
            
            if not report.description:
                self.log_issue('ERROR', f'Bug report {report.id} missing description')
            
            # Check user relationship
            if report.user_id:
                user = User.query.get(report.user_id)
                if not user:
                    self.log_issue('ERROR', f'Bug report {report.id} references non-existent user {report.user_id}')
                    orphaned_reports += 1
                else:
                    reports_by_user[user.id] = reports_by_user.get(user.id, 0) + 1
            else:
                self.log_issue('WARNING', f'Bug report {report.id} has no associated user')
                orphaned_reports += 1
            
            # Check status and priority values
            if report.status not in ['open', 'in_progress', 'resolved', 'closed']:
                self.log_issue('ERROR', f'Bug report {report.id} has invalid status: {report.status}')
            
            if report.priority not in ['low', 'medium', 'high', 'critical']:
                self.log_issue('ERROR', f'Bug report {report.id} has invalid priority: {report.priority}')
            
            # Check reproducibility score
            if report.reproducibility_score and (report.reproducibility_score < 0 or report.reproducibility_score > 100):
                self.log_issue('WARNING', f'Bug report {report.id} has invalid reproducibility score: {report.reproducibility_score}')
        
        self.stats['orphaned_reports'] = orphaned_reports
        self.stats['reports_by_user'] = reports_by_user
        
        print(f"   Reports audited: {len(reports)}")
        print(f"   Orphaned reports: {orphaned_reports}")
    
    def audit_attachments(self):
        """Audit file attachments"""
        print("\n📎 Auditing Attachments...")
        
        attachments = Attachment.query.all()
        self.stats['total_attachments'] = len(attachments)
        
        total_size = 0
        orphaned_attachments = 0
        
        for attachment in attachments:
            # Check bug report relationship
            if attachment.bug_report_id:
                report = BugReport.query.get(attachment.bug_report_id)
                if not report:
                    self.log_issue('ERROR', f'Attachment {attachment.id} references non-existent bug report {attachment.bug_report_id}')
                    orphaned_attachments += 1
            
            # Check required fields
            if not attachment.filename:
                self.log_issue('ERROR', f'Attachment {attachment.id} missing filename')
            
            if not attachment.content:
                self.log_issue('ERROR', f'Attachment {attachment.id} missing content')
            
            # Check file size
            if attachment.file_size <= 0:
                self.log_issue('ERROR', f'Attachment {attachment.id} has invalid file size: {attachment.file_size}')
            
            total_size += attachment.file_size
        
        self.stats['total_attachment_size'] = total_size
        self.stats['orphaned_attachments'] = orphaned_attachments
        
        print(f"   Attachments audited: {len(attachments)}")
        print(f"   Total size: {total_size / (1024*1024):.2f} MB")
        print(f"   Orphaned attachments: {orphaned_attachments}")
    
    def audit_teams_and_projects(self):
        """Audit team and project data"""
        print("\n👥 Auditing Teams and Projects...")
        
        teams = Team.query.all()
        projects = Project.query.all()
        
        self.stats['total_teams'] = len(teams)
        self.stats['total_projects'] = len(projects)
        
        for team in teams:
            # Check project relationship
            if team.project_id:
                project = Project.query.get(team.project_id)
                if not project:
                    self.log_issue('ERROR', f'Team {team.id} references non-existent project {team.project_id}')
            
            # Check creator relationship
            if team.created_by:
                creator = User.query.get(team.created_by)
                if not creator:
                    self.log_issue('ERROR', f'Team {team.id} references non-existent creator {team.created_by}')
        
        for project in projects:
            # Check creator relationship
            if project.created_by:
                creator = User.query.get(project.created_by)
                if not creator:
                    self.log_issue('ERROR', f'Project {project.id} references non-existent creator {project.created_by}')
        
        print(f"   Teams audited: {len(teams)}")
        print(f"   Projects audited: {len(projects)}")
    
    def audit_subscription_consistency(self):
        """Audit subscription data consistency"""
        print("\n💳 Auditing Subscription Consistency...")
        
        # Check users with Stripe customer IDs
        users_with_stripe = User.query.filter(User.stripe_customer_id.isnot(None)).all()
        
        for user in users_with_stripe:
            # Users with Stripe IDs should not be on freemium unless cancelled
            if user.subscription_plan == 'freemium' and user.subscription_status not in ['cancelled', 'past_due']:
                self.log_issue('WARNING', f'User {user.id} has Stripe ID but freemium plan')
            
            # Check for consistent subscription status
            if user.subscription_status == 'active' and user.subscription_plan == 'freemium':
                self.log_issue('WARNING', f'User {user.id} has active status but freemium plan')
        
        # Check for users with paid plans but no Stripe ID
        paid_users = User.query.filter(User.subscription_plan.in_(['standard', 'premium'])).all()
        
        for user in paid_users:
            if not user.stripe_customer_id and user.subscription_status == 'active':
                self.log_issue('WARNING', f'User {user.id} has paid plan but no Stripe customer ID')
        
        print(f"   Users with Stripe IDs: {len(users_with_stripe)}")
        print(f"   Users with paid plans: {len(paid_users)}")
    
    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "="*60)
        print("CUSTOMER DATA AUDIT REPORT")
        print("="*60)
        
        print(f"Audit completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Statistics summary
        print(f"\n📊 Statistics:")
        for key, value in self.stats.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for k, v in value.items():
                    print(f"     {k}: {v}")
            else:
                print(f"   {key}: {value}")
        
        # Issues summary
        print(f"\n🔍 Issues Found:")
        print(f"   Errors: {len(self.issues)}")
        print(f"   Warnings: {len(self.warnings)}")
        
        if self.issues:
            print(f"\n❌ Critical Errors:")
            for issue in self.issues:
                print(f"   - {issue['message']}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings[:10]:  # Show first 10 warnings
                print(f"   - {warning['message']}")
            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more warnings")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        if len(self.issues) == 0:
            if len(self.warnings) == 0:
                print("   ✅ EXCELLENT: No data integrity issues found")
            elif len(self.warnings) <= 5:
                print("   🟢 GOOD: Minor warnings found, no critical issues")
            else:
                print("   🟡 ACCEPTABLE: Multiple warnings found, review recommended")
        else:
            print("   🔴 ATTENTION REQUIRED: Critical data integrity issues found")
            print("   Immediate action needed to fix errors")
        
        return len(self.issues) == 0

def main():
    """Run customer data audit"""
    with app.app_context():
        auditor = CustomerDataAuditor()
        
        # Run all audit checks
        auditor.audit_user_data()
        auditor.audit_bug_reports()
        auditor.audit_attachments()
        auditor.audit_teams_and_projects()
        auditor.audit_subscription_consistency()
        
        # Generate final report
        success = auditor.generate_report()
        
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()