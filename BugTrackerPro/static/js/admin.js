/**
 * Admin Dashboard JavaScript
 * Handles report management, viewing, and deletion
 */

let allReports = [];
let filteredReports = [];
let currentPage = 1;
let totalPages = 1;
let selectedReports = new Set();

document.addEventListener('DOMContentLoaded', function() {
    loadReports();
    setupEventListeners();
});

function setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', debounce(filterReports, 300));
    
    // Modal event listeners
    const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
    document.getElementById('deleteReportBtn').addEventListener('click', function() {
        const reportId = this.getAttribute('data-report-id');
        if (reportId) {
            deleteReport(reportId);
            reportModal.hide();
        }
    });
}

async function loadReports(page = 1) {
    try {
        showLoading(true);
        
        const response = await fetch(`/reports?page=${page}&per_page=50`);
        const data = await response.json();
        
        if (data.success) {
            allReports = data.reports;
            filteredReports = [...allReports];
            currentPage = data.current_page;
            totalPages = data.pages;
            
            updateStats(data);
            displayReports(filteredReports);
            updatePagination();
        } else {
            showError('Failed to load reports: ' + data.error);
        }
    } catch (error) {
        console.error('Error loading reports:', error);
        showError('Network error while loading reports');
    } finally {
        showLoading(false);
    }
}

function updateStats(data) {
    document.getElementById('totalReports').textContent = data.total;
    
    // Calculate today's reports
    const today = new Date().toDateString();
    const todayCount = allReports.filter(report => 
        new Date(report.created_at).toDateString() === today
    ).length;
    document.getElementById('todayReports').textContent = todayCount;
    
    // Count reports with attachments
    const withAttachments = allReports.filter(report => 
        report.attachments && report.attachments.length > 0
    ).length;
    document.getElementById('attachmentReports').textContent = withAttachments;
    
    // Calculate average reports per day (last 30 days)
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const recentReports = allReports.filter(report => 
        new Date(report.created_at) >= thirtyDaysAgo
    ).length;
    const avgReports = Math.round(recentReports / 30 * 10) / 10;
    document.getElementById('avgReports').textContent = avgReports;
}

function displayReports(reports) {
    const container = document.getElementById('reportsList');
    const countElement = document.getElementById('reportCount');
    
    countElement.textContent = `${reports.length} report${reports.length !== 1 ? 's' : ''}`;
    
    if (reports.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <i class="fas fa-inbox fa-3x mb-3"></i>
                <h5>No bug reports found</h5>
                <p>No reports match your current search criteria.</p>
            </div>
        `;
        return;
    }
    
    // Clear container first
    container.innerHTML = '';
    
    // Create elements safely using DOM methods instead of innerHTML
    reports.forEach(report => {
        const reportCard = document.createElement('div');
        reportCard.className = 'report-card border-bottom p-3';
        reportCard.setAttribute('data-report-id', report.id);
        
        const row = document.createElement('div');
        row.className = 'row align-items-center';
        
        // Checkbox column
        const checkboxCol = document.createElement('div');
        checkboxCol.className = 'col-md-1';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input report-checkbox';
        checkbox.value = report.id;
        checkbox.addEventListener('change', () => toggleSelection(report.id));
        checkboxCol.appendChild(checkbox);
        
        // Content column
        const contentCol = document.createElement('div');
        contentCol.className = 'col-md-6';
        
        const title = document.createElement('h6');
        title.className = 'mb-1';
        const titleLink = document.createElement('a');
        titleLink.href = '#';
        titleLink.className = 'text-decoration-none';
        titleLink.textContent = report.title;
        titleLink.addEventListener('click', (e) => {
            e.preventDefault();
            viewReport(report.id);
        });
        title.appendChild(titleLink);
        
        const description = document.createElement('p');
        description.className = 'text-muted mb-1 small';
        description.textContent = truncateText(report.description, 100);
        
        const metadata = document.createElement('small');
        metadata.className = 'text-muted';
        
        // Create clock icon safely
        const clockIcon = document.createElement('i');
        clockIcon.className = 'fas fa-clock me-1';
        metadata.appendChild(clockIcon);
        
        // Add formatted date as text content (safe from XSS)
        const dateText = document.createTextNode(formatDate(report.created_at));
        metadata.appendChild(dateText);
        if (report.user_name) {
            const userSpan = document.createElement('span');
            userSpan.innerHTML = ` • <i class="fas fa-user me-1"></i>`;
            userSpan.appendChild(document.createTextNode(report.user_name));
            metadata.appendChild(userSpan);
        } else {
            metadata.appendChild(document.createTextNode(' • Anonymous'));
        }
        
        contentCol.appendChild(title);
        contentCol.appendChild(description);
        contentCol.appendChild(metadata);
        
        // Attachments column
        const attachmentsCol = document.createElement('div');
        attachmentsCol.className = 'col-md-3';
        if (report.attachments && report.attachments.length > 0) {
            const badge = document.createElement('span');
            badge.className = 'badge attachment-badge';
            
            // Create icon safely
            const icon = document.createElement('i');
            icon.className = 'fas fa-paperclip me-1';
            badge.appendChild(icon);
            
            // Add attachment count as text content (safe from XSS)
            const attachmentText = document.createTextNode(`${report.attachments.length} attachment${report.attachments.length !== 1 ? 's' : ''}`);
            badge.appendChild(attachmentText);
            
            attachmentsCol.appendChild(badge);
        }
        
        // Actions column
        const actionsCol = document.createElement('div');
        actionsCol.className = 'col-md-2 text-end';
        
        const viewBtn = document.createElement('button');
        viewBtn.className = 'btn btn-sm btn-outline-primary me-1';
        viewBtn.innerHTML = '<i class="fas fa-eye"></i>';
        viewBtn.addEventListener('click', () => viewReport(report.id));
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-outline-danger';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.addEventListener('click', () => confirmDelete(report.id));
        
        actionsCol.appendChild(viewBtn);
        actionsCol.appendChild(deleteBtn);
        
        // Assemble the row
        row.appendChild(checkboxCol);
        row.appendChild(contentCol);
        row.appendChild(attachmentsCol);
        row.appendChild(actionsCol);
        
        reportCard.appendChild(row);
        container.appendChild(reportCard);
    });
    
    document.getElementById('reportsContainer').style.display = 'block';
}

function viewReport(reportId) {
    const report = allReports.find(r => r.id === reportId);
    if (!report) return;
    
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    const deleteBtn = document.getElementById('deleteReportBtn');
    
    // Create title safely using DOM methods to prevent XSS
    modalTitle.innerHTML = '<i class="fas fa-bug me-2"></i>Bug Report #';
    const reportIdSpan = document.createElement('span');
    reportIdSpan.textContent = String(report.id);
    modalTitle.appendChild(reportIdSpan);
    deleteBtn.setAttribute('data-report-id', reportId);
    
    // Clear existing content first
    modalBody.innerHTML = '';
    
    // Create elements safely using DOM methods instead of innerHTML
    const titleDiv = document.createElement('div');
    titleDiv.className = 'mb-3';
    titleDiv.innerHTML = '<strong>Title:</strong>';
    const titleP = document.createElement('p');
    titleP.className = 'mt-1';
    titleP.textContent = report.title;
    titleDiv.appendChild(titleP);
    
    const descDiv = document.createElement('div');
    descDiv.className = 'mb-3';
    descDiv.innerHTML = '<strong>Description:</strong>';
    const descP = document.createElement('p');
    descP.className = 'mt-1';
    descP.textContent = report.description;
    descP.style.whiteSpace = 'pre-wrap';
    descDiv.appendChild(descP);
    
    const stepsDiv = document.createElement('div');
    stepsDiv.className = 'mb-3';
    stepsDiv.innerHTML = '<strong>AI-Parsed Reproduction Steps:</strong>';
    const stepsContent = document.createElement('div');
    stepsContent.className = 'parsed-steps bg-light text-dark p-3 rounded mt-1';
    if (report.parsed_steps) {
        stepsContent.textContent = report.parsed_steps;
        // Preserve line breaks by converting them to actual line breaks in the DOM
        stepsContent.style.whiteSpace = 'pre-wrap';
    } else {
        stepsContent.innerHTML = '<em>No steps extracted</em>';
    }
    stepsDiv.appendChild(stepsContent);
    
    const createdDiv = document.createElement('div');
    createdDiv.className = 'mb-3';
    createdDiv.innerHTML = '<strong>Created:</strong>';
    const createdP = document.createElement('p');
    createdP.className = 'mt-1';
    createdP.textContent = formatDate(report.created_at);
    createdDiv.appendChild(createdP);
    
    modalBody.appendChild(titleDiv);
    modalBody.appendChild(descDiv);
    modalBody.appendChild(stepsDiv);
    modalBody.appendChild(createdDiv);
    
    // Handle attachments safely
    if (report.attachments && report.attachments.length > 0) {
        const attachDiv = document.createElement('div');
        attachDiv.className = 'mt-3';
        
        const attachTitle = document.createElement('h6');
        attachTitle.innerHTML = '<i class="fas fa-paperclip me-2"></i>Attachments';
        attachDiv.appendChild(attachTitle);
        
        const listGroup = document.createElement('div');
        listGroup.className = 'list-group';
        
        report.attachments.forEach(att => {
            const link = document.createElement('a');
            link.href = `/reports/${report.id}/download/${att.id}`;
            link.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
            
            const leftDiv = document.createElement('div');
            leftDiv.innerHTML = '<i class="fas fa-file me-2"></i>';
            leftDiv.appendChild(document.createTextNode(att.filename));
            
            const rightSmall = document.createElement('small');
            rightSmall.className = 'text-muted';
            rightSmall.textContent = formatFileSize(att.file_size);
            
            link.appendChild(leftDiv);
            link.appendChild(rightSmall);
            listGroup.appendChild(link);
        });
        
        attachDiv.appendChild(listGroup);
        modalBody.appendChild(attachDiv);
    }
    
    const modal = new bootstrap.Modal(document.getElementById('reportModal'));
    modal.show();
}

function filterReports() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    if (!searchTerm) {
        filteredReports = [...allReports];
    } else {
        filteredReports = allReports.filter(report =>
            report.title.toLowerCase().includes(searchTerm) ||
            report.description.toLowerCase().includes(searchTerm)
        );
    }
    
    displayReports(filteredReports);
}

function toggleSelection(reportId) {
    if (selectedReports.has(reportId)) {
        selectedReports.delete(reportId);
    } else {
        selectedReports.add(reportId);
    }
    
    const deleteBtn = document.getElementById('deleteSelectedBtn');
    deleteBtn.style.display = selectedReports.size > 0 ? 'inline-block' : 'none';
}

async function deleteReport(reportId) {
    if (!confirm('Are you sure you want to delete this bug report? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/reports/${reportId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('Bug report deleted successfully');
            loadReports(currentPage);
        } else {
            showError('Failed to delete report: ' + data.error);
        }
    } catch (error) {
        console.error('Error deleting report:', error);
        showError('Network error while deleting report');
    }
}

function confirmDelete(reportId) {
    deleteReport(reportId);
}

async function deleteSelected() {
    if (selectedReports.size === 0) return;
    
    if (!confirm(`Are you sure you want to delete ${selectedReports.size} selected report(s)? This action cannot be undone.`)) {
        return;
    }
    
    const promises = Array.from(selectedReports).map(id => 
        fetch(`/reports/${id}`, { method: 'DELETE' })
    );
    
    try {
        await Promise.all(promises);
        showSuccess(`${selectedReports.size} report(s) deleted successfully`);
        selectedReports.clear();
        loadReports(currentPage);
    } catch (error) {
        console.error('Error deleting reports:', error);
        showError('Error deleting some reports');
        loadReports(currentPage); // Refresh to show current state
    }
}

function refreshReports() {
    selectedReports.clear();
    loadReports(currentPage);
}

function updatePagination() {
    const container = document.getElementById('paginationContainer');
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    let paginationHtml = '';
    
    // Previous button
    const prevDisabled = currentPage === 1 ? 'disabled' : '';
    paginationHtml += `
        <li class="page-item ${prevDisabled}">
            <a class="page-link" href="#" onclick="loadReports(${currentPage - 1}); return false;">Previous</a>
        </li>
    `;
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage || Math.abs(i - currentPage) <= 2 || i === 1 || i === totalPages) {
            const activeClass = i === currentPage ? 'active' : '';
            paginationHtml += `
                <li class="page-item ${activeClass}">
                    <a class="page-link" href="#" onclick="loadReports(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (Math.abs(i - currentPage) === 3) {
            paginationHtml += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }
    
    // Next button
    const nextDisabled = currentPage === totalPages ? 'disabled' : '';
    paginationHtml += `
        <li class="page-item ${nextDisabled}">
            <a class="page-link" href="#" onclick="loadReports(${currentPage + 1}); return false;">Next</a>
        </li>
    `;
    
    pagination.innerHTML = paginationHtml;
}

// Utility functions
function showLoading(show) {
    document.getElementById('loadingSpinner').style.display = show ? 'block' : 'none';
    document.getElementById('reportsContainer').style.display = show ? 'none' : 'block';
}

function showError(message) {
    // Simple alert for now - could be enhanced with toast notifications
    alert('Error: ' + message);
}

function showSuccess(message) {
    // Simple alert for now - could be enhanced with toast notifications
    alert('Success: ' + message);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}};
}