const dashboardDeanName = document.getElementById('dashboardDeanName');
const deanFullNameEl = document.getElementById('deanFullName');
const deanDepartmentEl = document.getElementById('deanDepartment');
const deanGenderEl = document.getElementById('deanGender');
const deanAgeEl = document.getElementById('deanAge');
const deanHeightEl = document.getElementById('deanHeight');
const deanWeightEl = document.getElementById('deanWeight');
const deanPhotoEl = document.getElementById('deanPhoto');
const deanNameHeader = document.getElementById('deanName');
const deanAvatarEl = document.getElementById('deanAvatar');

const facultyChartContainer = document.getElementById('facultyChartContainer');
const leaveRequestsContainer = document.querySelector('.leave-requests-container');
const leaveReportsContainer = document.querySelector('.leave-reports-cards-container');

const base_url = 'https://kt2980zx-8000.asse.devtunnels.ms/';

const logoutModal = document.getElementById('logoutModal');

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showModal(modal) {
    if (modal) modal.classList.remove('hidden');
}

function hideModal(modal) {
    if (modal) modal.classList.add('hidden');
}

function switchSection(sectionId, menuItem) {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.add('hidden-section');
    });

    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.remove('hidden-section');
    }

    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });
    if (menuItem) menuItem.classList.add('active');

    const sectionName = menuItem ? menuItem.textContent.trim().split(' ').slice(1).join(' ') : 'Dashboard';
    document.getElementById('breadcrumb').textContent = `📁 ${sectionName}`;
}

async function logoutDean() {
    showModal(logoutModal);
    try {
        const res = await fetch('/dean_logout/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        const data = await res.json();
        if (data.success && data.redirect_url) {
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1000);
        } else {
            console.error('Logout failed:', data.message || 'Unknown error');
            hideModal(logoutModal);
            alert('Logout failed. Please try again.');
        }
    } catch (err) {
        console.error('Logout failed:', err);
        hideModal(logoutModal);
        alert('Network error. Please try again.');
    }
}

async function loadDeanInfo() {
    try {
        const res = await fetch('/api/deans/me/', {
            method: 'GET',
            credentials: 'same-origin',
            headers: { 
                'Content-Type': 'application/json', 
                'X-CSRFToken': getCookie('csrftoken') 
            }
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.message || 'Failed to fetch dean info');

        const dean = data.data;

        dashboardDeanName.textContent = dean.full_name || 'N/A';
        deanFullNameEl.textContent = dean.full_name || 'N/A';
        deanDepartmentEl.textContent = dean.department_name || 'N/A';
        deanGenderEl.textContent = dean.gender || 'N/A';
        deanAgeEl.textContent = dean.age || 'N/A';
        deanHeightEl.textContent = dean.height || 'N/A';
        deanWeightEl.textContent = dean.weight || 'N/A';
        
        const photoUrl = dean.photo_url || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Crect fill='%23800020' width='120' height='120'/%3E%3Ctext fill='%23fff' font-size='60' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3ED%3C/text%3E%3C/svg%3E";
        deanPhotoEl.src = photoUrl || `${base_url}/static/assets/media/examplePIC.jpg`;
        deanAvatarEl.src = photoUrl || `${base_url}/static/assets/media/examplePIC.jpg`;
        deanNameHeader.textContent = dean.full_name + ' ▾';

        if (dean.department) {
            await loadFacultyStaff(dean.department);
            await loadLeaveRequests(dean.department_name || dean.department);
            await loadLeaveReports(dean.department);
        } else {
            facultyChartContainer.innerHTML = '<p class="loading-text">Department info unavailable</p>';
            leaveRequestsContainer.innerHTML = '<p class="loading-text">Department info unavailable</p>';
            leaveReportsContainer.innerHTML = '<p class="loading-text">Department info unavailable</p>';
        }

    } catch (err) {
        console.error('Error loading dean info:', err);
        facultyChartContainer.innerHTML = '<p class="loading-text">Failed to load faculty & staff.</p>';
        leaveRequestsContainer.innerHTML = '<p class="loading-text">Failed to load leave requests.</p>';
        leaveReportsContainer.innerHTML = '<p class="loading-text">Failed to load leave reports.</p>';
    }
}

async function loadFacultyStaff(departmentId) {
    try {
        facultyChartContainer.innerHTML = '<p class="loading-text">Loading faculty & staff...</p>';
        const res = await fetch(`/api/employees/?department=${departmentId}&is_active=true`, {
            method: 'GET',
            credentials: 'same-origin'
        });
        const data = await res.json();

        const employees = data.success ? data.data : (Array.isArray(data) ? data : []);
        
        if (employees.length === 0) {
            facultyChartContainer.innerHTML = '<p class="loading-text">No faculty/staff found in your department.</p>';
            return;
        }

        facultyChartContainer.innerHTML = '';
        facultyChartContainer.classList.add('org-chart');

        employees.forEach(emp => {
            const card = document.createElement('div');
            card.classList.add('org-card');
            const photoUrl = emp.photo_url || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Crect fill='%23800020' width='120' height='120'/%3E%3Ctext fill='%23fff' font-size='60' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3E" + (emp.full_name ? emp.full_name.charAt(0) : 'E') + "%3C/text%3E%3C/svg%3E";
            card.innerHTML = `
                <div class="org-avatar"><img src="${photoUrl}" alt="${emp.full_name || 'N/A'}"></div>
                <div class="org-title">${emp.full_name || 'N/A'}</div>
                <div class="org-subtitle">${emp.position_title || 'N/A'}</div>
            `;
            facultyChartContainer.appendChild(card);
        });

    } catch (err) {
        console.error('Error fetching faculty/staff:', err);
        facultyChartContainer.innerHTML = '<p class="loading-text">Failed to load faculty & staff.</p>';
    }
}

async function loadLeaveRequests(departmentName) {
    const leaveRequestsContainer = document.querySelector('#leaveRequestsSection .leave-requests-container');
    if (!leaveRequestsContainer) return;

    try {
        leaveRequestsContainer.innerHTML = '<p class="loading-text">Loading leave requests...</p>';

        const encodedDept = encodeURIComponent(departmentName);
        const res = await fetch(`/api/leave-requests/?department=${encodedDept}&view=requests`, {
            method: 'GET',
            credentials: 'same-origin'
        });
        const data = await res.json();

        console.log("Raw requests data:", data);

        if (!data || data.length === 0) {
            leaveRequestsContainer.innerHTML = '<p class="loading-text">No pending leave requests in your department</p>';
            return;
        }

        leaveRequestsContainer.innerHTML = '';

        data.forEach(req => {
            const app = req.application || {};
            const card = document.createElement('div');
            card.classList.add('leave-request-card');

            const photoUrl = app.employee_photo_url || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Crect fill='%23800020' width='60' height='60'/%3E%3Ctext fill='%23fff' font-size='30' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3E" + (app.employee_name ? app.employee_name.charAt(0) : 'E') + "%3C/text%3E%3C/svg%3E";

            card.innerHTML = `
                <div class="request-header">
                    <img src="${photoUrl}" alt="${app.employee_name}" class="employee-avatar">
                    <div class="employee-info">
                        <div class="employee-name">${app.employee_name || 'N/A'}</div>
                        <div class="employee-id">${app.employee_id_display || 'N/A'}</div>
                    </div>
                    <span class="status-badge status-pending">Pending Dean Approval</span>
                </div>
                <div class="request-body">
                    <div class="request-info-row">
                        <span class="info-label">Leave Type:</span>
                        <span class="info-value">${app.leave_type || 'N/A'}</span>
                    </div>
                    <div class="request-info-row">
                        <span class="info-label">Duration:</span>
                        <span class="info-value">${app.number_of_days || 0} day(s)</span>
                    </div>
                    <div class="request-info-row full-width">
                        <span class="info-label">Reason:</span>
                        <span class="info-value">${app.reason || 'N/A'}</span>
                    </div>
                </div>
                <div class="request-actions">
                    <button class="approve-btn" data-id="${req.id}">
                        <span class="btn-icon">✓</span> Approve
                    </button>
                    <button class="deny-btn" data-id="${req.id}">
                        <span class="btn-icon">✕</span> Deny
                    </button>
                </div>
            `;

            leaveRequestsContainer.appendChild(card);
        });

        leaveRequestsContainer.querySelectorAll('.approve-btn').forEach(btn => {
            btn.addEventListener('click', () => handleLeaveAction(btn.dataset.id, 'approve'));
        });
        leaveRequestsContainer.querySelectorAll('.deny-btn').forEach(btn => {
            btn.addEventListener('click', () => handleLeaveAction(btn.dataset.id, 'deny'));
        });

    } catch (err) {
        console.error('Error fetching leave requests:', err);
        leaveRequestsContainer.innerHTML = '<p class="loading-text">Failed to load leave requests.</p>';
    }
}

async function loadLeaveReports(departmentName) {
    const leaveReportsContainer = document.querySelector('#leaveReportsSection .leave-reports-cards-container');
    if (!leaveReportsContainer) return;

    try {
        leaveReportsContainer.innerHTML = '<p class="loading-text">Loading leave reports...</p>';

        const encodedDept = encodeURIComponent(departmentName);
        const res = await fetch(`/api/leave-requests/?department=${encodedDept}&view=reports`, {
            method: 'GET',
            credentials: 'same-origin'
        });
        const data = await res.json();

        console.log("Raw reports data:", data);

        if (!data || data.length === 0) {
            leaveReportsContainer.innerHTML = '<p class="loading-text">No leave reports in your department</p>';
            return;
        }

        leaveReportsContainer.innerHTML = '';

        data.forEach(report => {
            const app = report.application || {};
            const card = document.createElement('div');
            card.classList.add('leave-report-card');

            const statusText = report.status === "dean_approved" ? "Dean Approved" : "Dean Denied";
            const statusClass = `status-${report.status}`;

            const actions = document.createElement('div');
                actions.classList.add('report-actions');
                actions.innerHTML = `
                    <button class="delete-btn" data-id="${report.id}">
                        <span class="btn-icon">🗑</span> Delete
                    </button>
                `;
                card.appendChild(actions);

            card.innerHTML = `
                <div class="report-header">
                    <div class="report-employee">
                        <div class="report-name">${app.employee_name || 'N/A'}</div>
                        <div class="report-id">ID: ${app.employee_id_display || 'N/A'}</div>
                    </div>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                <div class="report-body">
                    <div class="report-row">
                        <span class="report-label">Leave Type</span>
                        <span class="report-value">${app.leave_type || 'N/A'}</span>
                    </div>
                    <div class="report-row">
                        <span class="report-label">Duration</span>
                        <span class="report-value">${app.number_of_days || 0} day(s)</span>
                    </div>
                    <div class="report-row full-width">
                        <span class="report-label">Reason</span>
                        <span class="report-value">${app.reason || 'N/A'}</span>
                    </div>
                    <div class="report-row">
                        <span class="report-label">Dean Reviewer</span>
                        <span class="report-value">${report.dean_reviewer_name || 'N/A'}</span>
                    </div>
                    <div class="report-row full-width">
                        <span class="report-label">Dean Comments</span>
                        <span class="report-value">${report.dean_comments || 'N/A'}</span>
                    </div>
                </div>
            `;

            leaveReportsContainer.appendChild(card);
            
            leaveReportsContainer.querySelectorAll('.delete-btn').forEach(btn => {
                btn.addEventListener('click', () => deleteLeaveReport(btn.dataset.id));
            });

        });

    } catch (err) {
        console.error('Error fetching leave reports:', err);
        leaveReportsContainer.innerHTML = '<p class="loading-text">Failed to load leave reports.</p>';
    }
}

async function handleLeaveAction(leaveId, action) {
    const comments = action === 'deny' ? prompt('Enter denial comments (optional):') || '' : '';
    
    const confirmed = confirm(`Are you sure you want to ${action} this leave request?`);
    if (!confirmed) return;

    try {
        const res = await fetch(`/api/leave-requests/${leaveId}/dean_${action}/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ comments })
        });

        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();

        if (data.success) {
            const pastTense = action === 'approve' ? 'approved' : 'denied';
            alert(data.message || `Leave request ${pastTense} successfully!`);
            await loadDeanInfo();
        } else {
            alert('Action failed: ' + (data.message || 'Unknown error'));
        }
    } catch (err) {
        console.error(`Error on ${action}:`, err);
        alert('Error performing action. Please try again.');
    }
}

async function deleteLeaveReport(reportId) {
    if (!confirm("Are you sure you want to delete this report?")) return;

    try {
        const res = await fetch(`/api/leave-requests/${reportId}/`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });

        if (res.ok) {
            //console.log(`Report ${reportId} deleted successfully`);
            const deptName = document.querySelector('#leaveReportsSection').dataset.department;
            loadLeaveReports(deptName);
        } else {
            console.error(`Failed to delete report ${reportId}`, res.status);
            alert("Failed to delete report. Please try again.");
        }
    } catch (err) {
        //console.error('Error deleting report:', err);
        alert("Error deleting report. Please try again.");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.menu-item[data-section]').forEach(item => {
        item.addEventListener('click', () => switchSection(item.dataset.section, item));
    });

    document.getElementById('logoutBtn').addEventListener('click', logoutDean);
    switchSection('dashboardSection', document.querySelector('.menu-item[data-section="dashboardSection"]'));
    loadDeanInfo();
});