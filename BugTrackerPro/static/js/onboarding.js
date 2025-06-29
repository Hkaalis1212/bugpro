/**
 * Onboarding Tutorial System
 * Provides step-by-step guidance for first-time users
 */

class OnboardingTutorial {
    constructor() {
        this.currentStep = 0;
        this.steps = [];
        this.overlay = null;
        this.tooltip = null;
        this.isActive = false;
        this.storageKey = 'bugReportingOnboardingCompleted';
        
        this.initializeSteps();
        this.createOverlay();
        this.createTooltip();
    }

    initializeSteps() {
        // Define tutorial steps based on current page
        const currentPath = window.location.pathname;
        
        if (currentPath === '/' || currentPath === '/index') {
            this.steps = [
                {
                    target: '.display-4',
                    title: 'Welcome to Bug Reporting!',
                    content: 'This is your AI-powered bug reporting system. Let me show you how to effectively report bugs and get automatic reproduction steps.',
                    position: 'bottom'
                },
                {
                    target: '#title',
                    title: 'Bug Title',
                    content: 'Start by giving your bug report a clear, descriptive title. This helps our team understand the issue quickly.',
                    position: 'bottom'
                },
                {
                    target: '#description',
                    title: 'Describe the Bug',
                    content: 'Provide detailed information about what went wrong. Our AI will automatically extract step-by-step reproduction instructions from your description.',
                    position: 'bottom'
                },
                {
                    target: '#drop-area',
                    title: 'Add Files (Optional)',
                    content: 'Drag and drop screenshots, error logs, or other files here. Visual evidence helps us understand and fix bugs faster.',
                    position: 'top'
                },
                {
                    target: 'button[type="submit"]',
                    title: 'Submit Your Report',
                    content: 'Click here to submit your bug report. Our AI will process it and generate reproduction steps automatically.',
                    position: 'top'
                },
                {
                    target: '.btn-outline-success, .btn-outline-info',
                    title: 'Account Features',
                    content: 'Create an account to track your bug reports and access additional features. Admins can manage all reports from the dashboard.',
                    position: 'bottom'
                }
            ];
        } else if (currentPath === '/admin') {
            this.steps = [
                {
                    target: '.display-5',
                    title: 'Admin Dashboard',
                    content: 'Welcome to the admin dashboard! Here you can manage all bug reports, view statistics, and perform administrative tasks.',
                    position: 'bottom'
                },
                {
                    target: '.row.mb-4:nth-child(2)',
                    title: 'Dashboard Statistics',
                    content: 'View key statistics about bug reports, including total reports and recent activity.',
                    position: 'bottom'
                },
                {
                    target: '#searchInput',
                    title: 'Search Reports',
                    content: 'Use the search box to quickly find specific bug reports by title or description.',
                    position: 'bottom'
                },
                {
                    target: '.table-responsive',
                    title: 'Manage Reports',
                    content: 'View all bug reports in this table. You can select multiple reports for bulk actions or click individual reports for details.',
                    position: 'top'
                },
                {
                    target: '#deleteSelectedBtn',
                    title: 'Bulk Actions',
                    content: 'Select multiple reports and use this button to delete them in bulk. Be careful - this action cannot be undone!',
                    position: 'top'
                }
            ];
        }
    }

    createOverlay() {
        this.overlay = document.createElement('div');
        this.overlay.className = 'onboarding-overlay';
        this.overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 9998;
            display: none;
        `;
        document.body.appendChild(this.overlay);
    }

    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'onboarding-tooltip';
        this.tooltip.style.cssText = `
            position: absolute;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            z-index: 9999;
            max-width: 300px;
            display: none;
            color: #333;
            font-family: system-ui, -apple-system, sans-serif;
        `;
        
        this.tooltip.innerHTML = `
            <div class="tooltip-header">
                <h4 class="tooltip-title" style="margin: 0 0 10px 0; color: #333; font-size: 16px; font-weight: 600;"></h4>
                <button class="tooltip-close" style="position: absolute; top: 10px; right: 10px; background: none; border: none; font-size: 18px; cursor: pointer; color: #666;">&times;</button>
            </div>
            <div class="tooltip-content" style="margin-bottom: 15px; line-height: 1.4; color: #555;"></div>
            <div class="tooltip-actions" style="display: flex; justify-content: space-between; align-items: center;">
                <div class="step-indicator" style="font-size: 12px; color: #888;"></div>
                <div class="tooltip-buttons">
                    <button class="btn-skip" style="background: none; border: 1px solid #ddd; padding: 6px 12px; border-radius: 4px; margin-right: 8px; cursor: pointer; font-size: 12px;">Skip</button>
                    <button class="btn-next" style="background: #007bff; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">Next</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.tooltip);
        
        // Bind events
        this.tooltip.querySelector('.tooltip-close').addEventListener('click', () => this.end());
        this.tooltip.querySelector('.btn-skip').addEventListener('click', () => this.end());
        this.tooltip.querySelector('.btn-next').addEventListener('click', () => this.nextStep());
    }

    shouldShowOnboarding() {
        // Check if user has completed onboarding
        if (localStorage.getItem(this.storageKey) === 'true') {
            return false;
        }
        
        // Check if there are steps for current page
        return this.steps.length > 0;
    }

    start() {
        if (!this.shouldShowOnboarding()) {
            return;
        }
        
        this.isActive = true;
        this.currentStep = 0;
        this.overlay.style.display = 'block';
        this.showStep(0);
        
        // Add escape key listener
        document.addEventListener('keydown', this.handleKeyPress.bind(this));
    }

    showStep(stepIndex) {
        if (stepIndex >= this.steps.length) {
            this.end();
            return;
        }
        
        const step = this.steps[stepIndex];
        const target = document.querySelector(step.target);
        
        if (!target) {
            console.warn(`Onboarding target not found: ${step.target}`);
            this.nextStep();
            return;
        }
        
        // Highlight target element
        this.highlightElement(target);
        
        // Position and show tooltip
        this.positionTooltip(target, step);
        this.updateTooltipContent(step, stepIndex);
        this.tooltip.style.display = 'block';
    }

    highlightElement(element) {
        // Remove previous highlights
        document.querySelectorAll('.onboarding-highlight').forEach(el => {
            el.classList.remove('onboarding-highlight');
        });
        
        // Add highlight to current element
        element.classList.add('onboarding-highlight');
        
        // Add CSS for highlight if not exists
        if (!document.querySelector('#onboarding-styles')) {
            const style = document.createElement('style');
            style.id = 'onboarding-styles';
            style.textContent = `
                .onboarding-highlight {
                    position: relative;
                    z-index: 9997;
                    box-shadow: 0 0 0 4px rgba(0, 123, 255, 0.5) !important;
                    border-radius: 4px;
                }
                
                .onboarding-overlay {
                    pointer-events: none;
                }
                
                .onboarding-tooltip {
                    pointer-events: auto;
                }
                
                .onboarding-highlight {
                    pointer-events: auto;
                }
            `;
            document.head.appendChild(style);
        }
        
        // Scroll element into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    positionTooltip(target, step) {
        const rect = target.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();
        
        let top, left;
        
        switch (step.position) {
            case 'top':
                top = rect.top - tooltipRect.height - 10;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'bottom':
                top = rect.bottom + 10;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'left':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.left - tooltipRect.width - 10;
                break;
            case 'right':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.right + 10;
                break;
            default:
                top = rect.bottom + 10;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
        }
        
        // Ensure tooltip stays within viewport
        const padding = 10;
        top = Math.max(padding, Math.min(window.innerHeight - tooltipRect.height - padding, top));
        left = Math.max(padding, Math.min(window.innerWidth - tooltipRect.width - padding, left));
        
        this.tooltip.style.top = top + 'px';
        this.tooltip.style.left = left + 'px';
    }

    updateTooltipContent(step, stepIndex) {
        this.tooltip.querySelector('.tooltip-title').textContent = step.title;
        this.tooltip.querySelector('.tooltip-content').textContent = step.content;
        this.tooltip.querySelector('.step-indicator').textContent = `Step ${stepIndex + 1} of ${this.steps.length}`;
        
        // Update button text for last step
        const nextBtn = this.tooltip.querySelector('.btn-next');
        nextBtn.textContent = stepIndex === this.steps.length - 1 ? 'Finish' : 'Next';
    }

    nextStep() {
        this.currentStep++;
        this.showStep(this.currentStep);
    }

    end() {
        this.isActive = false;
        this.overlay.style.display = 'none';
        this.tooltip.style.display = 'none';
        
        // Remove highlights
        document.querySelectorAll('.onboarding-highlight').forEach(el => {
            el.classList.remove('onboarding-highlight');
        });
        
        // Mark onboarding as completed
        localStorage.setItem(this.storageKey, 'true');
        
        // Remove event listeners
        document.removeEventListener('keydown', this.handleKeyPress.bind(this));
    }

    handleKeyPress(event) {
        if (!this.isActive) return;
        
        if (event.key === 'Escape') {
            this.end();
        } else if (event.key === 'ArrowRight' || event.key === 'Enter') {
            this.nextStep();
        }
    }

    reset() {
        localStorage.removeItem(this.storageKey);
    }
}

// Initialize onboarding when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.onboardingTutorial = new OnboardingTutorial();
    
    // Auto-start onboarding after a short delay
    setTimeout(() => {
        window.onboardingTutorial.start();
    }, 1000);
});

// Add manual trigger function
window.startOnboarding = function() {
    if (window.onboardingTutorial) {
        window.onboardingTutorial.reset();
        window.onboardingTutorial.start();
    }
};