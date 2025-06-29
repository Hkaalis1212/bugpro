/**
 * Advanced Features JavaScript
 * Handles reproducibility scoring, recording, and export functionality
 */

// Escape HTML characters to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show reproducibility score details
function showReproducibilityDetails(reportId) {
    fetch(`/api/reproducibility-score/${reportId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError('Failed to load reproducibility details: ' + data.error);
                return;
            }
            
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            
            // Create modal structure using DOM methods instead of innerHTML to prevent XSS
            const modalDialog = document.createElement('div');
            modalDialog.className = 'modal-dialog modal-lg';
            
            const modalContent = document.createElement('div');
            modalContent.className = 'modal-content';
            
            // Header
            const modalHeader = document.createElement('div');
            modalHeader.className = 'modal-header';
            modalHeader.innerHTML = `
                <h5 class="modal-title">Reproducibility Analysis</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            `;
            
            // Body
            const modalBody = document.createElement('div');
            modalBody.className = 'modal-body';
            
            // Score section
            const scoreRow = document.createElement('div');
            scoreRow.className = 'row mb-3';
            
            const scoreCol = document.createElement('div');
            scoreCol.className = 'col-md-6';
            scoreCol.innerHTML = '<h6>Overall Score</h6>';
            
            const progressDiv = document.createElement('div');
            progressDiv.className = 'progress mb-2';
            
            const progressBar = document.createElement('div');
            progressBar.className = `progress-bar ${getScoreColor(data.score)}`;
            progressBar.style.width = `${Math.max(0, Math.min(100, parseFloat(data.score) || 0))}%`;
            progressBar.setAttribute('role', 'progressbar');
            progressBar.textContent = `${(parseFloat(data.score) || 0).toFixed(1)}%`;
            
            progressDiv.appendChild(progressBar);
            scoreCol.appendChild(progressDiv);
            
            const confidenceCol = document.createElement('div');
            confidenceCol.className = 'col-md-6';
            confidenceCol.innerHTML = '<h6>Confidence Level</h6>';
            
            const confidenceBadge = document.createElement('span');
            confidenceBadge.className = `badge bg-${getConfidenceColor(data.confidence)}`;
            confidenceBadge.textContent = data.confidence || '';
            confidenceCol.appendChild(confidenceBadge);
            
            scoreRow.appendChild(scoreCol);
            scoreRow.appendChild(confidenceCol);
            
            // Factors and missing info section
            const factorsRow = document.createElement('div');
            factorsRow.className = 'row';
            
            const factorsCol = document.createElement('div');
            factorsCol.className = 'col-md-6';
            factorsCol.innerHTML = '<h6>Positive Factors</h6>';
            
            const factorsList = document.createElement('ul');
            factorsList.className = 'list-unstyled';
            
            (data.factors || []).forEach(factor => {
                const li = document.createElement('li');
                li.innerHTML = '<i class="fas fa-check text-success me-2"></i>';
                li.appendChild(document.createTextNode(factor));
                factorsList.appendChild(li);
            });
            
            factorsCol.appendChild(factorsList);
            
            const missingCol = document.createElement('div');
            missingCol.className = 'col-md-6';
            missingCol.innerHTML = '<h6>Missing Information</h6>';
            
            const missingList = document.createElement('ul');
            missingList.className = 'list-unstyled';
            
            (data.missing_info || []).forEach(info => {
                const li = document.createElement('li');
                li.innerHTML = '<i class="fas fa-exclamation-triangle text-warning me-2"></i>';
                li.appendChild(document.createTextNode(info));
                missingList.appendChild(li);
            });
            
            missingCol.appendChild(missingList);
            
            factorsRow.appendChild(factorsCol);
            factorsRow.appendChild(missingCol);
            
            // Recommendations section
            const recDiv = document.createElement('div');
            recDiv.className = 'mt-3';
            recDiv.innerHTML = '<h6>Recommendations</h6>';
            
            const recList = document.createElement('ul');
            (data.recommendations || []).forEach(rec => {
                const li = document.createElement('li');
                li.textContent = rec;
                recList.appendChild(li);
            });
            
            recDiv.appendChild(recList);
            
            // Assemble modal
            modalBody.appendChild(scoreRow);
            modalBody.appendChild(factorsRow);
            modalBody.appendChild(recDiv);
            
            modalContent.appendChild(modalHeader);
            modalContent.appendChild(modalBody);
            modalDialog.appendChild(modalContent);
            modal.appendChild(modalDialog);
            
            document.body.appendChild(modal);
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
            
            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
            });
        })
        .catch(error => {
            showError('Failed to load reproducibility details');
        });
}

// Start screen recording
function startRecording(reportId) {
    const duration = prompt('Recording duration in seconds (default: 60):', '60');
    if (!duration) return;
    
    showLoading(true);
    
    fetch('/api/start-recording', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            bug_id: reportId,
            duration: parseInt(duration)
        })
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        
        if (data.success) {
            showSuccess('Recording started successfully! Duration: ' + duration + ' seconds');
            // Refresh the page after recording duration + 5 seconds
            setTimeout(() => {
                location.reload();
            }, (parseInt(duration) + 5) * 1000);
        } else {
            showError(data.error || 'Failed to start recording');
        }
    })
    .catch(error => {
        showLoading(false);
        showError('Failed to start recording');
    });
}

// Export to GitHub
function exportToGithub(reportId) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Export to GitHub</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="githubExportForm">
                        <div class="mb-3">
                            <label for="githubToken" class="form-label">GitHub Token</label>
                            <input type="password" class="form-control" id="githubToken" required>
                            <div class="form-text">Personal access token with repo permissions</div>
                        </div>
                        <div class="mb-3">
                            <label for="repoOwner" class="form-label">Repository Owner</label>
                            <input type="text" class="form-control" id="repoOwner" required>
                        </div>
                        <div class="mb-3">
                            <label for="repoName" class="form-label">Repository Name</label>
                            <input type="text" class="form-control" id="repoName" required>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="githubExportBtn">Export</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listener safely without using onclick
    const exportBtn = modal.querySelector('#githubExportBtn');
    exportBtn.addEventListener('click', () => performGithubExport(reportId));
    
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

// Export to Jira
function exportToJira(reportId) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Export to Jira</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="jiraExportForm">
                        <div class="mb-3">
                            <label for="jiraUrl" class="form-label">Jira URL</label>
                            <input type="url" class="form-control" id="jiraUrl" placeholder="https://yourcompany.atlassian.net" required>
                        </div>
                        <div class="mb-3">
                            <label for="jiraUsername" class="form-label">Username</label>
                            <input type="email" class="form-control" id="jiraUsername" required>
                        </div>
                        <div class="mb-3">
                            <label for="jiraToken" class="form-label">API Token</label>
                            <input type="password" class="form-control" id="jiraToken" required>
                        </div>
                        <div class="mb-3">
                            <label for="projectKey" class="form-label">Project Key</label>
                            <input type="text" class="form-control" id="projectKey" placeholder="PROJ" required>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="jiraExportBtn">Export</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listener safely without using onclick
    const exportBtn = modal.querySelector('#jiraExportBtn');
    exportBtn.addEventListener('click', () => performJiraExport(reportId));
    
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

// Perform GitHub export
function performGithubExport(reportId) {
    const token = document.getElementById('githubToken').value;
    const owner = document.getElementById('repoOwner').value;
    const name = document.getElementById('repoName').value;
    
    if (!token || !owner || !name) {
        showError('All fields are required');
        return;
    }
    
    showLoading(true);
    
    fetch(`/api/export/github/${reportId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            github_token: token,
            repo_owner: owner,
            repo_name: name
        })
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        bootstrap.Modal.getInstance(document.querySelector('.modal')).hide();
        
        if (data.success) {
            showSuccess(`Successfully exported to GitHub: ${data.github_url}`);
            refreshReports();
        } else {
            showError(data.error || 'Export failed');
        }
    })
    .catch(error => {
        showLoading(false);
        showError('Export failed');
    });
}

// Perform Jira export
function performJiraExport(reportId) {
    const url = document.getElementById('jiraUrl').value;
    const username = document.getElementById('jiraUsername').value;
    const token = document.getElementById('jiraToken').value;
    const projectKey = document.getElementById('projectKey').value;
    
    if (!url || !username || !token || !projectKey) {
        showError('All fields are required');
        return;
    }
    
    showLoading(true);
    
    fetch(`/api/export/jira/${reportId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            jira_url: url,
            jira_username: username,
            jira_token: token,
            project_key: projectKey
        })
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        bootstrap.Modal.getInstance(document.querySelector('.modal')).hide();
        
        if (data.success) {
            showSuccess(`Successfully exported to Jira: ${data.jira_url}`);
            refreshReports();
        } else {
            showError(data.error || 'Export failed');
        }
    })
    .catch(error => {
        showLoading(false);
        showError('Export failed');
    });
}

// Helper functions
function getScoreColor(score) {
    if (score >= 80) return 'bg-success';
    if (score >= 60) return 'bg-info';
    if (score >= 40) return 'bg-warning';
    return 'bg-danger';
}

function getConfidenceColor(confidence) {
    const conf = confidence.toLowerCase();
    if (conf.includes('very high') || conf.includes('high')) return 'success';
    if (conf.includes('medium')) return 'warning';
    return 'danger';
}