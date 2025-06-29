/**
 * Bug Reporting System - Enhanced JavaScript with Robust Error Handling
 * Handles form submission, validation, animations, and UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Safely get DOM elements with fallbacks
    const form = document.getElementById('bugReportForm');
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    const submitSpinner = document.getElementById('submit-spinner');
    const resultsContainer = document.getElementById('ai-results');
    const resultsContent = document.getElementById('results-content');

    // Exit early if critical elements don't exist on this page
    if (!form || !submitBtn) {
        console.log('Bug form not found on this page - skipping initialization');
        return;
    }

    // Form submission handler with enhanced error handling
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!validateForm()) {
            return false;
        }
        
        // Show loading state
        setLoadingState(true);
        
        try {
            const formData = new FormData(form);
            
            const response = await fetch('/submit', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Display AI results
                if (resultsContainer && resultsContent) {
                    showResults(result);
                }
                
                // Show success message
                showAlert('success', 'Bug report submitted successfully!');
                
                // Reset form after delay
                setTimeout(() => {
                    form.reset();
                    form.classList.remove('was-validated');
                }, 2000);
            } else {
                showAlert('danger', result.error || 'Failed to submit bug report');
            }
        } catch (error) {
            console.error('Submission error:', error);
            showAlert('danger', 'Network error: Unable to submit bug report. Please check your connection and try again.');
        } finally {
            setLoadingState(false);
        }
    });

    // Initialize character counters for text fields
    const descriptionField = document.getElementById('description');
    const titleField = document.getElementById('title');
    
    if (descriptionField) {
        addCharacterCounter(descriptionField, 2000);
    }
    if (titleField) {
        addCharacterCounter(titleField, 200);
    }

    // Initialize file upload handling
    initializeFileUpload();
});

/**
 * Validate form inputs with comprehensive error checking
 */
function validateForm() {
    const form = document.getElementById('bugReportForm');
    const title = document.getElementById('title');
    const description = document.getElementById('description');
    
    if (!form || !title || !description) {
        console.log('Form validation failed: missing elements');
        return false;
    }
    
    let isValid = true;
    
    // Reset previous validation
    form.classList.remove('was-validated');
    
    // Validate title
    if (!title.value.trim() || title.value.trim().length < 5) {
        title.setCustomValidity('Title must be at least 5 characters long');
        isValid = false;
    } else {
        title.setCustomValidity('');
    }
    
    // Validate description
    if (!description.value.trim() || description.value.trim().length < 10) {
        description.setCustomValidity('Description must be at least 10 characters long');
        isValid = false;
    } else {
        description.setCustomValidity('');
    }
    
    // Apply validation styles
    form.classList.add('was-validated');
    
    return isValid;
}

/**
 * Set loading state with safe DOM manipulation
 */
function setLoadingState(loading) {
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    const submitSpinner = document.getElementById('submit-spinner');
    
    if (!submitBtn) {
        console.log('Submit button not found');
        return;
    }
    
    if (loading) {
        submitBtn.disabled = true;
        if (submitText) submitText.style.display = 'none';
        if (submitSpinner) submitSpinner.classList.remove('hidden');
    } else {
        submitBtn.disabled = false;
        if (submitText) submitText.style.display = 'flex';
        if (submitSpinner) submitSpinner.classList.add('hidden');
    }
}

/**
 * Show alert message with safe DOM manipulation
 */
function showAlert(type, message) {
    // Create alert if it doesn't exist
    let alertContainer = document.getElementById('alert-container');
    
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.className = 'fixed top-4 right-4 z-50';
        document.body.appendChild(alertContainer);
    }
    
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} bg-${type === 'success' ? 'green' : 'red'}-600 text-white p-4 rounded-lg shadow-lg mb-4`;
    alert.textContent = message;
    
    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'ml-4 text-white hover:text-gray-200';
    closeBtn.innerHTML = '&times;';
    closeBtn.onclick = () => alert.remove();
    alert.appendChild(closeBtn);
    
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Show results with safe DOM manipulation
 */
function showResults(result) {
    const resultsContainer = document.getElementById('ai-results');
    const resultsContent = document.getElementById('results-content');
    
    if (!resultsContainer || !resultsContent) {
        console.log('Results containers not found');
        return;
    }
    
    // Safely create results content
    const content = document.createElement('div');
    content.className = 'space-y-6';
    
    // Bug report ID
    const idSection = document.createElement('div');
    idSection.className = 'bg-blue-900 border border-blue-700 rounded-lg p-6';
    idSection.innerHTML = `
        <h3 class="text-lg font-bold text-blue-100 mb-3">
            <i class="fas fa-id-badge text-blue-400 mr-2"></i>
            Bug Report Created
        </h3>
        <p class="text-blue-200">Report ID: #${result.report_id}</p>
    `;
    content.appendChild(idSection);
    
    // AI analysis
    if (result.parsed_steps) {
        const aiSection = document.createElement('div');
        aiSection.className = 'bg-purple-900 border border-purple-700 rounded-lg p-6';
        aiSection.innerHTML = `
            <h3 class="text-lg font-bold text-purple-100 mb-3">
                <i class="fas fa-robot text-purple-400 mr-2"></i>
                AI-Generated Reproduction Steps
            </h3>
            <div class="text-purple-200 whitespace-pre-wrap">${escapeHtml(result.parsed_steps)}</div>
        `;
        content.appendChild(aiSection);
    }
    
    // Action buttons
    const actionsSection = document.createElement('div');
    actionsSection.className = 'flex flex-wrap gap-4 justify-center';
    actionsSection.innerHTML = `
        <a href="/history" class="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <i class="fas fa-history mr-2"></i>View Your Reports
        </a>
        <button onclick="resetForm()" class="inline-flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
            <i class="fas fa-plus mr-2"></i>Submit Another Report
        </button>
    `;
    content.appendChild(actionsSection);
    
    // Update results container
    resultsContent.innerHTML = '';
    resultsContent.appendChild(content);
    resultsContainer.classList.remove('hidden');
}

/**
 * Add character counter to input field with safe DOM manipulation
 */
function addCharacterCounter(field, maxLength) {
    if (!field || !field.parentNode) {
        console.log('Cannot add character counter: field or parent not found');
        return;
    }
    
    const counter = document.createElement('div');
    counter.className = 'character-counter text-sm text-gray-400 mt-1 text-right';
    counter.textContent = `0/${maxLength}`;
    
    field.parentNode.appendChild(counter);
    
    field.addEventListener('input', function() {
        const currentLength = this.value.length;
        counter.textContent = `${currentLength}/${maxLength}`;
        
        // Color coding based on length
        if (currentLength > maxLength * 0.9) {
            counter.className = 'character-counter text-sm text-red-400 mt-1 text-right';
        } else if (currentLength > maxLength * 0.7) {
            counter.className = 'character-counter text-sm text-yellow-400 mt-1 text-right';
        } else {
            counter.className = 'character-counter text-sm text-gray-400 mt-1 text-right';
        }
    });
}

/**
 * Initialize file upload handling with safe DOM manipulation
 */
function initializeFileUpload() {
    const fileInput = document.getElementById('attachments');
    const dropArea = document.querySelector('.drop-zone') || document.querySelector('[ondrop]');
    
    if (!fileInput) {
        console.log('File input not found - skipping file upload initialization');
        return;
    }
    
    // File input change handler
    fileInput.addEventListener('change', function() {
        displayFileList(this.files);
    });
    
    // Only initialize drag and drop if drop area exists
    if (dropArea) {
        // Drag and drop handlers
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });
        
        dropArea.addEventListener('drop', handleDrop, false);
    }
}

/**
 * Display file list with safe DOM manipulation
 */
function displayFileList(files) {
    const fileListDiv = document.getElementById('file-list');
    
    if (!fileListDiv) {
        console.log('File list container not found');
        return;
    }
    
    if (files.length === 0) {
        fileListDiv.innerHTML = '';
        return;
    }
    
    fileListDiv.innerHTML = '';
    
    const container = document.createElement('div');
    container.className = 'mt-4 space-y-2';
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileItem = document.createElement('div');
        fileItem.className = 'flex items-center justify-between bg-gray-700 p-3 rounded-lg';
        
        fileItem.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-file text-blue-400 mr-3"></i>
                <div>
                    <div class="text-white font-medium">${escapeHtml(file.name)}</div>
                    <div class="text-gray-400 text-sm">${formatFileSize(file.size)}</div>
                </div>
            </div>
            <button type="button" class="text-red-400 hover:text-red-300" onclick="removeFile(${i})">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(fileItem);
    }
    
    fileListDiv.appendChild(container);
}

/**
 * Utility functions
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    if (e.currentTarget && e.currentTarget.classList) {
        e.currentTarget.classList.add('border-blue-500', 'bg-blue-900');
    }
}

function unhighlight(e) {
    if (e.currentTarget && e.currentTarget.classList) {
        e.currentTarget.classList.remove('border-blue-500', 'bg-blue-900');
    }
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    const fileInput = document.getElementById('attachments');
    if (fileInput) {
        fileInput.files = files;
        displayFileList(files);
    }
}

function resetForm() {
    const form = document.getElementById('bugReportForm');
    if (form) {
        form.reset();
        form.classList.remove('was-validated');
        
        const resultsContainer = document.getElementById('ai-results');
        if (resultsContainer) {
            resultsContainer.classList.add('hidden');
        }
        
        const fileList = document.getElementById('file-list');
        if (fileList) {
            fileList.innerHTML = '';
        }
    }
}

function removeFile(index) {
    // File removal logic would go here
    console.log('Remove file at index:', index);
}

// Global functions for template usage
window.resetForm = resetForm;
window.removeFile = removeFile;