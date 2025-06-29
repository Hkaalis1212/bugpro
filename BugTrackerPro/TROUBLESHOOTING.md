# GitHub Repository Troubleshooting Guide

## Common Issues and Solutions

### 1. Repository Won't Load/Clone

**Problem**: Cannot access or clone the repository
**Solutions**:
- Check repository URL is correct
- Verify repository is public or you have access
- Try HTTPS instead of SSH: `git clone https://github.com/username/repo.git`

### 2. Missing Dependencies File

**Problem**: `pip install -r requirements.txt` fails
**Solution**: Use the provided requirements file:
```bash
pip install -r requirements_for_github.txt
```

### 3. Environment Variables Missing

**Problem**: Application crashes with missing environment variables
**Solution**: Copy and configure environment file:
```bash
cp .env.example .env
# Edit .env with your actual values
```

Required variables:
```
DATABASE_URL=postgresql://user:pass@host:5432/db
SESSION_SECRET=your-secret-key
OPENAI_API_KEY=your-openai-key
STRIPE_SECRET_KEY=your-stripe-key
GITHUB_CLIENT_ID=your-github-id
GITHUB_CLIENT_SECRET=your-github-secret
```

### 4. Database Connection Issues

**Problem**: Database connection fails
**Solutions**:
- Install PostgreSQL locally
- Use cloud database (Heroku Postgres, Railway, etc.)
- Check DATABASE_URL format

### 5. Import Errors

**Problem**: Python import errors when running
**Solutions**:
- Ensure Python 3.11+ is installed
- Install all dependencies: `pip install -r requirements_for_github.txt`
- Check for missing model imports

### 6. Static Files Not Loading

**Problem**: CSS/JS files not found
**Solution**: Verify static folder structure exists

## Quick Start Commands

1. **Clone repository**:
```bash
git clone https://github.com/yourusername/bug-reporting-system.git
cd bug-reporting-system
```

2. **Setup environment**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements_for_github.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your values
```

4. **Initialize database**:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. **Run application**:
```bash
python main.py
```

## Deployment Issues

### Heroku Deployment

**Problem**: Heroku build fails
**Solutions**:
- Add `Procfile` with: `web: gunicorn --bind 0.0.0.0:$PORT main:app`
- Add `runtime.txt` with: `python-3.11.7`
- Use `requirements_for_github.txt` as `requirements.txt`

### Railway/Render Deployment

**Problem**: Build or runtime errors
**Solutions**:
- Set Python version in settings
- Configure environment variables in dashboard
- Set start command: `gunicorn --bind 0.0.0.0:$PORT main:app`

## Service-Specific Setup

### OpenAI API
If AI features aren't working:
1. Get API key from https://platform.openai.com/api-keys
2. Add to environment: `OPENAI_API_KEY=sk-...`

### Stripe Integration
If payments aren't working:
1. Get keys from Stripe dashboard
2. Add both keys to environment
3. Configure webhook endpoints

### GitHub OAuth
If GitHub login fails:
1. Create OAuth app in GitHub settings
2. Set callback URL: `your-domain.com/oauth/callback`
3. Add client ID and secret to environment

## Testing the Setup

Run these commands to verify everything works:

```bash
# Test database connection
python -c "from app import app, db; app.app_context().push(); print('Database OK')"

# Test basic app loading
python -c "from app import app; print('App imports OK')"

# Run the application
python main.py
```

## Need More Help?

If you're still having issues:
1. Check the error messages carefully
2. Verify all environment variables are set
3. Ensure PostgreSQL is running (locally or cloud)
4. Make sure you're using Python 3.11+
5. Try the deployment guide in DEPLOYMENT.md