/**
 * Bug Reporting System - Enhanced JavaScript with TailwindCSS
 * Handles form submission, validation, animations, and UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('bugReportForm');
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    const submitSpinner = document.getElementById('submit-spinner');
    const resultsContainer = document.getElementById('ai-results');
    const resultsContent = document.getElementById('results-content');

    // Exit early if required elements don't exist on this page
    if (!form || !submitBtn) {
        console.log('Bug form not found on this page');
        return;
    }

    // Initialize project/team loading if user is authenticated
    if (document.getElementById('project_id')) {
        loadUserProjects();
    }

    // Form submission handler with enhanced animations
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Add form submitting animation
        form.classList.add('form-submitting');
        
        // Show loading state with smooth transitions
        setLoadingState(true);
        
        try {
            // Get form data including files
            const formData = new FormData(form);
            
            // Submit bug report with FormData (for file uploads)
            const response = await fetch('/submit', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success animation
                form.classList.remove('form-submitting');
                form.classList.add('form-success');
                
                // Display AI results with fade-in animation
                showResults(result);
                
                // Reset form after short delay
                setTimeout(() => {
                    form.reset();
                    form.classList.remove('form-success');
                }, 1000);
            } else {
                // Show error state
                showError(result.error || 'An error occurred while submitting the bug report.');
            }
        } catch (error) {
            console.error('Submission error:', error);
            showError('Network error. Please check your connection and try again.');
        } finally {
            setLoadingState(false);
            form.classList.remove('form-submitting');
        }
    });

    // Enhanced loading state with smooth transitions
    function setLoadingState(loading) {
        if (loading) {
            submitBtn.disabled = true;
            submitBtn.classList.add('pulse-loading', 'opacity-75');
            submitText.style.display = 'none';
            submitSpinner.classList.remove('hidden');
        } else {
            submitBtn.disabled = false;
            submitBtn.classList.remove('pulse-loading', 'opacity-75');
            submitText.style.display = 'inline';
            submitSpinner.classList.add('hidden');
        }
    }

    // Show success animation
    function showSuccessAnimation(reportId) {
        const animation = document.getElementById('successAnimation');
        const card = document.getElementById('successCard');
        const reportIdSpan = document.getElementById('successReportId');
        
        if (animation && card && reportIdSpan) {
            reportIdSpan.textContent = reportId;
            animation.classList.remove('hidden');
            
            // Animate card entrance
            setTimeout(() => {
                card.style.transform = 'scale(1)';
            }, 100);
            
            // Auto-hide after 3 seconds
            setTimeout(() => {
                card.style.transform = 'scale(0)';
                setTimeout(() => {
                    animation.classList.add('hidden');
                }, 500);
            }, 3000);
        }
    }

    // Show AI results with enhanced animations and cards
    function showResults(result) {
        // Show success animation first
        showSuccessAnimation(result.report_id);
        
        // Get confidence level color
        const confidenceColor = getConfidenceColor(result.reproducibility_confidence);
        const scoreColor = getScoreColor(result.reproducibility_score);
        
        const content = `
            <!-- Report Summary Cards -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <div class="bg-gradient-to-br from-green-800 to-green-900 border border-green-600 rounded-xl p-6 transform hover:scale-105 transition-all duration-300">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-bold text-green-100">Report Status</h3>
                        <div class="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
                            <i class="fas fa-check text-white text-xl"></i>
                        </div>
                    </div>
                    <p class="text-green-200 mb-2">Report ID: <span class="font-mono font-bold text-green-100">#${result.report_id}</span></p>
                    <div class="flex items-center">
                        <div class="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                        <span class="text-green-300 text-sm">Successfully submitted</span>
                    </div>
                </div>
                
                <div class="bg-gradient-to-br ${scoreColor.bg} border ${scoreColor.border} rounded-xl p-6 transform hover:scale-105 transition-all duration-300">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-bold ${scoreColor.text}">Reproducibility</h3>
                        <div class="w-12 h-12 ${scoreColor.iconBg} rounded-full flex items-center justify-center">
                            <i class="fas fa-chart-line text-white text-xl"></i>
                        </div>
                    </div>
                    <div class="flex items-end space-x-2 mb-2">
                        <span class="text-3xl font-bold ${scoreColor.text}">${result.reproducibility_score.toFixed(1)}</span>
                        <span class="text-lg ${scoreColor.text} opacity-75">/100</span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2 mb-2">
                        <div class="${scoreColor.progressBg} h-2 rounded-full transition-all duration-1000 ease-out" style="width: ${result.reproducibility_score}%"></div>
                    </div>
                </div>
                
                <div class="bg-gradient-to-br ${confidenceColor.bg} border ${confidenceColor.border} rounded-xl p-6 transform hover:scale-105 transition-all duration-300">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-bold ${confidenceColor.text}">Confidence</h3>
                        <div class="w-12 h-12 ${confidenceColor.iconBg} rounded-full flex items-center justify-center">
                            <i class="fas fa-shield-alt text-white text-xl"></i>
                        </div>
                    </div>
                    <p class="text-2xl font-bold ${confidenceColor.text} capitalize mb-2">${result.reproducibility_confidence}</p>
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${confidenceColor.badgeBg} ${confidenceColor.badgeText}">
                        <i class="fas fa-circle mr-1 text-xs"></i>
                        ${getConfidenceDescription(result.reproducibility_confidence)}
                    </span>
                </div>
            </div>
            
            <!-- AI Analysis Card -->
            <div class="bg-gradient-to-br from-purple-800 to-purple-900 border border-purple-600 rounded-xl p-6 mb-6">
                <h3 class="text-lg font-bold text-purple-100 mb-4 flex items-center">
                    <i class="fas fa-robot text-purple-400 mr-3"></i>
                    AI-Generated Reproduction Steps
                </h3>
                <div class="bg-gray-900 rounded-lg p-4 border border-gray-700">
                    <pre class="text-gray-200 whitespace-pre-wrap font-mono text-sm leading-relaxed">${result.parsed_steps || 'No specific steps could be extracted from the description.'}</pre>
                </div>
            </div>
            
            <!-- View History Link -->
            <div class="bg-gray-800 rounded-xl p-6 text-center">
                <h3 class="text-lg font-bold text-gray-200 mb-4">What's Next?</h3>
                <div class="flex flex-col sm:flex-row gap-4 justify-center">
                    <a href="/history" class="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                        <i class="fas fa-history mr-2"></i>View Your Reports
                    </a>
                    <button onclick="resetForm()" class="inline-flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
                        <i class="fas fa-plus mr-2"></i>Submit Another Report
                    </button>
                </div>
            </div>
        `;
        
        resultsContent.innerHTML = content;
        resultsContainer.classList.remove('hidden');
        resultsContainer.classList.add('results-enter');
        
        // Smooth scroll to results
        setTimeout(() => {
            resultsContainer.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }, 300);
    }

    // Show error with enhanced styling
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-50 border-2 border-red-200 text-red-800 px-6 py-4 rounded-xl shadow-lg z-50 fade-in';
        errorDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-circle text-red-600 mr-3"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-red-600 hover:text-red-800">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        document.body.appendChild(errorDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    // Real-time character counting for description
    const descriptionField = document.getElementById('description');
    const titleField = document.getElementById('title');
    
    // Add character counter to description field
    if (descriptionField) {
        addCharacterCounter(descriptionField, 2000);
    }
    if (titleField) {
        addCharacterCounter(titleField, 200);
    }
    
    // File input and drag-drop handlers
    const fileInput = document.getElementById('attachments');
    const dropArea = document.getElementById('drop-area');
    const browseLink = document.getElementById('browse-link');
    
    // Check if elements exist before adding event listeners
    if (fileInput && dropArea && browseLink) {
        // File input change handler
        fileInput.addEventListener('change', function() {
            displayFileList(this.files);
        });
        
        // Browse link click handler
        browseLink.addEventListener('click', function() {
            fileInput.click();
        });
        
        // Drag and drop event handlers
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
});

/**
 * Validate the form inputs
 */
function validateForm() {
    const form = document.getElementById('bugReportForm');
    const title = document.getElementById('title');
    const description = document.getElementById('description');
    
    if (!form || !title || !description) {
        console.log('Form elements not found');
        return false;
    }
    
    let isValid = true;
    
    // Reset validation classes
    form.classList.remove('was-validated');
    
    // Validate title
    if (!title.value.trim()) {
        title.setCustomValidity('Title is required');
        isValid = false;
    } else if (title.value.trim().length < 5) {
        title.setCustomValidity('Title must be at least 5 characters long');
        isValid = false;
    } else {
        title.setCustomValidity('');
    }
    
    // Validate description
    if (!description.value.trim()) {
        description.setCustomValidity('Description is required');
        isValid = false;
    } else if (description.value.trim().length < 10) {
        description.setCustomValidity('Description must be at least 10 characters long');
        isValid = false;
    } else {
        description.setCustomValidity('');
    }
    
    // Apply validation classes
    form.classList.add('was-validated');
    
    return isValid;
}

/**
 * Show alert message
 */
function showAlert(type, message) {
    const alertContainer = document.getElementById('alertContainer');
    const alertMessage = document.getElementById('alertMessage');
    const alertText = document.getElementById('alertText');
    
    if (!alertContainer || !alertMessage || !alertText) {
        console.log('Alert elements not found');
        return;
    }
    
    alertMessage.className = `alert alert-${type}`;
    
    // Create icon element safely
    const icon = document.createElement('i');
    icon.className = `fas fa-${type === 'danger' ? 'exclamation-triangle' : 'info-circle'} me-2`;
    
    // Clear previous content and add icon + text safely
    alertText.textContent = '';
    alertText.appendChild(icon);
    alertText.appendChild(document.createTextNode(message));
    
    alertContainer.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(hideAlert, 5000);
    }
    
    // Scroll to alert if it exists
    if (alertContainer.scrollIntoView) {
        alertContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/**
 * Hide alert message
 */
function hideAlert() {
    const alertContainer = document.getElementById('alertContainer');
    if (alertContainer) {
        alertContainer.style.display = 'none';
    }
}

/**
 * Show results after successful submission
 */
function showResults(reportId, parsedSteps) {
    const resultsContainer = document.getElementById('resultsContainer');
    const reportIdElement = document.getElementById('reportId');
    const parsedStepsElement = document.getElementById('parsedSteps');
    
    if (!resultsContainer || !reportIdElement || !parsedStepsElement) {
        console.log('Results elements not found');
        return;
    }
    
    reportIdElement.textContent = `#${reportId}`;
    
    // Safely display parsed steps using DOM methods instead of innerHTML
    displayParsedStepsSafely(parsedStepsElement, parsedSteps);
    
    resultsContainer.style.display = 'block';
    
    // Scroll to results
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Hide results container
 */
function hideResults() {
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.style.display = 'none';
}

/**
 * Safely display parsed steps using DOM methods to prevent XSS
 */
function displayParsedStepsSafely(container, steps) {
    // Clear existing content
    container.innerHTML = '';
    
    if (!steps) {
        const em = document.createElement('em');
        em.className = 'text-muted';
        em.textContent = 'No steps could be extracted from the description.';
        container.appendChild(em);
        return;
    }
    
    // Check if it's an error message
    if (steps.includes('[AI parsing failed:')) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-warning';
        
        const icon = document.createElement('i');
        icon.className = 'fas fa-exclamation-triangle me-2';
        errorDiv.appendChild(icon);
        
        const textNode = document.createTextNode(steps);
        errorDiv.appendChild(textNode);
        
        container.appendChild(errorDiv);
        return;
    }
    
    // Create main container for parsed steps
    const stepsDiv = document.createElement('div');
    stepsDiv.className = 'parsed-steps';
    
    // Split into lines and process each one
    const lines = steps.split('\n');
    
    lines.forEach((line, index) => {
        if (line.trim() === '') {
            // Add line break for empty lines
            if (index > 0) stepsDiv.appendChild(document.createElement('br'));
            return;
        }
        
        // Check for numbered steps
        const numberedMatch = line.match(/^(\d+\.\s)(.*)$/);
        if (numberedMatch) {
            const strong = document.createElement('strong');
            strong.textContent = numberedMatch[1];
            stepsDiv.appendChild(strong);
            stepsDiv.appendChild(document.createTextNode(numberedMatch[2]));
        }
        // Check for bullet points
        else if (line.match(/^[-*]\s/)) {
            const strong = document.createElement('strong');
            strong.textContent = '• ';
            stepsDiv.appendChild(strong);
            stepsDiv.appendChild(document.createTextNode(line.substring(2)));
        }
        // Regular text
        else {
            stepsDiv.appendChild(document.createTextNode(line));
        }
        
        // Add line break if not the last line
        if (index < lines.length - 1) {
            stepsDiv.appendChild(document.createElement('br'));
        }
    });
    
    container.appendChild(stepsDiv);
}

/**
 * Set loading state
 */
function setLoadingState(loading) {
    const submitBtn = document.getElementById('submit-btn') || document.getElementById('submitBtn');
    const submitText = document.getElementById('submit-text');
    const submitSpinner = document.getElementById('submit-spinner') || document.getElementById('loadingSpinner');
    
    if (!submitBtn) {
        console.log('Submit button not found');
        return;
    }
    
    if (loading) {
        submitBtn.disabled = true;
        if (submitText) {
            submitText.style.display = 'none';
        }
        if (submitSpinner) {
            submitSpinner.classList.remove('hidden');
        }
    } else {
        submitBtn.disabled = false;
        if (submitText) {
            submitText.style.display = 'flex';
        }
        if (submitSpinner) {
            submitSpinner.classList.add('hidden');
        }
        loadingSpinner.style.display = 'none';
    }
}

/**
 * Reset form and show form again
 */
function resetForm() {
    const form = document.getElementById('bugReportForm');
    form.reset();
    form.classList.remove('was-validated');
    hideResults();
    hideAlert();
    
    // Scroll back to form
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Add character counter to input field
 */
function addCharacterCounter(field, maxLength) {
    const counterDiv = document.createElement('div');
    counterDiv.className = 'form-text text-end';
    counterDiv.innerHTML = `<small><span id="${field.id}Counter">0</span>/${maxLength}</small>`;
    
    field.parentNode.appendChild(counterDiv);
    
    const counter = document.getElementById(`${field.id}Counter`);
    
    field.addEventListener('input', function() {
        const currentLength = this.value.length;
        counter.textContent = currentLength;
        
        // Change color based on length
        if (currentLength > maxLength * 0.9) {
            counter.className = 'text-warning';
        } else if (currentLength === maxLength) {
            counter.className = 'text-danger';
        } else {
            counter.className = '';
        }
    });
}

/**
 * Copy parsed steps to clipboard
 */
function copySteps() {
    const stepsElement = document.getElementById('parsedSteps');
    const stepsText = stepsElement.textContent || stepsElement.innerText;
    
    navigator.clipboard.writeText(stepsText).then(function() {
        showAlert('success', 'Reproduction steps copied to clipboard!');
    }).catch(function(err) {
        console.error('Failed to copy: ', err);
        showAlert('warning', 'Failed to copy to clipboard. Please select and copy manually.');
    });
}

/**
 * Prevent default drag behaviors
 */
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * Highlight drop area when item is dragged over it
 */
function highlight(e) {
    const dropArea = document.getElementById('drop-area');
    dropArea.classList.add('highlight');
}

/**
 * Remove highlight from drop area
 */
function unhighlight(e) {
    const dropArea = document.getElementById('drop-area');
    dropArea.classList.remove('highlight');
}

/**
 * Handle dropped files
 */
function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    // Update the file input with dropped files
    const fileInput = document.getElementById('attachments');
    if (fileInput) {
        fileInput.files = files;
    }
    
    displayFileList(files);
}

/**
 * Display selected files with file info and remove buttons
 */
function displayFileList(files) {
    const fileListDiv = document.getElementById('fileList') || document.getElementById('file-list');
    
    if (!fileListDiv) {
        console.log('File list container not found');
        return;
    }
    
    if (files.length === 0) {
        fileListDiv.innerHTML = '';
        return;
    }
    
    // Clear existing content
    fileListDiv.innerHTML = '';
    
    // Create container elements using DOM methods to prevent XSS
    const container = document.createElement('div');
    container.className = 'mt-2';
    
    const label = document.createElement('small');
    label.className = 'text-muted';
    label.textContent = 'Selected files:';
    container.appendChild(label);
    
    const fileContainer = document.createElement('div');
    fileContainer.className = 'mt-1';
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const sizeKB = (file.size / 1024).toFixed(1);
        const sizeText = sizeKB > 1024 ? `${(sizeKB / 1024).toFixed(1)} MB` : `${sizeKB} KB`;
        
        // Get file icon based on type
        const icon = getFileIcon(file.type, file.name);
        
        // Create file item using DOM methods to prevent XSS
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item d-flex justify-content-between align-items-center bg-light text-dark px-3 py-2 rounded mb-2';
        
        const fileInfo = document.createElement('div');
        fileInfo.className = 'd-flex align-items-center';
        
        const iconElement = document.createElement('i');
        iconElement.className = icon + ' me-2';
        
        const textContainer = document.createElement('div');
        
        const fileName = document.createElement('div');
        fileName.className = 'fw-medium';
        fileName.textContent = file.name; // Safe text content assignment
        
        const fileSize = document.createElement('small');
        fileSize.className = 'text-muted';
        fileSize.textContent = sizeText;
        
        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.className = 'btn btn-sm btn-outline-danger';
        removeButton.addEventListener('click', () => removeFile(i)); // Safe event listener
        
        const removeIcon = document.createElement('i');
        removeIcon.className = 'fas fa-times';
        removeButton.appendChild(removeIcon);
        
        // Assemble the structure
        textContainer.appendChild(fileName);
        textContainer.appendChild(fileSize);
        fileInfo.appendChild(iconElement);
        fileInfo.appendChild(textContainer);
        fileItem.appendChild(fileInfo);
        fileItem.appendChild(removeButton);
        fileContainer.appendChild(fileItem);
    }
    
    container.appendChild(fileContainer);
    fileListDiv.appendChild(container);
}

/**
 * Get appropriate icon for file type
 */
function getFileIcon(mimeType, filename) {
    if (mimeType.startsWith('image/')) {
        return 'fas fa-image text-success';
    } else if (mimeType === 'application/pdf') {
        return 'fas fa-file-pdf text-danger';
    } else if (filename.endsWith('.log')) {
        return 'fas fa-file-alt text-warning';
    } else if (filename.endsWith('.json')) {
        return 'fas fa-file-code text-info';
    } else if (filename.endsWith('.xml')) {
        return 'fas fa-file-code text-info';
    } else if (mimeType.startsWith('text/')) {
        return 'fas fa-file-alt text-primary';
    } else {
        return 'fas fa-file text-secondary';
    }
}

/**
 * Remove file from selection
 */
function removeFile(index) {
    const fileInput = document.getElementById('attachments');
    const dt = new DataTransfer();
    
    // Add all files except the one to remove
    for (let i = 0; i < fileInput.files.length; i++) {
        if (i !== index) {
            dt.items.add(fileInput.files[i]);
        }
    }
    
    // Update file input
    fileInput.files = dt.files;
    
    // Update display
    displayFileList(fileInput.files);
}

/**
 * Escape HTML characters to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
