/**
 * Payment Flow Utilities
 * Handles real-time payment status updates and visualization
 */

class PaymentStatusTracker {
    constructor() {
        this.pollInterval = null;
        this.checkInterval = 2000; // Check every 2 seconds
        this.maxAttempts = 30; // Max 1 minute of polling
        this.attempts = 0;
    }

    // Start polling for payment status
    startTracking(sessionId) {
        this.sessionId = sessionId;
        this.attempts = 0;
        
        this.pollInterval = setInterval(() => {
            this.checkPaymentStatus();
        }, this.checkInterval);
    }

    // Check payment status with backend
    async checkPaymentStatus() {
        this.attempts++;
        
        if (this.attempts > this.maxAttempts) {
            this.stopTracking();
            this.showTimeout();
            return;
        }

        try {
            const response = await fetch(`/api/payment-status/${this.sessionId}`);
            const data = await response.json();
            
            if (data.status === 'complete') {
                this.stopTracking();
                this.onPaymentSuccess(data);
            } else if (data.status === 'failed') {
                this.stopTracking();
                this.onPaymentFailure(data);
            }
            // Continue polling for pending status
            
        } catch (error) {
            console.error('Error checking payment status:', error);
        }
    }

    stopTracking() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    onPaymentSuccess(data) {
        // Update UI to show success
        this.updateFlowStep(4, 'success');
        this.showSuccessMessage(data);
        
        // Redirect to dashboard after 3 seconds
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 3000);
    }

    onPaymentFailure(data) {
        // Update UI to show failure
        this.updateFlowStep(2, 'error');
        this.showErrorMessage(data.error || 'Payment failed');
    }

    showTimeout() {
        this.showErrorMessage('Payment verification timed out. Please check your account or contact support.');
    }

    updateFlowStep(stepNumber, status) {
        const event = new CustomEvent('paymentStatusUpdate', {
            detail: { step: stepNumber, status: status }
        });
        window.dispatchEvent(event);
    }

    showSuccessMessage(data) {
        const notification = this.createNotification(
            'Payment Successful!',
            `Your ${data.plan} subscription has been activated.`,
            'success'
        );
        document.body.appendChild(notification);
    }

    showErrorMessage(message) {
        const notification = this.createNotification(
            'Payment Error',
            message,
            'error'
        );
        document.body.appendChild(notification);
    }

    createNotification(title, message, type) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${
            type === 'success' ? 'bg-green-600' : 'bg-red-600'
        } text-white`;
        
        notification.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} text-xl"></i>
                </div>
                <div class="ml-3">
                    <h4 class="font-semibold">${title}</h4>
                    <p class="text-sm mt-1">${message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-auto">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
        
        return notification;
    }
}

// Stripe integration utilities
class StripeIntegration {
    static openCheckout(plan) {
        // Create a popup window for Stripe checkout
        const popup = window.open('', 'stripe-checkout', 'width=600,height=700');
        
        // Create form and submit to checkout endpoint
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/subscription/create-checkout';
        form.target = 'stripe-checkout';
        
        const planInput = document.createElement('input');
        planInput.type = 'hidden';
        planInput.name = 'plan';
        planInput.value = plan;
        
        form.appendChild(planInput);
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
        
        // Monitor popup for completion
        const checkClosed = setInterval(() => {
            if (popup.closed) {
                clearInterval(checkClosed);
                // Check if payment was successful
                this.checkPaymentCompletion();
            }
        }, 1000);
        
        return popup;
    }
    
    static async checkPaymentCompletion() {
        // Check with backend if payment was completed
        try {
            const response = await fetch('/api/subscription/status');
            const data = await response.json();
            
            if (data.status === 'active') {
                // Payment was successful
                window.dispatchEvent(new CustomEvent('paymentSuccess', {
                    detail: data
                }));
            }
        } catch (error) {
            console.error('Error checking payment completion:', error);
        }
    }
}

// Payment flow animations
class PaymentAnimations {
    static animateStepTransition(fromStep, toStep) {
        const fromElement = document.getElementById(`step${fromStep}`);
        const toElement = document.getElementById(`step${toStep}`);
        
        if (fromElement) {
            fromElement.style.transform = 'scale(0.95)';
            fromElement.style.opacity = '0.7';
        }
        
        if (toElement) {
            setTimeout(() => {
                toElement.style.transform = 'scale(1.05)';
                toElement.style.opacity = '1';
            }, 200);
        }
    }
    
    static showLoadingSpinner(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            const spinner = document.createElement('div');
            spinner.className = 'inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2';
            element.prepend(spinner);
        }
    }
    
    static hideLoadingSpinner(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            const spinner = element.querySelector('.animate-spin');
            if (spinner) {
                spinner.remove();
            }
        }
    }
}

// Export for global use
window.PaymentStatusTracker = PaymentStatusTracker;
window.StripeIntegration = StripeIntegration;
window.PaymentAnimations = PaymentAnimations;