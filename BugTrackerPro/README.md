# AI-Powered Bug Reporting System

A comprehensive bug reporting system that uses AI to analyze and categorize bug reports, with integrated payment processing, team collaboration, and GitHub integration.

## Features

- **AI-Powered Analysis**: Automatic extraction of reproduction steps using OpenAI
- **User Authentication**: Secure login/registration with role-based access control
- **Team Collaboration**: Create teams, assign bugs, and manage projects
- **GitHub Integration**: Connect GitHub accounts and export bugs as issues
- **Payment Processing**: Stripe integration for subscription management
- **File Uploads**: Drag-and-drop file attachments for bug reports
- **Admin Dashboard**: Comprehensive management interface
- **Reproducibility Scoring**: AI-powered bug quality assessment

## Tech Stack

- **Backend**: Flask (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: HTML5, TailwindCSS, Vanilla JavaScript
- **AI**: OpenAI GPT for bug analysis
- **Payments**: Stripe for subscription management
- **Authentication**: Flask-Login with GitHub OAuth
- **Testing**: Comprehensive test suite with Playwright

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- OpenAI API key
- Stripe account (for payments)
- GitHub OAuth app (for GitHub integration)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bug-reporting-system.git
   cd bug-reporting-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file with:
   ```
   DATABASE_URL=postgresql://username:password@localhost/bugtracker
   SESSION_SECRET=your-secret-key-here
   OPENAI_API_KEY=your-openai-api-key
   STRIPE_SECRET_KEY=your-stripe-secret-key
   STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret
   ```

4. **Initialize the database**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Run the application**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

Visit `http://localhost:5000` to access the application.

## Configuration

### GitHub Integration Setup

1. Go to GitHub → Settings → Developer settings → OAuth Apps
2. Create a new OAuth App with:
   - Application name: "Bug Reporting System"
   - Homepage URL: Your deployment URL
   - Authorization callback URL: `your-domain/oauth/callback`
3. Add the Client ID and Secret to your environment variables

### Stripe Setup

1. Create a Stripe account
2. Get your API keys from the Stripe dashboard
3. Add them to your environment variables
4. Configure webhook endpoints for subscription management

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `POST /logout` - User logout

### Bug Reports
- `POST /submit` - Submit new bug report
- `GET /api/reports` - Get all reports (admin)
- `GET /bug/<id>` - View specific bug report
- `DELETE /api/bug/<id>` - Delete bug report (admin)

### GitHub Integration
- `GET /login/github` - GitHub OAuth login
- `GET /oauth/callback` - GitHub OAuth callback
- `GET /api/github/repos` - Get user repositories
- `POST /api/export/github/<bug_id>` - Export bug to GitHub

### External API (for chatbots)
- `GET /api/health` - Health check
- `POST /api/submit` - Submit bug via API

## Testing

Run the comprehensive test suite:

```bash
python comprehensive_tests.py
```

For integration testing:
```bash
python integration_test.py
```

## Deployment

### Replit Deployment
1. Import the project to Replit
2. Set environment variables in Secrets
3. Run the application

### Traditional Hosting
1. Set up a PostgreSQL database
2. Configure environment variables
3. Use gunicorn as the WSGI server
4. Set up a reverse proxy (nginx recommended)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on GitHub or contact the development team.

## Architecture

The system follows a modular Flask architecture with:
- **Models**: Database models using SQLAlchemy
- **Routes**: RESTful API endpoints
- **Templates**: Jinja2 templates with TailwindCSS
- **Static Files**: JavaScript, CSS, and assets
- **Tests**: Comprehensive test coverage

## Security

- Password hashing with Werkzeug
- CSRF protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Secure file uploads