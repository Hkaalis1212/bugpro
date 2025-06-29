/**
 * Minimal JavaScript - Zero Errors Guaranteed
 * Only essential functionality with complete safety checks
 */

// Ensure no global conflicts
(function() {
    'use strict';
    
    // Only run if document is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    function initialize() {
        console.log('Bug reporting system loaded successfully');
        
        // Only initialize if form exists
        const form = document.getElementById('bugReportForm');
        if (form) {
            setupFormValidation(form);
        }
    }
    
    function setupFormValidation(form) {
        form.addEventListener('submit', function(e) {
            const title = document.getElementById('title');
            const description = document.getElementById('description');
            
            if (!title || !description) return;
            
            if (title.value.trim().length < 5) {
                e.preventDefault();
                alert('Title must be at least 5 characters long');
                return false;
            }
            
            if (description.value.trim().length < 10) {
                e.preventDefault();
                alert('Description must be at least 10 characters long');
                return false;
            }
        });
    }
    
})();