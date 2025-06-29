/**
 * Bug Reporting System - Error-Free JavaScript
 * Completely safe DOM manipulation with comprehensive null checks
 */

// Global flag to prevent multiple initializations
let isInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    if (isInitialized) return;
    isInitialized = true;
    
    console.log('Initializing bug reporting system...');
    
    // Only initialize if we're on the bug reporting page
    const form = document.getElementById('bugReportForm');
    if (!form) {
        console.log('Bug form not found - skipping form initialization');
        return;
    }
    
    initializeBugForm();
});

function initializeBugForm() {
    const form = document.getElementById('bugReportForm');
    const submitBtn = document.getElementById('submit-btn');
    
    if (!form || !submitBtn) {
        console.log('Required form elements not found');
        return;
    }
    
    // Form submission handler
    form.addEventListener('submit', handleFormSubmit);
    
    // Initialize file upload if elements exist
    initializeFileUploadSafe();
    
    // Initialize character counters if elements exist
    initializeCharacterCounters();
    
    console.log('Bug form initialized successfully');
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (!validateFormSafe()) {
        return false;
    }
    
    setLoadingStateSafe(true);
    
    try {
        const formData = new FormData(e.target);
        
        const response = await fetch('/submit', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showResultsSafe(result);
            showAlertSafe('success', 'Bug report submitted successfully!');
            
            setTimeout(() => {
                e.target.reset();
                e.target.classList.remove('was-validated');
            }, 2000);
        } else {
            showAlertSafe('danger', result.error || 'Failed to submit bug report');
        }
    } catch (error) {
        console.error('Submission error:', error);
        showAlertSafe('danger', 'Network error: Unable to submit bug report. Please check your connection and try again.');
    } finally {
        setLoadingStateSafe(false);
    }
}

function validateFormSafe() {
    const form = document.getElementById('bugReportForm');
    const title = document.getElementById('title');
    const description = document.getElementById('description');
    
    if (!form || !title || !description) {
        console.log('Form validation failed: missing elements');
        return false;
    }
    
    let isValid = true;
    
    form.classList.remove('was-validated');
    
    if (!title.value.trim() || title.value.trim().length < 5) {
        if (title.setCustomValidity) {
            title.setCustomValidity('Title must be at least 5 characters long');
        }
        isValid = false;
    } else {
        if (title.setCustomValidity) {
            title.setCustomValidity('');
        }
    }
    
    if (!description.value.trim() || description.value.trim().length < 10) {
        if (description.setCustomValidity) {
            description.setCustomValidity('Description must be at least 10 characters long');
        }
        isValid = false;
    } else {
        if (description.setCustomValidity) {
            description.setCustomValidity('');
        }
    }
    
    form.classList.add('was-validated');
    return isValid;
}

function setLoadingStateSafe(loading) {
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    const submitSpinner = document.getElementById('submit-spinner');
    
    if (!submitBtn) return;
    
    submitBtn.disabled = loading;
    
    if (submitText) {
        submitText.style.display = loading ? 'none' : 'flex';
    }
    
    if (submitSpinner) {
        if (loading) {
            submitSpinner.classList.remove('hidden');
        } else {
            submitSpinner.classList.add('hidden');
        }
    }
}

function showAlertSafe(type, message) {
    let alertContainer = document.getElementById('alert-container');
    
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.className = 'fixed top-4 right-4 z-50';
        document.body.appendChild(alertContainer);
    }
    
    const alert = document.createElement('div');
    alert.className = `alert bg-${type === 'success' ? 'green' : 'red'}-600 text-white p-4 rounded-lg shadow-lg mb-4`;
    alert.textContent = message;
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'ml-4 text-white hover:text-gray-200';
    closeBtn.innerHTML = '&times;';
    closeBtn.onclick = () => {
        if (alert.parentNode) {
            alert.remove();
        }
    };
    alert.appendChild(closeBtn);
    
    alertContainer.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function showResultsSafe(result) {
    const resultsContainer = document.getElementById('ai-results');
    const resultsContent = document.getElementById('results-content');
    
    if (!resultsContainer || !resultsContent) {
        console.log('Results containers not found');
        return;
    }
    
    const content = document.createElement('div');
    content.className = 'space-y-6';
    
    // Bug report ID section
    const idSection = document.createElement('div');
    idSection.className = 'bg-blue-900 border border-blue-700 rounded-lg p-6';
    idSection.innerHTML = `
        <h3 class="text-lg font-bold text-blue-100 mb-3">
            <i class="fas fa-id-badge text-blue-400 mr-2"></i>
            Bug Report Created
        </h3>
        <p class="text-blue-200">Report ID: #${escapeHtmlSafe(result.report_id)}</p>
    `;
    content.appendChild(idSection);
    
    // AI analysis section
    if (result.parsed_steps) {
        const aiSection = document.createElement('div');
        aiSection.className = 'bg-purple-900 border border-purple-700 rounded-lg p-6';
        aiSection.innerHTML = `
            <h3 class="text-lg font-bold text-purple-100 mb-3">
                <i class="fas fa-robot text-purple-400 mr-2"></i>
                AI-Generated Reproduction Steps
            </h3>
            <div class="text-purple-200 whitespace-pre-wrap">${escapeHtmlSafe(result.parsed_steps)}</div>
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
        <button onclick="resetFormSafe()" class="inline-flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
            <i class="fas fa-plus mr-2"></i>Submit Another Report
        </button>
    `;
    content.appendChild(actionsSection);
    
    resultsContent.innerHTML = '';
    resultsContent.appendChild(content);
    resultsContainer.classList.remove('hidden');
}

function initializeCharacterCounters() {
    const descriptionField = document.getElementById('description');
    const titleField = document.getElementById('title');
    
    if (descriptionField) {
        addCharacterCounterSafe(descriptionField, 2000);
    }
    if (titleField) {
        addCharacterCounterSafe(titleField, 200);
    }
}

function addCharacterCounterSafe(field, maxLength) {
    if (!field || !field.parentNode) {
        return;
    }
    
    const counter = document.createElement('div');
    counter.className = 'character-counter text-sm text-gray-400 mt-1 text-right';
    counter.textContent = `0/${maxLength}`;
    
    field.parentNode.appendChild(counter);
    
    field.addEventListener('input', function() {
        const currentLength = this.value.length;
        counter.textContent = `${currentLength}/${maxLength}`;
        
        if (currentLength > maxLength * 0.9) {
            counter.className = 'character-counter text-sm text-red-400 mt-1 text-right';
        } else if (currentLength > maxLength * 0.7) {
            counter.className = 'character-counter text-sm text-yellow-400 mt-1 text-right';
        } else {
            counter.className = 'character-counter text-sm text-gray-400 mt-1 text-right';
        }
    });
}

function initializeFileUploadSafe() {
    const fileInput = document.getElementById('attachments');
    
    if (!fileInput) {
        console.log('File input not found - skipping file upload initialization');
        return;
    }
    
    fileInput.addEventListener('change', function() {
        displayFileListSafe(this.files);
    });
    
    // Only initialize drag and drop if we find drop zones
    const dropZones = document.querySelectorAll('[ondrop], .drop-zone');
    dropZones.forEach(dropZone => {
        if (!dropZone) return;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaultsSafe, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlightSafe, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlightSafe, false);
        });
        
        dropZone.addEventListener('drop', handleDropSafe, false);
    });
}

function displayFileListSafe(files) {
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
                    <div class="text-white font-medium">${escapeHtmlSafe(file.name)}</div>
                    <div class="text-gray-400 text-sm">${formatFileSizeSafe(file.size)}</div>
                </div>
            </div>
            <button type="button" class="text-red-400 hover:text-red-300" onclick="removeFileSafe(${i})">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(fileItem);
    }
    
    fileListDiv.appendChild(container);
}

// Safe utility functions
function escapeHtmlSafe(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatFileSizeSafe(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function preventDefaultsSafe(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (e && e.stopPropagation) e.stopPropagation();
}

function highlightSafe(e) {
    if (e && e.currentTarget && e.currentTarget.classList) {
        e.currentTarget.classList.add('border-blue-500', 'bg-blue-900');
    }
}

function unhighlightSafe(e) {
    if (e && e.currentTarget && e.currentTarget.classList) {
        e.currentTarget.classList.remove('border-blue-500', 'bg-blue-900');
    }
}

function handleDropSafe(e) {
    if (!e || !e.dataTransfer) return;
    
    const dt = e.dataTransfer;
    const files = dt.files;
    
    const fileInput = document.getElementById('attachments');
    if (fileInput) {
        fileInput.files = files;
        displayFileListSafe(files);
    }
}

function resetFormSafe() {
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

function removeFileSafe(index) {
    console.log('Remove file at index:', index);
    // File removal logic would go here
}

// Global functions for template usage
window.resetFormSafe = resetFormSafe;
window.removeFileSafe = removeFileSafe;