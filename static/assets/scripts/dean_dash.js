const dashboardDeanName = document.getElementById('dashboardDeanName');
const deanFullNameEl = document.getElementById('deanFullName');
const deanDepartmentEl = document.getElementById('deanDepartment');
const deanPhotoEl = document.getElementById('deanPhoto');
const deanNameHeader = document.getElementById('deanName');
const deanAvatarEl = document.getElementById('deanAvatar');

const facultyChartContainer = document.getElementById('facultyChartContainer');
const leaveRequestsContainer = document.querySelector('.leave-requests-container');
const leaveReportsContainer = document.querySelector('.leave-reports-cards-container');
const logoutModal = document.getElementById('logoutModal');

const prof_Section = document.getElementById('modal_hidden_div');

let currentDeanData = null;

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

async function viewProfile() {
    const profileDiv = document.querySelector('.dean-info-div');

    if (!profileDiv) return;

    if (!currentDeanData) {
        alert('Dean data is not loaded yet. Please wait...');
        return;
    }

    profileDiv.style.display = 'block';

    const dean = currentDeanData;
    const defaultPhoto = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Crect fill='%23800020' width='120' height='120'/%3E%3Ctext fill='%23fff' font-size='60' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3ED%3C/text%3E%3C/svg%3E";
    
    document.getElementById('profileFullName').value = dean.full_name || '';
    document.getElementById('profileDepartment').textContent = dean.department_name || '—';
    document.getElementById('profileUsername').value = dean.username || '';
    document.getElementById('profileGender').value = dean.gender || '';
    document.getElementById('profileAge').value = dean.age || '';
    document.getElementById('profileHeight').value = dean.height || '';
    document.getElementById('profileWeight').value = dean.weight || '';
    document.getElementById('profilePassword').value = '';
    document.getElementById('profilePhotoPreview').src = dean.photo_url || defaultPhoto;
}

document.getElementById('closeDeanModal')?.addEventListener('click', function() {
    const profileDiv = document.querySelector('.dean-info-div');
    
    if (profileDiv) profileDiv.style.display = 'none';
});

document.getElementById('deanName')?.addEventListener('click', function(e) {
    e.stopPropagation();
    const modal_cont = document.getElementById("modal_cont");
    const dropdown = document.getElementById('deanDropdown');

    const isOpen = dropdown.style.display === 'block';
    dropdown.style.display = isOpen ? 'none' : 'block';
    modal_cont.style.display = isOpen ? 'none' : 'block';
});

document.addEventListener('click', function(event) {
    const modal_cont = document.getElementById("modal_cont");
    const dropdown = document.getElementById('deanDropdown');
    const trigger = document.getElementById('deanName');

    if (trigger && !trigger.contains(event.target) && modal_cont && !modal_cont.contains(event.target)) {
        dropdown.style.display = 'none';
        modal_cont.style.display = 'none';
    }
});

document.getElementById('profilePhotoInput')?.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
            document.getElementById('profilePhotoPreview').src = ev.target.result;
        };
        reader.readAsDataURL(file);
    }
});

document.getElementById('deanProfileForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const confirmed = window.confirm(
        "Are you sure you want to update your profile? You will be logged out and redirected to the login page."
    );
    if (!confirmed) {
        return;
    }

    if (!currentDeanData || !currentDeanData.id) {
        alert('Dean ID is not available.');
        return;
    }

    const formData = new FormData();
    formData.append('full_name', document.getElementById('profileFullName').value);
    formData.append('gender', document.getElementById('profileGender').value);
    formData.append('age', document.getElementById('profileAge').value);
    formData.append('height', document.getElementById('profileHeight').value);
    formData.append('weight', document.getElementById('profileWeight').value);
    formData.append('department', currentDeanData.department);

    const password = document.getElementById('profilePassword').value;
    if (password) {
        formData.append('password', password);
    }

    const username = document.getElementById('profileUsername').value;
    if (username) {
        formData.append('username', username);
    }

    const photoFile = document.getElementById('profilePhotoInput').files[0];
    if (photoFile) {
        formData.append('photo', photoFile);
    }

    formData.append('is_active', 'true');

    try {
        prof_Section.style.display = 'none';
        showModal(logoutModal);
        const response = await fetch(`/api/deans/${currentDeanData.id}/`, {
            method: 'PUT',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            alert('Profile updated successfully! You will now be logged out and redirected to the login page.');

            const logoutRes = await fetch('/dean_logout/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
            const logoutData = await logoutRes.json();

            if (logoutData.success && logoutData.redirect_url) {
                setTimeout(() => {
                    window.location.href = logoutData.redirect_url;
                }, 1000);
            } else {
                alert('Logout failed. Please log in again manually.');
            }
        } else {
            alert('Failed to update profile: ' + (result.message || 'Unknown error'));
        }
    } catch (error) {
        //console.error('Error updating profile:', error);
        alert('An error occurred while updating the profile.');
    } finally {
        hideModal(logoutModal);
    }
});

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
    const confirmed = window.confirm("You'll be redirected to starting page, and you'll need to login again?");
    if (!confirmed) {
        return;
    }

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
        showModal(logoutModal);
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
        currentDeanData = dean;

        const defaultPhoto = "static/assets/media/examplePIC.jpg";

        if (dashboardDeanName) dashboardDeanName.textContent = dean.full_name || 'N/A';
        if (deanFullNameEl) deanFullNameEl.textContent = dean.full_name || 'N/A';
        if (deanDepartmentEl) deanDepartmentEl.textContent = dean.department_name || 'N/A';
        if (deanPhotoEl) deanPhotoEl.src = dean.photo_url || defaultPhoto;
        if (deanAvatarEl) deanAvatarEl.src = dean.photo_url || defaultPhoto;
        if (deanNameHeader) deanNameHeader.textContent = dean.full_name ? dean.full_name + ' ▾' : 'N/A';

        if (dean.department) {
            await Promise.all([
                loadFacultyStaff(dean.department).catch(err => {
                    console.error('Error loading faculty:', err);
                    facultyChartContainer.innerHTML = '<p class="loading-text">Failed to load faculty & staff.</p>';
                }),
                loadLeaveRequests(dean.department_name || dean.department).catch(err => {
                    console.error('Error loading leave requests:', err);
                    leaveRequestsContainer.innerHTML = '<p class="loading-text">Failed to load leave requests.</p>';
                }),
                loadLeaveReports(dean.department).catch(err => {
                    console.error('Error loading leave reports:', err);
                    leaveReportsContainer.innerHTML = '<p class="loading-text">Failed to load leave reports.</p>';
                })
            ]);
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
    } finally {
        hideModal(logoutModal);
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
            card.style.maxWidth = '500px';
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

        //console.log("Raw reports data:", data);

        if (!data || data.length === 0) {
            leaveReportsContainer.innerHTML = '<p class="loading-text">No leave reports in your department</p>';
            return;
        }

        const filteredReports = data.filter(report => 
            ['dean_approved', 'dean_denied', 'approved', 'denied'].includes(report.status)
        );

        if (filteredReports.length === 0) {
            leaveReportsContainer.innerHTML = '<p class="loading-text">No reviewed leave reports in your department</p>';
            return;
        }

        leaveReportsContainer.innerHTML = '';

        filteredReports.forEach(report => {
            const app = report.application || {};
            const card = document.createElement('div');
            card.classList.add('leave-report-card');

            let statusText = '';
            let statusClass = '';
            let approvalSection = '';

            switch(report.status) {
                case 'dean_approved':
                    statusText = 'Dean Approved (Pending HR)';
                    statusClass = 'status-dean_approved';
                    approvalSection = `
                        <div class="report-row">
                            <span class="report-label">Dean Reviewer</span>
                            <span class="report-value">${report.dean_reviewer_name || 'N/A'}</span>
                        </div>
                        <div class="report-row">
                            <span class="report-label">Dean Reviewed At</span>
                            <span class="report-value">${formatDateTime(report.dean_reviewed_at)}</span>
                        </div>
                        ${report.dean_comments ? `
                        <div class="report-row full-width">
                            <span class="report-label">Dean Comments</span>
                            <span class="report-value">${report.dean_comments}</span>
                        </div>
                        ` : ''}
                        <div class="report-row full-width">
                            <span class="report-label">HR Status</span>
                            <span class="report-value" style="color: #FF9800; font-weight: bold;">⏳ Pending HR Approval</span>
                        </div>
                    `;
                    break;

                case 'dean_denied':
                    statusText = 'Denied by Dean';
                    statusClass = 'status-dean_denied';
                    approvalSection = `
                        <div class="report-row">
                            <span class="report-label">Dean Reviewer</span>
                            <span class="report-value">${report.dean_reviewer_name || 'N/A'}</span>
                        </div>
                        <div class="report-row">
                            <span class="report-label">Dean Reviewed At</span>
                            <span class="report-value">${formatDateTime(report.dean_reviewed_at)}</span>
                        </div>
                        <div class="report-row full-width">
                            <span class="report-label">Denial Reason</span>
                            <span class="report-value" style="color: #f44336; font-weight: bold;">${report.dean_comments || 'No reason provided'}</span>
                        </div>
                    `;
                    break;

                case 'approved':
                    statusText = 'Approved by HR';
                    statusClass = 'status-approved';
                    approvalSection = `
                        <div class="approval-group" style="background: #e8f5e9; padding: 15px; border-radius: 6px; margin-bottom: 10px;">
                            <h4 style="margin: 0 0 10px 0; color: #2e7d32; font-size: 14px;">✓ APPROVED BY DEAN</h4>
                            <div class="report-row">
                                <span class="report-label">Reviewed At</span>
                                <span class="report-value">${formatDateTime(report.dean_reviewed_at)}</span>
                            </div>
                            ${report.dean_comments ? `
                            <div class="report-row full-width">
                                <span class="report-label">Comments</span>
                                <span class="report-value">${report.dean_comments}</span>
                            </div>
                            ` : ''}
                        </div>
                        <div class="approval-group" style="background: #e8f5e9; padding: 15px; border-radius: 6px;">
                            <h4 style="margin: 0 0 10px 0; color: #2e7d32; font-size: 14px;">✓ APPROVED BY HR</h4>
                            <div class="report-row">
                                <span class="report-label">Reviewed At</span>
                                <span class="report-value">${formatDateTime(report.hr_reviewed_at)}</span>
                            </div>
                            ${report.hr_comments ? `
                            <div class="report-row full-width">
                                <span class="report-label">Comments</span>
                                <span class="report-value">${report.hr_comments}</span>
                            </div>
                            ` : ''}
                        </div>
                    `;
                    break;

                case 'denied':
                    statusText = 'Denied by HR';
                    statusClass = 'status-denied';
                    approvalSection = `
                        <div class="approval-group" style="background: #e8f5e9; padding: 15px; border-radius: 6px; margin-bottom: 10px;">
                            <h4 style="margin: 0 0 10px 0; color: #2e7d32; font-size: 14px;">✓ APPROVED BY DEAN</h4>
                            <div class="report-row">
                                <span class="report-label">Reviewed At</span>
                                <span class="report-value">${formatDateTime(report.dean_reviewed_at)}</span>
                            </div>
                            ${report.dean_comments ? `
                            <div class="report-row full-width">
                                <span class="report-label">Comments</span>
                                <span class="report-value">${report.dean_comments}</span>
                            </div>
                            ` : ''}
                        </div>
                        <div class="approval-group" style="background: #ffebee; padding: 15px; border-radius: 6px;">
                            <h4 style="margin: 0 0 10px 0; color: #c62828; font-size: 14px;">✗ DENIED BY HR</h4>
                            <div class="report-row">
                                <span class="report-label">Reviewed At</span>
                                <span class="report-value">${formatDateTime(report.hr_reviewed_at)}</span>
                            </div>
                            <div class="report-row full-width">
                                <span class="report-label">Denial Reason</span>
                                <span class="report-value" style="color: #f44336; font-weight: bold;">${report.hr_comments || 'No reason provided'}</span>
                            </div>
                        </div>
                    `;
                    break;

                default:
                    statusText = report.status_display || report.status;
                    statusClass = `status-${report.status}`;
            }
            let deleteButton = '';
            if (report.status === 'dean_denied') {
                deleteButton = `
                    <div class="report-actions">
                        <button class="delete-btn" 
                                data-id="${report.id}" 
                                data-department="${app.department_name || ''}"
                                style="background:#f44336; color:white; border:none; 
                                    padding:8px 14px; border-radius:6px; 
                                    font-size:14px; cursor:pointer; 
                                    display:flex; align-items:center; justify-content:center; gap:6px; 
                                    transition:background 0.3s ease; width:100%; position:relative; top:15px;">
                            <span class="btn-icon">🗑</span> Delete
                        </button>
                    </div>
                `;
            }

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
                        <span class="report-label">Department</span>
                        <span class="report-value">${app.department_name || 'N/A'}</span>
                    </div>
                    <div class="report-row">
                        <span class="report-label">Position</span>
                        <span class="report-value">${app.position_title || 'N/A'}</span>
                    </div>
                    <div class="report-row">
                        <span class="report-label">Leave Type</span>
                        <span class="report-value">${app.leave_type || 'N/A'}</span>
                    </div>
                    <div class="report-row">
                        <span class="report-label">Duration</span>
                        <span class="report-value">${app.number_of_days || 0} day(s)</span>
                    </div>
                    <div class="report-row">
                        <span class="report-label">Date Filed</span>
                        <span class="report-value">${formatDate(app.date_filed)}</span>
                    </div>
                    <div class="report-row full-width">
                        <span class="report-label">Reason</span>
                        <span class="report-value">${app.reason || 'N/A'}</span>
                    </div>
                    
                    ${approvalSection}
                    ${deleteButton} 
                </div>
            `;

            leaveReportsContainer.appendChild(card);
        });
        

        leaveReportsContainer.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const reportId = btn.dataset.id;
                const deptName = btn.dataset.department;

                if (deptName) {
                    localStorage.setItem('deptName', deptName);
                }

                deleteLeaveReport(reportId);
            });
        });


    } catch (err) {
        console.error('Error fetching leave reports:', err);
        leaveReportsContainer.innerHTML = '<p class="loading-text">Failed to load leave reports.</p>';
    }
}

function formatDate(dateStr) {
    if (!dateStr || dateStr === 'N/A') return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
}

function formatDateTime(dateStr) {
    if (!dateStr || dateStr === 'N/A') return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
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

        //console.log("Raw requests data:", data);

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

async function handleLeaveAction(leaveId, action) {
    const comments = action === 'deny' ? prompt('Enter denial comments (optional):') || '' : '';

    const confirmed = confirm(`Are you sure you want to ${action} this leave request?`);
    if (!confirmed) return;

    const actionMap = {
        approve: 'dean_approve', 
        deny: 'dean_deny'    
    };

    const endpoint = actionMap[action];
    if (!endpoint) {
        alert('Invalid action');
        return;
    }

    const url = `/api/leave-requests/${leaveId}/${endpoint}/`;

    try {
        const res = await fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ comments })
        });

        if (!res.ok) {
            const text = await res.text(); 
            throw new Error(`HTTP error ${res.status} - ${text}`);
        }

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
        showModal(logoutModal);

        const res = await fetch(`/api/leave-requests/${reportId}/delete-if-denied/`, {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (res.ok) {
            const result = await res.json();
            //console.log("Delete response:", result); ..pang debug lng

            const deptName = localStorage.getItem('deptName');
            if (deptName) {
                loadLeaveReports(deptName);
                localStorage.removeItem('deptName');
            }
        } else {
            let errorMessage = "Failed to delete report. Please try again.";
            try {
                const result = await res.json();
                errorMessage = result.error || errorMessage;
            } catch (e) {
            }
            alert(errorMessage);
        }
    } catch (err) {
        //console.error("Fetch error:", err); ..pang debug lng
        alert("Error deleting report. Please try again.");
    } finally {
        hideModal(logoutModal);
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
