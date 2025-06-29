# Deployment Guide

This guide covers different ways to deploy the AI Bug Reporting System.

## Quick Deploy Options

### Deploy to Heroku
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Deploy to Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

### Deploy to Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## Manual Deployment

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Environment variables configured

### Environment Variables Required

```bash
DATABASE_URL=postgresql://user:password@host:5432/database
SESSION_SECRET=your-secret-key
OPENAI_API_KEY=your-openai-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bug-reporting-system.git
cd bug-reporting-system
```

2. Install dependencies:
```bash
pip install -r requirements_for_github.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your values
```

4. Initialize database:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. Run the application:
```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

### Production Deployment

#### Heroku Deployment

1. Create a Heroku app:
```bash
heroku create your-app-name
```

2. Add PostgreSQL addon:
```bash
heroku addons:create heroku-postgresql:mini
```

3. Set environment variables:
```bash
heroku config:set SESSION_SECRET=your-secret-key
heroku config:set OPENAI_API_KEY=your-openai-key
heroku config:set STRIPE_SECRET_KEY=your-stripe-key
heroku config:set GITHUB_CLIENT_ID=your-github-id
heroku config:set GITHUB_CLIENT_SECRET=your-github-secret
```

4. Deploy:
```bash
git push heroku main
```

#### VPS/Server Deployment

1. Install dependencies:
```bash
sudo apt update
sudo apt install python3.11 python3-pip postgresql nginx
```

2. Create application user:
```bash
sudo useradd -m -s /bin/bash bugtracker
sudo su - bugtracker
```

3. Clone and setup:
```bash
git clone https://github.com/yourusername/bug-reporting-system.git
cd bug-reporting-system
pip install -r requirements_for_github.txt
```

4. Configure nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

5. Create systemd service:
```ini
[Unit]
Description=Bug Reporting System
After=network.target

[Service]
User=bugtracker
WorkingDirectory=/home/bugtracker/bug-reporting-system
Environment=PATH=/home/bugtracker/bug-reporting-system/venv/bin
ExecStart=/home/bugtracker/bug-reporting-system/venv/bin/gunicorn --bind 127.0.0.1:5000 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## Database Setup

### PostgreSQL Setup

1. Create database and user:
```sql
CREATE DATABASE bugtracker;
CREATE USER bugtracker WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE bugtracker TO bugtracker;
```

2. Update DATABASE_URL:
```bash
DATABASE_URL=postgresql://bugtracker:secure_password@localhost/bugtracker
```

## External Services Setup

### OpenAI API
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add to environment variables

### Stripe Setup
1. Create Stripe account
2. Get API keys from dashboard
3. Set up webhook endpoints for subscription management
4. Add keys to environment variables

### GitHub OAuth
1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create new OAuth App:
   - Application name: "Bug Reporting System"
   - Homepage URL: Your deployment URL
   - Authorization callback URL: `your-domain.com/oauth/callback`
3. Add Client ID and Secret to environment variables

## Health Checks

The application provides several health check endpoints:

- `GET /ping` - Basic health check
- `GET /api/health` - API health check
- Database connectivity is verified automatically

## Monitoring

Consider setting up monitoring for:
- Application uptime
- Database performance
- API response times
- Error rates
- Subscription webhook processing

## Backup Strategy

Regular backups should include:
- PostgreSQL database
- Uploaded files in `attached_assets/`
- Environment variables (securely)

## Security Considerations

- Use HTTPS in production
- Set strong SESSION_SECRET
- Keep API keys secure
- Regular security updates
- Monitor for suspicious activity
- Implement rate limiting if needed

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Verify PostgreSQL is running
   - Check firewall settings

2. **Static Files Not Loading**
   - Ensure static file serving is configured
   - Check file permissions

3. **GitHub OAuth Issues**
   - Verify callback URL matches exactly
   - Check client ID and secret

4. **Stripe Webhooks Failing**
   - Verify webhook endpoint URL
   - Check webhook secret

### Logs

Check application logs for errors:
```bash
heroku logs --tail  # For Heroku
journalctl -u bugtracker -f  # For systemd
```