import os
import stripe
from flask import current_app
from models import User, db
from datetime import datetime, timedelta

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Stripe Price IDs (you'll need to create these in your Stripe dashboard)
STRIPE_PRICES = {
    'standard': 'price_standard_monthly',  # Replace with actual price ID
    'premium': 'price_premium_monthly'     # Replace with actual price ID
}

def get_domain():
    """Get the current domain for redirect URLs"""
    if os.environ.get('REPLIT_DEPLOYMENT'):
        return f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}"
    else:
        domains = os.environ.get('REPLIT_DOMAINS')
        if domains:
            return f"https://{domains.split(',')[0]}"
    return "http://localhost:5000"

def create_stripe_customer(user):
    """Create a Stripe customer for the user"""
    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
            metadata={
                'user_id': user.id
            }
        )
        
        user.stripe_customer_id = customer.id
        db.session.commit()
        
        return customer
    except Exception as e:
        current_app.logger.error(f"Error creating Stripe customer: {e}")
        return None

def create_checkout_session(user, plan):
    """Create a Stripe checkout session for subscription"""
    try:
        # Ensure user has a Stripe customer ID
        if not user.stripe_customer_id:
            customer = create_stripe_customer(user)
            if not customer:
                return None
        
        domain = get_domain()
        
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            line_items=[
                {
                    'price': STRIPE_PRICES[plan],
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f'{domain}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{domain}/subscription/cancelled',
            metadata={
                'user_id': user.id,
                'plan': plan
            }
        )
        
        return checkout_session
    except Exception as e:
        current_app.logger.error(f"Error creating checkout session: {e}")
        return None

def handle_successful_payment(session_id):
    """Handle successful payment and update user subscription"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            user_id = session.metadata.get('user_id')
            plan = session.metadata.get('plan')
            
            user = User.query.get(user_id)
            if user:
                # Get the subscription
                subscription = stripe.Subscription.retrieve(session.subscription)
                
                user.subscription_plan = plan
                user.stripe_subscription_id = subscription.id
                user.subscription_status = 'active'
                user.subscription_end_date = datetime.fromtimestamp(
                    subscription.current_period_end
                )
                
                db.session.commit()
                return True
                
    except Exception as e:
        current_app.logger.error(f"Error handling successful payment: {e}")
    
    return False

def cancel_subscription(user):
    """Cancel user's subscription"""
    try:
        if user.stripe_subscription_id:
            stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            user.subscription_status = 'cancelled'
            db.session.commit()
            return True
            
    except Exception as e:
        current_app.logger.error(f"Error cancelling subscription: {e}")
    
    return False

def reactivate_subscription(user):
    """Reactivate a cancelled subscription"""
    try:
        if user.stripe_subscription_id:
            stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            user.subscription_status = 'active'
            db.session.commit()
            return True
            
    except Exception as e:
        current_app.logger.error(f"Error reactivating subscription: {e}")
    
    return False

def get_billing_portal_url(user):
    """Create a billing portal session for the user"""
    try:
        if not user.stripe_customer_id:
            return None
            
        domain = get_domain()
        
        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f'{domain}/subscription/manage'
        )
        
        return portal_session.url
        
    except Exception as e:
        current_app.logger.error(f"Error creating billing portal: {e}")
        return None

def handle_webhook(payload, signature):
    """Handle Stripe webhooks"""
    try:
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload, signature, endpoint_secret
            )
        else:
            event = stripe.Event.construct_from(
                payload, stripe.api_key
            )
        
        # Handle different event types
        if event['type'] == 'invoice.payment_succeeded':
            handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            handle_payment_failed(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_deleted(event['data']['object'])
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Webhook error: {e}")
        return False

def handle_payment_succeeded(invoice):
    """Handle successful subscription payment"""
    try:
        subscription_id = invoice['subscription']
        customer_id = invoice['customer']
        
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.subscription_status = 'active'
            user.subscription_end_date = datetime.fromtimestamp(
                invoice['period_end']
            )
            db.session.commit()
            
    except Exception as e:
        current_app.logger.error(f"Error handling payment success: {e}")

def handle_payment_failed(invoice):
    """Handle failed subscription payment"""
    try:
        customer_id = invoice['customer']
        
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.subscription_status = 'past_due'
            db.session.commit()
            
    except Exception as e:
        current_app.logger.error(f"Error handling payment failure: {e}")

def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    try:
        customer_id = subscription['customer']
        
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.subscription_plan = 'freemium'
            user.subscription_status = 'cancelled'
            user.stripe_subscription_id = None
            db.session.commit()
            
    except Exception as e:
        current_app.logger.error(f"Error handling subscription deletion: {e}")