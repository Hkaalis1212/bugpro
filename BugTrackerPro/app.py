import os
import logging
import base64
import asyncio
import requests
from datetime import datetime
from urllib.parse import urlparse, urljoin
from flask import Flask, request, jsonify, render_template, render_template_string, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.utils import secure_filename
from openai import OpenAI
from github import Github
# Advanced features will be imported later

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure the database
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL environment variable is not set")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = None

# Initialize new feature components after app creation
def initialize_advanced_features():
    global reproducibility_scorer, screen_recorder, export_manager
    try:
        from reproducibility_scorer import ReproducibilityScorer
        from screen_recorder import ScreenRecorder
        from export_integrations import ExportManager
        reproducibility_scorer = ReproducibilityScorer()
        screen_recorder = ScreenRecorder()
        export_manager = ExportManager()
        app.logger.info("Advanced features initialized successfully")
    except ImportError as e:
        app.logger.warning(f"Advanced features not available: {e}")
        reproducibility_scorer = None
        screen_recorder = None
        export_manager = None

# Initialize features
reproducibility_scorer = None
screen_recorder = None
export_manager = None

# File upload configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'log', 'json', 'xml'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_safe_url(target):
    """Check if a URL is safe for redirect (same origin only)."""
    if not target:
        return False
    
    # Parse the target URL directly (don't use urljoin to avoid bypass)
    try:
        test_url = urlparse(target)
    except (ValueError, AttributeError):
        return False
    
    # Only allow relative URLs (no scheme or netloc)
    # This prevents redirects to external domains
    if test_url.scheme or test_url.netloc:
        return False
    
    # Ensure it starts with / and doesn't contain dangerous patterns
    return target.startswith('/') and not target.startswith('//')

# Create database tables
with app.app_context():
    import models  # noqa: F401
    db.create_all()

@app.route('/ping')
def ping():
    """Simple health check route."""
    return jsonify({'status': 'alive', 'message': 'Server is running'})

@app.route('/api/health')
def api_health():
    """API health check for external systems."""
    return jsonify({
        "status": "healthy",
        "service": "bug-tracker-pro",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "submit_bug": "/api/submit",
            "health_check": "/api/health",
            "web_interface": "/",
            "documentation": "/api/submit (GET for docs)"
        },
        "note": "This API accepts bug reports from AI chatbots and external systems"
    })

@app.route('/api/submit', methods=['POST', 'GET'])
def api_submit_bug():
    """API endpoint for external bug submissions from AI chatbots."""
    if request.method == 'GET':
        return jsonify({
            "message": "Bug submission API endpoint",
            "method": "POST",
            "required_fields": ["title", "description"],
            "optional_fields": ["priority", "reporter_name", "reporter_email"],
            "example": {
                "title": "Login button not working",
                "description": "When clicking the login button, nothing happens. Browser console shows no errors.",
                "priority": "medium",
                "reporter_name": "AI Assistant",
                "reporter_email": "ai@system.com"
            }
        })
    
    try:
        from models import User, BugReport
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        priority = data.get('priority', 'medium')
        reporter_name = data.get('reporter_name', 'External API')
        reporter_email = data.get('reporter_email', 'api@external.com')
        
        if not title or not description:
            return jsonify({
                "success": False,
                "error": "Title and description are required"
            }), 400
        
        if len(title) < 5:
            return jsonify({
                "success": False,
                "error": "Title must be at least 5 characters long"
            }), 400
        
        if len(description) < 10:
            return jsonify({
                "success": False,
                "error": "Description must be at least 10 characters long"
            }), 400
        
        # Create anonymous user for API submissions if needed
        api_user = User.query.filter_by(email='api@external.com').first()
        if not api_user:
            from werkzeug.security import generate_password_hash
            api_user = User(
                email='api@external.com',
                first_name='API',
                last_name='User'
            )
            api_user.set_password('api_access_only')
            db.session.add(api_user)
            db.session.commit()
        
        # Parse with AI if available
        parsed_steps = "API submission - please refer to description for details"
        ai_explanation = None
        
        try:
            if os.environ.get('OPENAI_API_KEY'):
                parsed_steps = parse_bug_description(description)
                ai_explanation = generate_ai_explanation(title, description, parsed_steps)
        except Exception as e:
            logging.warning(f"AI parsing failed: {e}")
        
        # Create bug report
        bug_report = BugReport(
            title=title,
            description=description,
            parsed_steps=parsed_steps,
            priority=priority,
            status='open',
            user_id=api_user.id
        )
        
        db.session.add(bug_report)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Bug report submitted successfully",
            "bug_id": bug_report.id,
            "title": title,
            "priority": priority,
            "status": "open",
            "ai_analysis": bool(ai_explanation),
            "reproduction_steps": parsed_steps[:200] + "..." if len(parsed_steps) > 200 else parsed_steps
        })
        
    except Exception as e:
        logging.error(f"API submission error: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/')
def index():
    """Render the advanced bug reporting interface."""
    return render_template("index.html")



@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        from models import User
        
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        from models import User
        
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests."""
    if request.method == 'POST':
        from models import User
        
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            reset_token = user.generate_reset_token()
            
            # Send reset email
            try:
                send_password_reset_email(user, reset_token)
                # In development mode, show the reset link directly
                import os
                if not os.environ.get('SENDGRID_API_KEY'):
                    reset_url = f"{request.url_root}reset-password/{reset_token}"
                    flash(f'Password reset link (DEV MODE): <a href="{reset_url}" class="text-warning">{reset_url}</a>', 'success')
                else:
                    flash('Password reset instructions have been sent to your email.', 'success')
            except Exception as e:
                app.logger.error(f"Failed to send reset email: {str(e)}")
                flash('Failed to send reset email. Please try again later.', 'error')
        else:
            # Don't reveal if email exists or not for security
            flash('If the email exists in our system, password reset instructions have been sent.', 'success')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token."""
    from models import User
    
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset token. Please request a new password reset.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('reset_password.html', token=token)
        
        # Reset the password
        user.reset_password(new_password)
        
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)


def send_password_reset_email(user, reset_token):
    """Send password reset email to user."""
    import os
    
    # Check if SendGrid is configured
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    
    if sendgrid_api_key:
        # Use SendGrid for production
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
            
            reset_url = f"{request.url_root}reset-password/{reset_token}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #1f2937; color: white; padding: 20px; text-align: center;">
                    <h1>Bug Reporter - Password Reset</h1>
                </div>
                
                <div style="padding: 30px;">
                    <h2>Password Reset Request</h2>
                    <p>Hello {user.first_name},</p>
                    
                    <p>You requested a password reset for your Bug Reporter account. Click the button below to reset your password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #3b82f6;">{reset_url}</p>
                    
                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        This link will expire in 1 hour. If you didn't request this password reset, please ignore this email.
                    </p>
                </div>
                
                <div style="background: #f3f4f6; padding: 20px; text-align: center; color: #666; font-size: 12px;">
                    Bug Reporter Team
                </div>
            </body>
            </html>
            """
            
            message = Mail(
                from_email='noreply@bugreporter.com',
                to_emails=user.email,
                subject='Reset Your Bug Reporter Password',
                html_content=html_content
            )
            
            response = sg.send(message)
            app.logger.info(f"Password reset email sent to {user.email}")
            
        except Exception as e:
            app.logger.error(f"SendGrid error: {str(e)}")
            raise e
    else:
        # Development mode - log the reset URL
        reset_url = f"{request.url_root}reset-password/{reset_token}"
        app.logger.info(f"Password reset URL for {user.email}: {reset_url}")
        print(f"🔗 Password Reset Link for {user.email}: {reset_url}")


def admin_required(f):
    """Decorator to require admin access."""
    from functools import wraps
    
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Render the admin dashboard for managing bug reports."""
    return render_template("admin.html")

@app.route('/submit', methods=['POST'])
def submit():
    """Handle bug report submission with AI parsing."""
    # Check if this is from the simple form (no files)
    is_simple_form = 'repo' in request.form and not request.files.get('attachments')
    from models import BugReport, Attachment
    
    try:
        # Get form data (handling both JSON and form data)
        if request.is_json:
            data = request.get_json()
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            files = []
        else:
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            files = request.files.getlist('attachments')
        
        # Validate input
        if not title:
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400
            
        if not description:
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
        
        # Parse bug description using AI
        try:
            parsed_steps = parse_bug_description(description) if openai_client else "AI parsing not available"
        except Exception as e:
            app.logger.warning(f"OpenAI API error: {e}")
            parsed_steps = "Please refer to the bug description for reproduction steps. AI parsing temporarily unavailable."
        
        # Calculate reproducibility score
        attachments_for_scoring = [{'filename': f.filename} for f in files if f and f.filename]
        if reproducibility_scorer:
            repro_metrics = reproducibility_scorer.score_bug_report(title, description, attachments_for_scoring)
        else:
            # Fallback scoring
            class SimpleMetrics:
                def __init__(self):
                    self.score = 50.0
                    self.confidence = "Medium"
                    self.factors = ["Basic analysis performed"]
                    self.recommendations = ["Enable advanced features for detailed scoring"]
            repro_metrics = SimpleMetrics()
        
        # Get assignment info (handle both simple and advanced forms)
        project_id = request.form.get('project_id')
        assigned_to = request.form.get('assigned_to')
        team_id = request.form.get('team_id')
        priority = request.form.get('priority', 'medium')
        # Handle GitHub repo from simple form or advanced form
        github_repo = request.form.get('repo', '').strip() or request.form.get('github_repo', '').strip()
        
        # Generate AI explanation using ChatGPT
        ai_explanation = None
        try:
            ai_explanation = generate_ai_explanation(title, description, parsed_steps) if openai_client else None
        except Exception as e:
            app.logger.warning(f"ChatGPT explanation generation failed: {e}")
            ai_explanation = None
        
        # Create bug report in database
        bug_report = BugReport(
            title=title,
            description=description,
            parsed_steps=parsed_steps,
            user_id=current_user.id if current_user.is_authenticated else None,
            project_id=int(project_id) if project_id and project_id.isdigit() else None,
            assigned_to=int(assigned_to) if assigned_to and assigned_to.isdigit() else None,
            team_id=int(team_id) if team_id and team_id.isdigit() else None,
            priority=priority,
            assigned_at=datetime.utcnow() if assigned_to else None,
            reproducibility_score=repro_metrics.score,
            reproducibility_confidence=repro_metrics.confidence.lower(),
            github_repo=github_repo,
            ai_explanation=ai_explanation
        )
        
        db.session.add(bug_report)
        db.session.flush()  # Get the ID without committing
        
        # Process file attachments
        for file in files:
            if file and file.filename:
                if not allowed_file(file.filename):
                    db.session.rollback()
                    return jsonify({
                        'success': False,
                        'error': f'File type not allowed: {file.filename}'
                    }), 400
                
                # Check file size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > MAX_FILE_SIZE:
                    db.session.rollback()
                    return jsonify({
                        'success': False,
                        'error': f'File too large: {file.filename} (max 10MB)'
                    }), 400
                
                # Read file content
                file_content = file.read()
                file.seek(0)  # Reset for potential reuse
                
                # Create attachment record
                attachment = Attachment(
                    filename=secure_filename(file.filename),
                    file_size=file_size,
                    content=base64.b64encode(file_content).decode('utf-8'),
                    bug_report_id=bug_report.id
                )
                
                db.session.add(attachment)
        
        # Commit the transaction
        db.session.commit()
        
        app.logger.info(f"Bug report submitted: ID {bug_report.id}, Title: {title}")
        
        # Handle different response types
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': True,
                'message': 'Bug report submitted successfully!',
                'report_id': bug_report.id,
                'parsed_steps': parsed_steps,
                'reproducibility_score': float(repro_metrics.score),
                'reproducibility_confidence': repro_metrics.confidence,
                'reproducibility_factors': repro_metrics.factors,
                'reproducibility_recommendations': repro_metrics.recommendations
            })
        elif is_simple_form:
            # For simple form, show a success page
            return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Bug Submitted - BugTrackerPro 🐛</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 text-gray-800 font-sans">
  <div class="max-w-xl mx-auto mt-10 p-6 bg-white rounded-2xl shadow-lg">
    <div class="text-center">
      <div class="mb-4">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
          <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
          </svg>
        </div>
      </div>
      <h1 class="text-2xl font-bold text-green-600 mb-2">Bug Report Submitted!</h1>
      <p class="text-gray-600 mb-4">Report ID: <span class="font-mono text-blue-600">#{{ report_id }}</span></p>
      
      <div class="bg-gray-50 p-4 rounded-lg mb-6 text-left">
        <h3 class="font-semibold mb-2">🤖 AI Analysis:</h3>
        <p class="text-sm text-gray-700">{{ parsed_steps }}</p>
      </div>
      
      <div class="space-y-3">
        <a href="/" class="block w-full bg-blue-600 text-white py-2 px-4 rounded-xl hover:bg-blue-700 transition">
          Submit Another Bug
        </a>
        <a href="/advanced" class="block w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-xl hover:bg-gray-300 transition">
          Use Advanced Form
        </a>
      </div>
    </div>
  </div>
</body>
</html>
            """, report_id=bug_report.id, parsed_steps=parsed_steps)
        else:
            # For advanced form submissions, redirect
            flash(f'Bug report submitted successfully! Report ID: #{bug_report.id}', 'success')
            return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error submitting bug report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while submitting the bug report. Please try again.'
        }), 500

@app.route('/reports', methods=['GET'])
@admin_required
def get_reports():
    """Get all bug reports (admin only)."""
    from models import BugReport
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        reports = BugReport.query.order_by(BugReport.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'reports': [report.to_dict() for report in reports.items],
            'total': reports.total,
            'pages': reports.pages,
            'current_page': page,
            'per_page': per_page
        })
    except Exception as e:
        app.logger.error(f"Error fetching reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching reports.'
        }), 500

@app.route('/reports/<int:report_id>', methods=['DELETE'])
@admin_required
def delete_report(report_id):
    """Delete a specific bug report (admin only)."""
    from models import BugReport
    
    try:
        report = BugReport.query.get_or_404(report_id)
        db.session.delete(report)
        db.session.commit()
        
        app.logger.info(f"Bug report deleted: ID {report_id} by admin {current_user.email}")
        
        return jsonify({
            'success': True,
            'message': 'Bug report deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting report {report_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while deleting the report.'
        }), 500

@app.route('/reports/<int:report_id>/download/<int:attachment_id>')
@admin_required
def download_attachment(report_id, attachment_id):
    """Download a specific attachment (admin only)."""
    from models import Attachment
    import base64
    from flask import Response
    
    try:
        attachment = Attachment.query.filter_by(
            id=attachment_id, 
            bug_report_id=report_id
        ).first_or_404()
        
        # Decode the base64 content
        file_content = base64.b64decode(attachment.content)
        
        return Response(
            file_content,
            headers={
                'Content-Disposition': f'attachment; filename="{attachment.filename}"',
                'Content-Type': 'application/octet-stream'
            }
        )
        
    except Exception as e:
        app.logger.error(f"Error downloading attachment {attachment_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while downloading the attachment.'
        }), 500

@app.route('/create-admin')
def create_admin():
    """Create initial admin user (remove in production)."""
    from models import User
    
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        return 'Admin user created: admin@example.com / admin123'
    return 'Admin user already exists'

def parse_bug_description(description):
    """
    Parse bug description using OpenAI to extract reproduction steps.
    
    Args:
        description (str): The bug description text
        
    Returns:
        str: Parsed reproduction steps or fallback manual steps
    """
    if not openai_client:
        return "Please refer to the bug description for reproduction steps. AI parsing not configured."
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert at analyzing bug reports. Extract clear, step-by-step reproduction instructions from the bug description. Format your response as a numbered list of specific, actionable steps that someone could follow to reproduce the issue. If the description doesn't contain clear steps, provide the best interpretation based on the information given."
                },
                {
                    "role": "user", 
                    "content": f"Please extract the step-by-step reproduction steps from this bug report:\n\n{description}"
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        parsed_steps = response.choices[0].message.content or ""
        parsed_steps = parsed_steps.strip()
        app.logger.info("Successfully parsed bug description with AI")
        return parsed_steps
        
    except Exception as e:
        app.logger.error(f"AI parsing failed: {str(e)}")
        # Return a simple manual parsing fallback
        return "Please refer to the bug description for reproduction steps. AI parsing temporarily unavailable."

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error occurred'
    }), 500

# Subscription routes
@app.route('/pricing')
def pricing():
    """Display pricing plans."""
    return render_template('pricing.html')

@app.route('/payment-flow')
def payment_flow():
    """Display interactive payment flow visualization."""
    plan = request.args.get('plan', 'standard')
    plan_name = plan.title()
    plan_price = '19.99' if plan == 'premium' else '9.99'
    
    return render_template('payment_flow.html', 
                         plan_name=plan_name, 
                         plan_price=plan_price,
                         plan=plan)

@app.route('/pricing/teams')
def team_pricing():
    """Display team-based pricing with project analytics."""
    return render_template('pricing_tiers.html')

@app.route('/subscription/create-checkout', methods=['POST'])
@login_required
def create_checkout():
    """Create Stripe checkout session."""
    import stripe
    
    # Check if Stripe is configured
    stripe_key = os.environ.get('STRIPE_SECRET_KEY')
    if not stripe_key:
        flash('Payment processing is temporarily unavailable. Please contact support for subscription assistance.', 'info')
        return redirect(url_for('pricing'))
    
    stripe.api_key = stripe_key
    
    plan = request.form.get('plan')
    if plan not in ['standard', 'premium']:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('pricing'))
    
    try:
        # Get proper domain URL with HTTPS
        if 'replit.dev' in request.host:
            domain = f"https://{request.host}"
        else:
            domain = request.host_url.rstrip('/')
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{plan.title()} Plan - Bug Tracker',
                        'description': f'Monthly subscription to Bug Tracker {plan.title()} plan'
                    },
                    'unit_amount': 999 if plan == 'standard' else 1999,  # $9.99 or $19.99
                    'recurring': {'interval': 'month'}
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f'{domain}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{domain}/pricing?cancelled=true',
            metadata={
                'user_id': str(current_user.id),
                'plan': plan
            },
            allow_promotion_codes=True,
            billing_address_collection='auto'
        )
        
        # Log the checkout URL for debugging
        app.logger.info(f"Redirecting to Stripe checkout: {checkout_session.url}")
        
        # Direct redirect to Stripe checkout
        # Store session ID for status tracking
        session['stripe_session_id'] = checkout_session.id
        
        return redirect(checkout_session.url)
        
    except Exception as e:
        app.logger.error(f"Stripe checkout error: {e}")
        flash('Unable to process payment at this time. Please try again later.', 'error')
        return redirect(url_for('pricing'))

@app.route('/subscription/success')
def subscription_success():
    """Handle successful subscription."""
    session_id = request.args.get('session_id')
    
    if session_id and current_user.is_authenticated:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        try:
            # Retrieve the session from Stripe to verify completion
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            if checkout_session.payment_status == 'paid':
                # Get plan from metadata
                plan = checkout_session.metadata.get('plan', 'standard')
                customer_id = checkout_session.customer
                
                # Update user subscription with verified data
                current_user.subscription_status = 'active'
                current_user.subscription_plan = plan
                current_user.stripe_customer_id = customer_id
                current_user.subscription_end_date = None  # For ongoing subscriptions
                
                # Reset monthly report count for new subscribers
                if current_user.subscription_plan != 'freemium':
                    current_user.reports_this_month = 0
                
                db.session.commit()
                
                flash(f'Your {plan.title()} subscription has been activated successfully!', 'success')
                app.logger.info(f"User {current_user.id} subscription activated: {plan}")
            else:
                flash('Payment verification failed. Please contact support.', 'error')
                app.logger.warning(f"Payment verification failed for session {session_id}")
                
        except Exception as e:
            flash('Error processing subscription. Please contact support.', 'error')
            app.logger.error(f"Subscription processing error: {e}")
    else:
        flash('Invalid subscription session.', 'error')
    
    return render_template('subscription_success.html')

@app.route('/api/payment-status/<session_id>')
@login_required
def payment_status(session_id):
    """Check payment status for real-time updates."""
    import stripe
    
    if not os.environ.get('STRIPE_SECRET_KEY'):
        return jsonify({'error': 'Stripe not configured'}), 503
    
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            return jsonify({
                'status': 'complete',
                'plan': session.metadata.get('plan'),
                'customer_id': session.customer
            })
        elif session.payment_status == 'unpaid' and session.status == 'expired':
            return jsonify({
                'status': 'failed',
                'error': 'Session expired'
            })
        else:
            return jsonify({
                'status': 'pending'
            })
            
    except Exception as e:
        app.logger.error(f"Error checking payment status: {e}")
        return jsonify({'error': 'Unable to check status'}), 500

@app.route('/api/subscription/status')
@login_required
def subscription_status():
    """Get current user's subscription status."""
    return jsonify({
        'plan': current_user.subscription_plan,
        'status': current_user.subscription_status,
        'reports_this_month': current_user.get_monthly_report_count()
    })

@app.route('/subscription/cancelled')
def subscription_cancelled():
    """Handle cancelled subscription."""
    return render_template('subscription_cancelled.html')

@app.route('/manage-subscription')
@login_required
def manage_subscription():
    """Redirect to Stripe billing portal for subscription management."""
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        if not current_user.stripe_customer_id:
            flash('No subscription found. Please subscribe first.', 'info')
            return redirect(url_for('pricing'))
        
        # Create a billing portal session with proper return URL
        domain = request.host_url.rstrip('/')
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{domain}/dashboard"
        )
        
        app.logger.info(f"User {current_user.id} accessing billing portal")
        return redirect(portal_session.url)
            
    except stripe.error.InvalidRequestError as e:
        app.logger.error(f"Invalid Stripe request: {e}")
        flash('Invalid subscription data. Please contact support.', 'error')
        return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"Billing portal error: {e}")
        flash('Unable to access billing portal. Please contact support.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user subscription."""
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Find and cancel the user's subscription
        if current_user.stripe_customer_id:
            # List subscriptions for the customer
            subscriptions = stripe.Subscription.list(
                customer=current_user.stripe_customer_id,
                status='active'
            )
            
            for subscription in subscriptions.data:
                # Cancel at period end to allow access until billing cycle ends
                stripe.Subscription.modify(
                    subscription.id,
                    cancel_at_period_end=True
                )
                
                # Update user status but keep access until period end
                current_user.subscription_status = 'cancel_at_period_end'
                current_user.subscription_end_date = datetime.fromtimestamp(subscription.current_period_end)
                db.session.commit()
                
                flash('Your subscription will be cancelled at the end of your current billing period.', 'info')
                app.logger.info(f"User {current_user.id} scheduled subscription cancellation")
                return redirect(url_for('subscription_cancelled'))
        
        flash('No active subscription found.', 'info')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        app.logger.error(f"Subscription cancellation error: {e}")
        flash('Unable to cancel subscription. Please contact support.', 'error')
        return redirect(url_for('dashboard'))

def stripe_webhook():
    """Handle Stripe webhooks for subscription events."""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    # Get webhook secret from environment
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if not webhook_secret:
        app.logger.warning("Stripe webhook secret not configured")
        return '', 400
    
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Verify webhook signature
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_successful_payment(session)
            
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            handle_subscription_renewal(invoice)
            
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            handle_payment_failure(invoice)
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            handle_subscription_cancellation(subscription)
        
        return '', 200
        
    except ValueError as e:
        app.logger.error(f"Invalid payload: {e}")
        return '', 400
    except stripe.error.SignatureVerificationError as e:
        app.logger.error(f"Invalid signature: {e}")
        return '', 400
    except Exception as e:
        app.logger.error(f"Webhook error: {e}")
        return '', 400

def handle_successful_payment(session):
    """Handle successful payment completion."""
    try:
        user_id = session['metadata'].get('user_id')
        plan = session['metadata'].get('plan')
        customer_id = session['customer']
        
        if user_id and plan:
            user = User.query.get(int(user_id))
            if user:
                user.subscription_status = 'active'
                user.subscription_plan = plan
                user.stripe_customer_id = customer_id
                user.reports_this_month = 0  # Reset for new billing cycle
                db.session.commit()
                
                app.logger.info(f"Webhook: User {user_id} subscription activated via webhook")
                
    except Exception as e:
        app.logger.error(f"Error handling successful payment: {e}")

def handle_subscription_renewal(invoice):
    """Handle successful subscription renewal."""
    try:
        customer_id = invoice['customer']
        
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.subscription_status = 'active'
            user.reports_this_month = 0  # Reset monthly usage
            db.session.commit()
            
            app.logger.info(f"Webhook: User {user.id} subscription renewed")
            
    except Exception as e:
        app.logger.error(f"Error handling subscription renewal: {e}")

def handle_payment_failure(invoice):
    """Handle failed payment attempts."""
    try:
        customer_id = invoice['customer']
        
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            # Don't immediately cancel, but mark as past due
            if user.subscription_status == 'active':
                user.subscription_status = 'past_due'
                db.session.commit()
                
                app.logger.warning(f"Webhook: Payment failed for user {user.id}")
                
    except Exception as e:
        app.logger.error(f"Error handling payment failure: {e}")

def handle_subscription_cancellation(subscription):
    """Handle subscription cancellation."""
    try:
        customer_id = subscription['customer']
        
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.subscription_status = 'cancelled'
            user.subscription_plan = 'freemium'
            user.subscription_end_date = datetime.utcnow()
            db.session.commit()
            
            app.logger.info(f"Webhook: User {user.id} subscription cancelled")
            
    except Exception as e:
        app.logger.error(f"Error handling subscription cancellation: {e}")

# Webhook route
@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook_endpoint():
    """Route handler for Stripe webhooks."""
    return stripe_webhook()

# New feature routes

@app.route('/recordings/<filename>')
def serve_recording(filename):
    """Serve screen recordings"""
    return send_from_directory('recordings', filename)

@app.route('/api/start-recording', methods=['POST'])
@admin_required
def start_screen_recording():
    """Start screen recording for bug reproduction"""
    try:
        data = request.get_json()
        bug_id = data.get('bug_id')
        duration = data.get('duration', 60)
        
        if not bug_id:
            return jsonify({'error': 'Bug ID required'}), 400
            
        bug_report = BugReport.query.get_or_404(bug_id)
        
        # Start recording in background (simplified for this demo)
        # In production, this would use async tasks
        recording_path = f"recordings/bug_{bug_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"
        
        # Update bug report with recording path
        bug_report.recording_path = recording_path
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recording started',
            'recording_path': recording_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<platform>/<int:bug_id>', methods=['POST'])
@admin_required
def export_bug_report(platform, bug_id):
    """Export bug report to GitHub or Jira"""
    try:
        bug_report = BugReport.query.get_or_404(bug_id)
        
        # Get export configuration from request
        data = request.get_json() or {}
        
        if platform.lower() == 'github':
            token = data.get('github_token') or os.environ.get('GITHUB_TOKEN')
            repo_owner = data.get('repo_owner')
            repo_name = data.get('repo_name')
            
            if not all([token, repo_owner, repo_name]):
                return jsonify({
                    'error': 'GitHub token, repo_owner, and repo_name required'
                }), 400
            
            export_manager.configure_github(token, repo_owner, repo_name)
            
        elif platform.lower() == 'jira':
            base_url = data.get('jira_url')
            username = data.get('jira_username')
            api_token = data.get('jira_token')
            project_key = data.get('project_key')
            
            if not all([base_url, username, api_token, project_key]):
                return jsonify({
                    'error': 'Jira URL, username, token, and project key required'
                }), 400
            
            export_manager.configure_jira(base_url, username, api_token, project_key)
        
        # Prepare bug report data
        bug_data = bug_report.to_dict()
        if bug_report.user:
            bug_data['user_email'] = bug_report.user.email
        
        # Prepare reproducibility score data
        repro_data = {
            'score': float(bug_report.reproducibility_score),
            'confidence': bug_report.reproducibility_confidence,
            'factors': ['Detailed analysis available'],
            'recommendations': ['Review original report for full details']
        }
        
        # Export to platform
        result = export_manager.export_to_platform(platform, bug_data, repro_data)
        
        if result['success']:
            # Update bug report with export status
            if platform.lower() == 'github':
                bug_report.exported_to_github = True
                bug_report.github_issue_url = result.get('github_url')
            elif platform.lower() == 'jira':
                bug_report.exported_to_jira = True
                bug_report.jira_issue_url = result.get('jira_url')
            
            db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reproducibility-score/<int:bug_id>')
@admin_required
def get_reproducibility_details(bug_id):
    """Get detailed reproducibility analysis for a bug report"""
    try:
        bug_report = BugReport.query.get_or_404(bug_id)
        
        # Recalculate detailed score
        attachments = [{'filename': att.filename} for att in bug_report.attachments]
        repro_metrics = reproducibility_scorer.score_bug_report(
            bug_report.title, 
            bug_report.description, 
            attachments
        )
        
        return jsonify({
            'score': repro_metrics.score,
            'confidence': repro_metrics.confidence,
            'factors': repro_metrics.factors,
            'missing_info': repro_metrics.missing_info,
            'recommendations': repro_metrics.recommendations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    """Handle email subscription for updates."""
    if request.method == 'POST':
        from models import EmailSubscriber
        
        email = request.form.get('email', '').strip().lower()
        source = request.form.get('source', 'website')
        
        if not email:
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('subscribe'))
        
        # Check if already subscribed
        existing = EmailSubscriber.query.filter_by(email=email).first()
        if existing:
            if existing.is_active:
                flash('You are already subscribed to updates!', 'info')
            else:
                # Reactivate subscription
                existing.is_active = True
                db.session.commit()
                flash('Your subscription has been reactivated!', 'success')
            return redirect(url_for('subscribe'))
        
        # Create new subscription
        subscriber = EmailSubscriber(email=email, source=source)
        db.session.add(subscriber)
        db.session.commit()
        
        flash('Thank you for subscribing! You will receive updates about new features and improvements.', 'success')
        return redirect(url_for('subscribe'))
    
    return render_template('subscribe.html')


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """Handle user feedback and pain points collection."""
    if request.method == 'POST':
        from models import UserFeedback
        
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        feedback_type = request.form.get('feedback_type', 'general')
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        priority = request.form.get('priority', 'medium')
        
        if not email or not subject or not message:
            flash('Please fill in all required fields', 'error')
            return render_template('feedback.html')
        
        # Create feedback entry
        user_feedback = UserFeedback(
            email=email,
            name=name,
            feedback_type=feedback_type,
            subject=subject,
            message=message,
            priority=priority,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(user_feedback)
        db.session.commit()
        
        flash('Thank you for your feedback! We will review it and get back to you if needed.', 'success')
        return redirect(url_for('feedback'))
    
    return render_template('feedback.html')


@app.route('/admin/subscribers')
@login_required
@admin_required
def admin_subscribers():
    """Admin view for managing email subscribers."""
    from models import EmailSubscriber
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    subscribers = EmailSubscriber.query.order_by(EmailSubscriber.subscribed_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin_subscribers.html', subscribers=subscribers)


@app.route('/admin/feedback')
@login_required
@admin_required
def admin_feedback():
    """Admin view for managing user feedback."""
    from models import UserFeedback
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    per_page = 20
    
    query = UserFeedback.query
    
    if status_filter != 'all':
        query = query.filter(UserFeedback.status == status_filter)
    if type_filter != 'all':
        query = query.filter(UserFeedback.feedback_type == type_filter)
    
    feedback_items = query.order_by(UserFeedback.submitted_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin_feedback.html', feedback_items=feedback_items, 
                         status_filter=status_filter, type_filter=type_filter)


@app.route('/admin/feedback/<int:feedback_id>/update', methods=['POST'])
@login_required
@admin_required
def update_feedback_status(feedback_id):
    """Update feedback status (admin only)."""
    from models import UserFeedback
    
    new_status = request.form.get('status')
    
    if new_status not in ['open', 'in_progress', 'resolved', 'closed']:
        return jsonify({'error': 'Invalid status'}), 400
    
    feedback_item = UserFeedback.query.get_or_404(feedback_id)
    feedback_item.status = new_status
    db.session.commit()
    
    return jsonify({'success': True, 'status': new_status})


# Team Management Routes
@app.route('/teams')
@login_required
def teams():
    """View teams that user is part of."""
    from models import Team, TeamMember
    
    user_teams = Team.query.join(TeamMember).filter(
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True,
        Team.is_active == True
    ).all()
    
    return render_template('teams.html', teams=user_teams)


@app.route('/teams/create', methods=['GET', 'POST'])
@login_required
def create_team():
    """Create a new team."""
    from models import Project
    
    if request.method == 'POST':
        from models import Team, TeamMember
        
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        project_id = request.form.get('project_id')
        
        if not name:
            flash('Team name is required', 'error')
            return render_template('create_team.html')
        
        if not project_id:
            flash('Project selection is required', 'error')
            return render_template('create_team.html')
        
        # Verify project ownership
        project = Project.query.filter_by(id=project_id, created_by=current_user.id).first()
        if not project:
            flash('Invalid project selected', 'error')
            return render_template('create_team.html')
        
        # Create team
        team = Team(
            name=name,
            description=description,
            created_by=current_user.id,
            project_id=project_id
        )
        db.session.add(team)
        db.session.flush()  # Get the ID
        
        # Add creator as admin
        team_member = TeamMember(
            team_id=team.id,
            user_id=current_user.id,
            role='admin'
        )
        db.session.add(team_member)
        db.session.commit()
        
        flash('Team created successfully!', 'success')
        return redirect(url_for('teams'))
    
    # Get user's projects for the form
    user_projects = Project.query.filter_by(created_by=current_user.id, is_active=True).all()
    return render_template('create_team.html', projects=user_projects)


@app.route('/teams/<int:team_id>')
@login_required
def team_detail(team_id):
    """View team details and members."""
    from models import Team, TeamMember, BugReport
    
    # Check if user is member of this team
    team_member = TeamMember.query.filter_by(
        team_id=team_id,
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not team_member:
        flash('You are not a member of this team', 'error')
        return redirect(url_for('teams'))
    
    team = Team.query.get_or_404(team_id)
    members = TeamMember.query.filter_by(team_id=team_id, is_active=True).all()
    
    # Populate member display data
    for member in members:
        member.user_name = f"{member.user.first_name} {member.user.last_name}"
        member.user_email = member.user.email
    
    # Get team's bug reports with assigned user names
    bug_reports = BugReport.query.filter_by(team_id=team_id).order_by(BugReport.created_at.desc()).limit(10).all()
    for bug in bug_reports:
        if bug.assigned_user:
            bug.assigned_user_name = f"{bug.assigned_user.first_name} {bug.assigned_user.last_name}"
    
    return render_template('team_detail.html', team=team, members=members, 
                         bug_reports=bug_reports, user_role=team_member.role)


@app.route('/teams/<int:team_id>/add-member', methods=['POST'])
@login_required
def add_team_member(team_id):
    """Add a member to the team."""
    from models import Team, TeamMember, User
    
    try:
        # Check if user is team admin or team creator
        team = Team.query.get_or_404(team_id)
        team_member = TeamMember.query.filter_by(
            team_id=team_id,
            user_id=current_user.id,
            role='admin',
            is_active=True
        ).first()
        
        # Also allow team creator
        if not team_member and team.created_by != current_user.id:
            return jsonify({'success': False, 'error': 'Only team admins can add members'}), 403
        
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'member')
        github_username = request.form.get('github_username', '').strip()
        
        if not email:
            return jsonify({'success': False, 'error': 'Email address is required'}), 400
            
        if role not in ['admin', 'member', 'viewer']:
            return jsonify({'success': False, 'error': 'Invalid role specified'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'error': f'User with email {email} not found. Please ensure the user has registered in the system.'}), 404
        
        # Check if already a member
        existing = TeamMember.query.filter_by(
            team_id=team_id,
            user_id=user.id
        ).first()
        
        if existing:
            if existing.is_active:
                return jsonify({'success': False, 'error': f'{user.first_name} {user.last_name} is already a member of this team'}), 400
            else:
                # Reactivate membership
                existing.is_active = True
                existing.role = role
                existing.github_username = github_username
                app.logger.info(f"Reactivated user {user.email} in team {team_id}")
        else:
            # Add new member
            new_member = TeamMember(
                team_id=team_id,
                user_id=user.id,
                role=role,
                github_username=github_username
            )
            db.session.add(new_member)
            app.logger.info(f"Added new user {user.email} to team {team_id}")
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Successfully added {user.first_name} {user.last_name} to the team',
            'user_name': f'{user.first_name} {user.last_name}',
            'role': role
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding team member: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to add member: {str(e)}'}), 500


@app.route('/add-team-members')
@login_required
def add_team_members_page():
    """Render the add team members interface."""
    from models import Team, TeamMember, Project
    from datetime import datetime, timedelta
    
    # Get teams where user is admin or creator
    user_teams = []
    team_memberships = TeamMember.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    
    for membership in team_memberships:
        team = membership.team
        if membership.role == 'admin' or team.created_by == current_user.id:
            # Add user role to team object for template
            team.user_role = membership.role
            team.members = TeamMember.query.filter_by(team_id=team.id, is_active=True).all()
            user_teams.append(team)
    
    # Calculate stats
    admin_teams_count = len(user_teams)
    total_members_count = sum(len(team.members) for team in user_teams)
    active_projects_count = len(set(team.project_id for team in user_teams))
    
    # Get recently added members (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_members = TeamMember.query.filter(
        TeamMember.team_id.in_([team.id for team in user_teams]),
        TeamMember.joined_at >= thirty_days_ago,
        TeamMember.is_active == True
    ).order_by(TeamMember.joined_at.desc()).limit(6).all()
    
    return render_template('add_team_members.html', 
                         user_teams=user_teams,
                         admin_teams_count=admin_teams_count,
                         total_members_count=total_members_count,
                         active_projects_count=active_projects_count,
                         recent_members=recent_members)


@app.route('/teams/<int:team_id>/register-and-add-member', methods=['POST'])
@login_required
def register_and_add_member(team_id):
    """Register a new user and add them to the team."""
    from models import Team, TeamMember, User
    from werkzeug.security import generate_password_hash
    
    try:
        # Check if user is team admin or team creator
        team = Team.query.get_or_404(team_id)
        team_member = TeamMember.query.filter_by(
            team_id=team_id,
            user_id=current_user.id,
            role='admin',
            is_active=True
        ).first()
        
        # Also allow team creator
        if not team_member and team.created_by != current_user.id:
            return jsonify({'success': False, 'error': 'Only team admins can add members'}), 403
        
        # Get form data
        email = request.form.get('new_email', '').strip().lower()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        temp_password = request.form.get('temp_password', '').strip()
        role = request.form.get('new_role', 'member')
        github_username = request.form.get('github_username', '').strip()
        
        # Validate input
        if not all([email, first_name, last_name, temp_password]):
            return jsonify({'success': False, 'error': 'All fields are required for new user registration'}), 400
        
        if len(temp_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters long'}), 400
            
        if role not in ['admin', 'member', 'viewer']:
            return jsonify({'success': False, 'error': 'Invalid role specified'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'error': f'User with email {email} already exists. Use "Add Existing User" instead.'}), 400
        
        # Create new user
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=generate_password_hash(temp_password)
        )
        db.session.add(new_user)
        db.session.flush()  # Get the user ID
        
        # Add user to team
        new_member = TeamMember(
            team_id=team_id,
            user_id=new_user.id,
            role=role,
            github_username=github_username
        )
        db.session.add(new_member)
        
        db.session.commit()
        
        app.logger.info(f"Registered new user {email} and added to team {team_id}")
        
        return jsonify({
            'success': True, 
            'message': f'Successfully registered {first_name} {last_name} and added to the team. They can now log in with their email and temporary password.',
            'user_name': f'{first_name} {last_name}',
            'role': role,
            'temporary_password': True
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error registering new user: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to register user: {str(e)}'}), 500


@app.route('/teams/<int:team_id>/assign-bug', methods=['POST'])
@login_required
def assign_bug_to_member(team_id):
    """Assign a bug to a team member."""
    from models import BugReport, TeamMember
    from datetime import datetime
    
    bug_id = request.form.get('bug_id')
    assigned_to = request.form.get('assigned_to')
    
    if not bug_id or not assigned_to:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user can assign bugs (team member)
    team_member = TeamMember.query.filter_by(
        team_id=team_id,
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not team_member:
        return jsonify({'error': 'You are not a member of this team'}), 403
    
    # Check if assignee is team member
    assignee = TeamMember.query.filter_by(
        team_id=team_id,
        user_id=assigned_to,
        is_active=True
    ).first()
    
    if not assignee:
        return jsonify({'error': 'Assignee is not a team member'}), 400
    
    # Update bug assignment
    bug_report = BugReport.query.get_or_404(bug_id)
    bug_report.assigned_to = assigned_to
    bug_report.team_id = team_id
    bug_report.assigned_at = datetime.utcnow()
    
    db.session.commit()
    
    # Try to assign in GitHub if exported
    if bug_report.exported_to_github and bug_report.github_issue_url and assignee.github_username:
        try:
            assign_github_issue(bug_report.github_issue_url, assignee.github_username)
        except Exception as e:
            logging.warning(f"Failed to assign GitHub issue: {e}")
    
    return jsonify({'success': True})


def assign_github_issue(github_issue_url, github_username):
    """Assign a GitHub issue to a user."""
    import requests
    import re
    
    # Extract owner, repo, and issue number from URL
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/issues/(\d+)', github_issue_url)
    if not match:
        raise ValueError("Invalid GitHub issue URL")
    
    owner, repo, issue_number = match.groups()
    
    # This would require GitHub token - placeholder for now
    # In production, you'd store GitHub tokens per user/team
    # and make API calls to assign issues
    logging.info(f"Would assign GitHub issue {owner}/{repo}#{issue_number} to {github_username}")
    
    # Example API call (requires proper token):
    # headers = {'Authorization': f'token {github_token}'}
    # data = {'assignees': [github_username]}
    # response = requests.patch(
    #     f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}',
    #     json=data, headers=headers
    # )


# API Routes for Team Data
@app.route('/api/user-teams')
@login_required
def api_user_teams():
    """Get teams that user is part of."""
    from models import Team, TeamMember
    
    user_teams = Team.query.join(TeamMember).filter(
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True,
        Team.is_active == True
    ).all()
    
    return jsonify([team.to_dict() for team in user_teams])


@app.route('/api/team-members/<int:team_id>')
@login_required
def api_team_members(team_id):
    """Get members of a specific team."""
    from models import TeamMember
    
    # Check if user is member of this team
    user_member = TeamMember.query.filter_by(
        team_id=team_id,
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not user_member:
        return jsonify({'error': 'Not authorized'}), 403
    
    members = TeamMember.query.filter_by(
        team_id=team_id,
        is_active=True
    ).all()
    
    return jsonify([member.to_dict() for member in members])


# Project Management Routes
@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for logged-in users."""
    return render_template('dashboard.html')

@app.route('/bug/<int:bug_id>')
@login_required
def bug_detail(bug_id):
    """View detailed bug report."""
    from models import BugReport
    bug = BugReport.query.get_or_404(bug_id)
    
    # Check permissions - allow viewing for now, will implement proper role check
    # if not current_user.can_view_bug(bug):
    #     flash('You do not have permission to view this bug report.', 'error')
    #     return redirect(url_for('dashboard'))
    
    return render_template('bug_detail.html', bug=bug)

@app.route('/history')
@login_required  
def history():
    """View user's bug report history."""
    return render_template('history.html')

@app.route('/api/user/reports')
@login_required
def api_user_reports():
    """Get current user's bug reports."""
    from models import BugReport
    
    try:
        reports = BugReport.query.filter_by(user_id=current_user.id).order_by(BugReport.created_at.desc()).all()
        return jsonify([report.to_dict() for report in reports])
    except Exception as e:
        app.logger.error(f"Error loading user reports: {str(e)}")
        return jsonify({'error': 'Failed to load reports'}), 500

@app.route('/projects')
@login_required
def projects():
    """View user's projects."""
    return render_template('projects.html')

@app.route('/projects/<int:project_id>')
@login_required
def project_analytics(project_id):
    """View project analytics dashboard."""
    from models import Project, BugReport, TeamMember
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    project = Project.query.filter_by(id=project_id, created_by=current_user.id).first()
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('projects'))
    
    # Calculate analytics
    total_bugs = len(project.bug_reports)
    resolved_bugs = len([b for b in project.bug_reports if b.status == 'resolved'])
    
    # Calculate average resolution time
    resolved_reports = [b for b in project.bug_reports if b.resolved_at and b.assigned_at]
    avg_resolution_hours = 0
    if resolved_reports:
        total_hours = sum([(b.resolved_at - b.assigned_at).total_seconds() / 3600 for b in resolved_reports])
        avg_resolution_hours = total_hours / len(resolved_reports)
    
    # Team performance metrics
    team_performance = []
    for team in project.teams:
        for member in team.members:
            if member.is_active:
                user_bugs = [b for b in project.bug_reports if b.assigned_to == member.user_id]
                resolved_user_bugs = [b for b in user_bugs if b.status == 'resolved']
                
                member_avg_resolution = 0
                if resolved_user_bugs:
                    member_resolved_with_times = [b for b in resolved_user_bugs if b.resolved_at and b.assigned_at]
                    if member_resolved_with_times:
                        total_member_hours = sum([(b.resolved_at - b.assigned_at).total_seconds() / 3600 for b in member_resolved_with_times])
                        member_avg_resolution = total_member_hours / len(member_resolved_with_times)
                
                success_rate = (len(resolved_user_bugs) / len(user_bugs) * 100) if user_bugs else 0
                
                team_performance.append({
                    'name': f"{member.user.first_name} {member.user.last_name}".strip(),
                    'assigned_count': len(user_bugs),
                    'resolved_count': len(resolved_user_bugs),
                    'avg_resolution_hours': member_avg_resolution,
                    'success_rate': success_rate
                })
    
    # Chart data for trends (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    chart_labels = []
    new_bugs_data = []
    resolved_bugs_data = []
    
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        chart_labels.append(date.strftime('%m/%d'))
        
        daily_new = len([b for b in project.bug_reports if b.created_at.date() == date.date()])
        daily_resolved = len([b for b in project.bug_reports if b.resolved_at and b.resolved_at.date() == date.date()])
        
        new_bugs_data.append(daily_new)
        resolved_bugs_data.append(daily_resolved)
    
    # Priority distribution
    priority_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for bug in project.bug_reports:
        priority_counts[bug.priority] += 1
    
    # Recent activity
    recent_activity = []
    for bug in sorted(project.bug_reports, key=lambda x: x.created_at, reverse=True)[:10]:
        if bug.status == 'resolved' and bug.resolved_at:
            recent_activity.append({
                'type': 'bug_resolved',
                'title': f'Bug Resolved: {bug.title}',
                'description': f'Resolved by {bug.assigned_user.first_name if bug.assigned_user else "Unknown"}',
                'timestamp': bug.resolved_at
            })
        elif bug.assigned_at:
            recent_activity.append({
                'type': 'bug_assigned', 
                'title': f'Bug Assigned: {bug.title}',
                'description': f'Assigned to {bug.assigned_user.first_name if bug.assigned_user else "Unknown"}',
                'timestamp': bug.assigned_at
            })
        else:
            recent_activity.append({
                'type': 'bug_created',
                'title': f'New Bug: {bug.title}',
                'description': f'Priority: {bug.priority.title()}',
                'timestamp': bug.created_at
            })
    
    analytics = {
        'total_bugs': total_bugs,
        'resolved_bugs': resolved_bugs,
        'avg_resolution_hours': avg_resolution_hours,
        'active_team_members': len(team_performance),
        'team_performance': team_performance,
        'recent_activity': sorted(recent_activity, key=lambda x: x['timestamp'], reverse=True)[:10],
        'chart_data': {
            'trends': {
                'labels': chart_labels,
                'new_bugs': new_bugs_data,
                'resolved_bugs': resolved_bugs_data
            },
            'priority': {
                'labels': ['Critical', 'High', 'Medium', 'Low'],
                'values': [priority_counts['critical'], priority_counts['high'], 
                          priority_counts['medium'], priority_counts['low']]
            }
        }
    }
    
    return render_template('project_analytics.html', project=project, analytics=analytics)

@app.route('/projects', methods=['POST'])
@login_required
def create_project():
    """Create a new project."""
    from models import Project
    
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        github_repo = request.form.get('github_repo', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Project name is required'}), 400
        
        project = Project(
            name=name,
            description=description,
            github_repo=github_repo,
            created_by=current_user.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({'success': True, 'project_id': project.id})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating project: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create project'}), 500

@app.route('/api/projects')
@login_required  
def api_projects():
    """Get user's projects."""
    from models import Project
    
    projects = Project.query.filter_by(created_by=current_user.id, is_active=True).all()
    return jsonify([project.to_dict() for project in projects])

@app.route('/api/project-teams/<int:project_id>')
@login_required
def api_project_teams(project_id):
    """Get teams for a specific project."""
    from models import Team
    
    teams = Team.query.filter_by(project_id=project_id, is_active=True).all()
    return jsonify([team.to_dict() for team in teams])


# GitHub OAuth Routes
@app.route('/login/github')
def github_login():
    """Redirect to GitHub OAuth."""
    if not GITHUB_CLIENT_ID:
        flash('GitHub OAuth not configured', 'error')
        return redirect(url_for('index'))
    
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={url_for('github_callback', _external=True)}"
        f"&scope=repo,user:email"
        f"&state={session.get('csrf_token', 'default')}"
    )
    return redirect(github_auth_url)


@app.route('/oauth/callback')
def github_callback():
    """Handle GitHub OAuth callback."""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        flash('GitHub authorization failed', 'error')
        return redirect(url_for('index'))
    
    # Exchange code for access token
    token_data = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code
    }
    
    headers = {'Accept': 'application/json'}
    response = requests.post('https://github.com/login/oauth/access_token', 
                           data=token_data, headers=headers)
    
    if response.status_code != 200:
        flash('Failed to get GitHub access token', 'error')
        return redirect(url_for('index'))
    
    token_info = response.json()
    access_token = token_info.get('access_token')
    
    if not access_token:
        flash('Invalid GitHub access token', 'error')
        return redirect(url_for('index'))
    
    # Get user info from GitHub
    github_headers = {'Authorization': f'token {access_token}'}
    user_response = requests.get('https://api.github.com/user', headers=github_headers)
    
    if user_response.status_code != 200:
        flash('Failed to get GitHub user info', 'error')
        return redirect(url_for('index'))
    
    github_user = user_response.json()
    
    # Update current user with GitHub info
    if current_user.is_authenticated:
        current_user.github_username = github_user['login']
        current_user.github_token = access_token
        current_user.github_connected_at = datetime.utcnow()
        db.session.commit()
        flash('GitHub account connected successfully!', 'success')
    else:
        # Store in session for after login
        session['github_token'] = access_token
        session['github_username'] = github_user['login']
        flash('GitHub connected. Please log in to link your account.', 'info')
    
    return redirect(url_for('index'))


@app.route('/github/disconnect', methods=['POST'])
@login_required
def github_disconnect():
    """Disconnect GitHub account."""
    current_user.github_username = None
    current_user.github_token = None
    current_user.github_connected_at = None
    db.session.commit()
    
    flash('GitHub account disconnected', 'info')
    return redirect(url_for('index'))


@app.route('/api/github/repos')
@login_required
def get_github_repos():
    """Get user's GitHub repositories."""
    if not current_user.github_token:
        return jsonify({'error': 'GitHub not connected'}), 401
    
    try:
        g = Github(current_user.github_token)
        user = g.get_user()
        repos = []
        
        for repo in user.get_repos(sort='updated', direction='desc'):
            if not repo.fork:  # Exclude forks
                repos.append({
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'private': repo.private
                })
                
                if len(repos) >= 20:  # Limit to recent 20 repos
                    break
        
        return jsonify(repos)
    except Exception as e:
        logging.error(f"GitHub API error: {e}")
        return jsonify({'error': 'Failed to fetch repositories'}), 500


@app.route('/api/github/collaborators/<path:repo_name>')
@login_required
def get_github_collaborators(repo_name):
    """Get collaborators for a GitHub repository."""
    if not current_user.github_token:
        return jsonify({'error': 'GitHub not connected'}), 401
    
    try:
        g = Github(current_user.github_token)
        repo = g.get_repo(repo_name)
        collaborators = []
        
        for collaborator in repo.get_collaborators():
            collaborators.append({
                'login': collaborator.login,
                'avatar_url': collaborator.avatar_url,
                'permissions': collaborator.permissions
            })
        
        return jsonify(collaborators)
    except Exception as e:
        logging.error(f"GitHub API error: {e}")
        return jsonify({'error': 'Failed to fetch collaborators'}), 500


def generate_ai_explanation(title, description, parsed_steps):
    """Generate AI explanation using ChatGPT."""
    try:
        prompt = f"""
        You are a technical expert helping to explain a bug report. Given the following bug information:
        
        Title: {title}
        Description: {description}
        Reproduction Steps: {parsed_steps}
        
        Please provide a clear, technical explanation that:
        1. Summarizes the core issue
        2. Explains the likely cause
        3. Suggests potential impact
        4. Recommends investigation approaches
        
        Keep it concise but informative for developers.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {"role": "system", "content": "You are a technical expert who provides clear, actionable bug analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return None

@app.route('/api/bugs/<int:bug_id>/assign', methods=['PUT'])
@login_required
def assign_bug(bug_id):
    """Assign bug to a user (admin or team lead only)."""
    from models import BugReport
    bug = BugReport.query.get_or_404(bug_id)
    
    if not current_user.can_assign_bugs():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.get_json()
    assignee_id = data.get('assignee_id')
    
    if assignee_id:
        assignee = User.query.get(assignee_id)
        if not assignee:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Team leads can only assign to their team members
        if current_user.role == 'team_lead' and not current_user.is_admin:
            team_ids = [membership.team_id for membership in current_user.team_memberships 
                       if membership.role in ['admin', 'team_lead']]
            assignee_team_ids = [membership.team_id for membership in assignee.team_memberships]
            
            if not any(team_id in team_ids for team_id in assignee_team_ids):
                return jsonify({'success': False, 'message': 'Can only assign to team members'}), 403
        
        bug.assigned_to = assignee_id
        bug.assigned_at = datetime.utcnow()
    else:
        bug.assigned_to = None
        bug.assigned_at = None
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Bug assignment updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error'}), 500

@app.route('/api/users/role/<int:user_id>', methods=['PUT'])
@login_required
def update_user_role(user_id):
    """Update user role (admin only)."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    from models import User
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    new_role = data.get('role')
    
    if new_role not in ['user', 'team_lead', 'admin']:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400
    
    user.role = new_role
    if new_role == 'admin':
        user.is_admin = True
    else:
        user.is_admin = False
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'User role updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error'}), 500

# Helper functions for templates
def get_status_badge(status):
    """Generate status badge HTML."""
    badges = {
        'open': {'class': 'bg-blue-100 text-blue-800 border-blue-200', 'emoji': '🔵', 'text': 'Open'},
        'in_progress': {'class': 'bg-yellow-100 text-yellow-800 border-yellow-200', 'emoji': '🟡', 'text': 'In Progress'},
        'resolved': {'class': 'bg-green-100 text-green-800 border-green-200', 'emoji': '🟢', 'text': 'Resolved'},
        'closed': {'class': 'bg-gray-100 text-gray-800 border-gray-200', 'emoji': '⚫', 'text': 'Closed'}
    }
    badge = badges.get(status, badges['open'])
    return f'<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border {badge["class"]}">{badge["emoji"]} {badge["text"]}</span>'

def get_priority_badge(priority):
    """Generate priority badge HTML."""
    badges = {
        'low': {'class': 'bg-green-100 text-green-800', 'emoji': '🟢', 'text': 'Low'},
        'medium': {'class': 'bg-yellow-100 text-yellow-800', 'emoji': '🟡', 'text': 'Medium'},
        'high': {'class': 'bg-orange-100 text-orange-800', 'emoji': '🟠', 'text': 'High'},
        'critical': {'class': 'bg-red-100 text-red-800', 'emoji': '🔴', 'text': 'Critical'}
    }
    badge = badges.get(priority, badges['medium'])
    return f'<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium {badge["class"]}">{badge["emoji"]} {badge["text"]}</span>'

def get_confidence_class(confidence):
    """Get CSS class for confidence level."""
    classes = {
        'high': 'bg-green-100 text-green-800',
        'medium': 'bg-yellow-100 text-yellow-800',
        'low': 'bg-red-100 text-red-800'
    }
    return classes.get(confidence, classes['medium'])

# Register template functions
app.jinja_env.globals.update(
    get_status_badge=get_status_badge,
    get_priority_badge=get_priority_badge,
    get_confidence_class=get_confidence_class
)


@app.route('/api/bugs/<int:bug_id>/status', methods=['PUT'])
@login_required
def update_bug_status(bug_id):
    """Update bug status (admin, team lead, or bug owner)."""
    from models import BugReport
    bug = BugReport.query.get_or_404(bug_id)
    
    # Check permissions using role-based system
    if not current_user.can_edit_bug(bug):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['open', 'in_progress', 'resolved', 'closed']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    
    bug.status = new_status
    if new_status == 'resolved':
        bug.resolved_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Status updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error'}), 500

@app.route('/api/bugs/<int:bug_id>', methods=['DELETE'])
@login_required
def delete_bug_api(bug_id):
    """Delete bug report (admin only)."""
    bug = BugReport.query.get_or_404(bug_id)
    
    if not current_user.can_delete_bug(bug):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        db.session.delete(bug)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Bug report deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error'}), 500

def create_github_issue_with_assignment(bug_report):
    """Create GitHub issue with assignees and enhanced content."""
    if not bug_report.github_repo or not current_user.github_token:
        return None
    
    try:
        g = Github(current_user.github_token)
        repo = g.get_repo(bug_report.github_repo)
        
        # Build issue body with AI explanation
        body_parts = [
            "## Bug Description",
            bug_report.description,
            "",
            "## Reproduction Steps",
            bug_report.parsed_steps or "Not available",
        ]
        
        if bug_report.ai_explanation:
            body_parts.extend([
                "",
                "## AI Analysis",
                bug_report.ai_explanation
            ])
        
        body_parts.extend([
            "",
            f"**Priority:** {bug_report.priority.title()}",
            f"**Reported by:** {current_user.github_username or current_user.email}",
            "",
            f"*Created via Bug Reporting System*"
        ])
        
        body = "\n".join(body_parts)
        
        # Create issue
        issue = repo.create_issue(
            title=bug_report.title,
            body=body,
            labels=[f"priority:{bug_report.priority}", "bug"]
        )
        
        # Assign to team member if specified
        if bug_report.assigned_user and bug_report.assigned_user.github_username:
            try:
                issue.edit(assignees=[bug_report.assigned_user.github_username])
            except Exception as e:
                logging.warning(f"Failed to assign GitHub issue: {e}")
        
        # Update bug report with GitHub URL
        bug_report.github_issue_url = issue.html_url
        bug_report.exported_to_github = True
        db.session.commit()
        
        return issue.html_url
    except Exception as e:
        logging.error(f"GitHub issue creation error: {e}")
        return None


with app.app_context():
    # Import models to ensure they're registered
    import models  # noqa: F401
    
    # Create all tables
    db.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
