const CONFIG = {
  // Development URL - replace with production URL when deploying
  DEV_URL: "https://kt2980zx-8000.asse.devtunnels.ms",
  PROD_URL: "",
  
  get API_BASE() {
    return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      ? this.DEV_URL 
      : this.PROD_URL || this.DEV_URL;
  }
};

const API_BASE = CONFIG.API_BASE;

let allEmployees = [];
let allDepartments = [];
let allPositions = [];
let currentPhotoFile = null;
let currentHRUser = null;

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');

document.addEventListener('DOMContentLoaded', function() {
  initializeDashboard();
  setupEventListeners();
});

async function initializeDashboard() {
  try {
    showLoader();
    await loadHRProfile();
    await loadDepartments();
    await loadPositions();
    await loadEmployees();
    await loadLeaveRequests();
    await loadLeaveReports();
    populateOrgChart();
  } catch (error) {
    console.error('Error initializing dashboard:', error);
    showError('Failed to initialize dashboard. Please refresh the page.');
  } finally {
    hideLoader();
  }
}

// Setup event listeners
function setupEventListeners() {
  document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', function() {
      const section = this.getAttribute('data-section');
      if (section) {
        switchSection(section, this);
      }
    });
  });

  const addEmployeeBtn = document.querySelector('.btn-primary');
  const updateEmployeeBtn = document.querySelector('.btn-secondary');
  const employeeForm = document.getElementById('employeeForm');
  
  if (addEmployeeBtn) addEmployeeBtn.addEventListener('click', openAddEmployeeModal);
  if (updateEmployeeBtn) updateEmployeeBtn.addEventListener('click', openUpdateModal);
  if (employeeForm) employeeForm.addEventListener('submit', handleEmployeeSubmit);
  
  const adminProfile = document.getElementById('adminProfile');
  if (adminProfile) {
    adminProfile.addEventListener('click', function(e) {
      e.stopPropagation();
      const dropdown = document.getElementById('adminDropdown');
      if (dropdown) dropdown.classList.toggle('hidden');
    });
  }

  document.addEventListener('click', function() {
    const dropdown = document.getElementById('adminDropdown');
    if (dropdown && !dropdown.classList.contains('hidden')) {
      dropdown.classList.add('hidden');
    }
  });
  
  const deptForm = document.getElementById('departmentForm');
  const posForm = document.getElementById('positionForm');
  const hrForm = document.getElementById('hrForm');
  
  if (deptForm) deptForm.addEventListener('submit', handleDepartmentSubmit);
  if (posForm) posForm.addEventListener('submit', handlePositionSubmit);
  if (hrForm) hrForm.addEventListener('submit', handleHRProfileSubmit);
}

function showLoader() {
  const loader = document.getElementById('globalLoadingModal');
  if (loader) loader.style.display = 'flex';
}

function hideLoader() {
  const loader = document.getElementById('globalLoadingModal');
  if (loader) loader.style.display = 'none';
}

function showError(message) {
  console.error(message);
  alert(message);
}

function showSuccess(message) {
  console.log(message);
  alert(message);
}

async function loadHRProfile() {
  try {
    const hrUsername = sessionStorage.getItem('hrUsername') || "@OsmeñaVerified_HR";
    
    const response = await fetch(`${API_BASE}/api/hruser/${encodeURIComponent(hrUsername)}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      }
    });

    if (!response.ok) {
      console.warn('HR profile not found');
      document.getElementById('hrProfessionalId').textContent = 'Not Found';
      document.getElementById('hrUsername').value = hrUsername;
      return;
    }

    const hrData = await response.json();
    currentHRUser = hrData;
    updateHRProfileUI(hrData);
    
  } catch (error) {
    console.error('Error loading HR profile:', error);
    showError('Failed to load HR profile');
  }
}

function updateHRProfileUI(hrData) {
  const fields = {
    'hrUsername': hrData.username || '',
    'hrFullName': hrData.full_name || '',
    'hrGender': hrData.gender || '',
    'hrHeight': hrData.height || '',
    'hrWeight': hrData.weight || '',
    'hrAge': hrData.age || '',
    'hrProfessionalId': "OC-HR-2026237" + hrData.id || 'N/A'
  };

  for (const [fieldId, value] of Object.entries(fields)) {
    const element = document.getElementById(fieldId);
    if (element) {
      if (fieldId === 'hrProfessionalId') {
        element.textContent = value;
      } else {
        element.value = value;
      }
    }
  }

  const photoUrl = hrData.photo_url || '/static/assets/media/examplePIC.jpg';
  const avatarElements = [
    document.getElementById('hrAvatar'),
    document.getElementById('hrProfilePic')
  ];
  
  avatarElements.forEach(el => {
    if (el) {
      el.src = photoUrl;
      el.onerror = function() {
        this.src = '/static/assets/media/examplePIC.jpg';
      };
    }
  });
}

function toggleHRModal() {
  const modal = document.getElementById('hrModal');
  if (!modal) return;
  
  if (modal.style.display === 'flex') {
    modal.style.display = 'none';
  } else {
    modal.style.display = 'flex';
    if (!currentHRUser) {
      loadHRProfile();
    } else {
      updateHRProfileUI(currentHRUser);
    }
  }
}

async function handleHRProfileSubmit(e) {
  e.preventDefault();
  showLoader();

  const formData = new FormData();
  const hrUsername = document.getElementById('hrUsername').value;

  formData.append('full_name', document.getElementById('hrFullName').value);
  formData.append('gender', document.getElementById('hrGender').value);
  formData.append('height', document.getElementById('hrHeight').value);
  formData.append('weight', document.getElementById('hrWeight').value);
  formData.append('age', document.getElementById('hrAge').value);

  const newPassword = document.getElementById('hrPassword').value;
  if (newPassword && newPassword.trim() !== '') {
    formData.append('password', newPassword);
  }

  const photoFile = document.getElementById('hrPhoto').files[0];
  if (photoFile) {
    formData.append('photo', photoFile);
  }

  try {
    const response = await fetch(`${API_BASE}/api/hruser/${encodeURIComponent(hrUsername)}/`, {
      method: 'PUT',
      headers: {
        'X-CSRFToken': csrftoken
      },
      body: formData
    });

    const result = await response.json();
    
    if (response.ok) {
      showSuccess('HR profile updated successfully!');
      toggleHRModal();
      updateHRProfileUI(result);
      document.getElementById('hrPassword').value = '';
    } else {
      showError('Error: ' + (result.message || JSON.stringify(result)));
    }
  } catch (error) {
    console.error('Error updating HR profile:', error);
    showError('Failed to update HR profile.');
  } finally {
    hideLoader();
  }
}

async function loadDepartments() {
  try {
    const response = await fetch(`${API_BASE}/api/departments/`);
    if (!response.ok) throw new Error('Failed to load departments');
    allDepartments = await response.json();
    populateDepartmentSelect();
  } catch (error) {
    console.error('Error loading departments:', error);
    allDepartments = [];
  }
}

async function loadPositions() {
  try {
    const response = await fetch(`${API_BASE}/api/positions/`);
    if (!response.ok) throw new Error('Failed to load positions');
    allPositions = await response.json();
    populatePositionSelect();
  } catch (error) {
    console.error('Error loading positions:', error);
    allPositions = [];
  }
}

async function loadEmployees() {
  try {
    const response = await fetch(`${API_BASE}/api/employees/`);
    if (!response.ok) throw new Error('Failed to load employees');
    allEmployees = await response.json();
    populateFacultyChart();
    populateOrgChart();
  } catch (error) {
    console.error('Error loading employees:', error);
    allEmployees = [];
  }
}

async function loadLeaveRequests() {
  try {
    const response = await fetch(`${API_BASE}/api/leave-requests/`);
    if (!response.ok) throw new Error('Failed to load leave requests');
    
    const allRequests = await response.json();
    
    const pendingRequests = allRequests.filter(req => 
      req.status === 'pending' || req.status === 'Pending'
    );
    
    displayLeaveRequests(pendingRequests);
  } catch (error) {
    console.error('Error loading leave requests:', error);
    displayLeaveRequests([]);
  }
}

async function loadLeaveReports() {
  try {
    const response = await fetch(`${API_BASE}/api/leave-requests/`);
    if (!response.ok) throw new Error('Failed to load leave reports');
    
    const allRequests = await response.json();
    
    const nonPendingRequests = allRequests.filter(req => 
      req.status !== 'pending' && req.status !== 'Pending'
    );
    
    displayLeaveReports(nonPendingRequests);
  } catch (error) {
    console.error('Error loading leave reports:', error);
    displayLeaveReports([]);
  }
}

function populateDepartmentSelect() {
  const select = document.getElementById('employeeDepartment');
  if (!select) return;
  
  select.innerHTML = '<option value="">Select Department</option>';
  allDepartments.forEach(dept => {
    select.innerHTML += `<option value="${dept.id}">${dept.name}</option>`;
  });
}

function populatePositionSelect() {
    const select = document.getElementById('employeePosition');
    if (!select) return;

    select.innerHTML = '<option value="">Select Position</option>';

    allPositions
        .filter(pos => pos.title.toLowerCase() !== 'dean')
        .forEach(pos => {
            const option = document.createElement('option');
            option.value = pos.id;
            option.textContent = pos.title;
            select.appendChild(option);
        });
}

function populateOrgChart() {
  const academicSection = document.getElementById('academic-section');
  const adminSection = document.getElementById('admin-section');
  const itSection = document.getElementById('it-section');

  if (!academicSection || !adminSection || !itSection) return;

  const academicDepts = allDepartments.filter(d => 
    ['basic-ed', 'grad-school', 'cite', 'caba', 'chm'].includes(d.code)
  );
  const adminDepts = allDepartments.filter(d => 
    ['hr', 'finance', 'admissions'].includes(d.code)
  );
  const itDepts = allDepartments.filter(d => 
    ['it', 'support'].includes(d.code)
  );

  academicSection.innerHTML = createDepartmentCards(academicDepts);
  adminSection.innerHTML = createDepartmentCards(adminDepts);
  itSection.innerHTML = createDepartmentCards(itDepts);
}

function createDepartmentCards(departments) {
  if (!departments || departments.length === 0) {
    return '<p style="text-align: center; color: #999; padding: 20px;">No departments found</p>';
  }

  return departments.map(dept => {
    const employees = allEmployees.filter(e => 
      e.department === dept.id && e.is_active
    );
    const count = employees.length;

    return `
      <div class="dept-card" onclick="filterEmployeesByDepartment(${dept.id})">
        <div class="dept-icon">📚</div>
        <div class="dept-name">${dept.name}</div>
        <div class="dept-count">${count} ${count === 1 ? 'Employee' : 'Employees'}</div>
      </div>
    `;
  }).join('');
}

function filterEmployeesByDepartment(deptId) {
  switchSection('facultySection');
}

function populateFacultyChart() {
  const container = document.getElementById('facultyChartContainer');
  if (!container) return;
  
  const activeEmployees = allEmployees.filter(emp => emp.is_active);
  
  if (activeEmployees.length === 0) {
    container.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">No active employees found</p>';
    return;
  }

  const groupedByDept = {};
  activeEmployees.forEach(emp => {
    const deptName = emp.department_name || 'Unknown Department';
    if (!groupedByDept[deptName]) {
      groupedByDept[deptName] = [];
    }
    groupedByDept[deptName].push(emp);
  });

  let html = '';
  for (const [deptName, employees] of Object.entries(groupedByDept)) {
    html += `
      <div class="faculty-department">
        <h3 class="dept-header">${deptName}</h3>
        <div class="faculty-grid">
          ${employees.map(emp => `
            <div class="faculty-card">
              <div class="faculty-photo">
                ${emp.photo_url 
                  ? `<img src="${emp.photo_url}" alt="${emp.full_name}" onerror="this.parentElement.innerHTML='<div class=\\'no-photo\\'>👤</div>'">` 
                  : '<div class="no-photo">👤</div>'}
              </div>
              <div class="faculty-info">
                <div class="faculty-name">${emp.full_name}</div>
                <div class="faculty-position">${emp.position_title || 'N/A'}</div>
                <div class="faculty-id">${emp.employee_id}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}

function displayLeaveRequests(reports) {
  const container = document.querySelector('.leave-requests-container');
  if (!container) return;

  if (!reports || reports.length === 0) {
    container.innerHTML =
      '<p style="text-align: center; padding: 40px; color: #666;">No pending leave requests found</p>';
    return;
  }

  container.innerHTML = reports.map(req => {
    const app = req.application || {};

    const employeeName = app.employee_name || 'N/A';
    const employeeId = app.employee_id_display || 'N/A';
    const departmentName = app.department_name || 'N/A';
    const positionTitle = app.position_title || 'N/A';

    const leaveType = app.leave_type || 'N/A';
    const numDays = app.number_of_days || 0;
    const dateFiled = app.date_filed || 'N/A';
    const location = app.vacation_location || app.sick_location || 'N/A';
    const reason = app.reason || '';

    const deanReviewerName = req.dean_reviewer_name || 'Dean';
    const deanReviewedAt = req.dean_reviewed_at || '';
    const deanComments = req.dean_comments || '';

    const formatDate = (dateStr) => {
      if (!dateStr) return 'N/A';
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    };

    const leaveTypeLabel = {
      vacation: 'Vacation Leave',
      sick: 'Sick Leave',
      maternity: 'Maternity Leave',
      paternity: 'Paternity Leave',
      emergency: 'Emergency Leave'
    }[leaveType] || leaveType;

    const locationLabel = {
      philippines: 'Within the Philippines',
      abroad: 'Abroad',
      hospital: 'In Hospital',
      home: 'At Home'
    }[location] || location;

    return `
      <div class="leave-report-card">

        <!-- Header -->
        <div style="
          background: linear-gradient(180deg, #8B0000 0%, #5a0000 100%);
          color: white;
          padding: 20px 30px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        ">
          <h2 style="margin: 0; font-size: 18px;">
            Leave Request #${req.id}
          </h2>
          <span style="
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            background-color: #FFC107;
            color: #000;
          ">
            Pending HR Approval
          </span>
        </div>

        <!-- Body -->
        <div style="padding: 30px;">

          <!-- Employee Info -->
          <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
          ">
            <div>
              <label>Employee ID</label>
              <div>${employeeId}</div>
            </div>
            <div>
              <label>Employee Name</label>
              <div>${employeeName}</div>
            </div>
          </div>

          <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
          ">
            <div>
              <label>Department</label>
              <div>${departmentName}</div>
            </div>
            <div>
              <label>Position</label>
              <div>${positionTitle}</div>
            </div>
            <div>
              <label>Date Filed</label>
              <div>${formatDate(dateFiled)}</div>
            </div>
          </div>

          <!-- Leave Details -->
          <div style="
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
          ">
            <h3>Leave Details</h3>
            <p><strong>Type:</strong> ${leaveTypeLabel}</p>
            <p><strong>Location:</strong> ${locationLabel}</p>
            <p><strong>Number of Days:</strong> ${numDays}</p>
            ${reason ? `<p><strong>Reason:</strong> ${reason}</p>` : ''}
          </div>

          <!-- Dean Approval -->
          <div style="
            background-color: #e8f5e9;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
          ">
            <h3 style="color: #2e7d32;">Dean Approval</h3>
            <p><strong>Reviewed By:</strong> ${deanReviewerName}</p>
            <p><strong>Reviewed At:</strong> ${formatDate(deanReviewedAt)}</p>
            ${deanComments ? `<p><strong>Comments:</strong> ${deanComments}</p>` : ''}
          </div>

          <!-- Actions -->
          <div style="display: flex; gap: 10px;">
            <button class="approve-btn" data-id="${req.id}">
              ✓ Approve
            </button>
            <button class="reject-btn" data-id="${req.id}">
              ✕ Reject
            </button>
          </div>

        </div>
      </div>
    `;
  }).join('');

  container.querySelectorAll('.approve-btn').forEach(btn => {
    btn.addEventListener('click', () =>
      approveLeaveRequest(btn.dataset.id)
    );
  });

  container.querySelectorAll('.reject-btn').forEach(btn => {
    btn.addEventListener('click', () =>
      rejectLeaveRequest(btn.dataset.id)
    );
  });
}


function displayLeaveReports(reports) {
  const container = document.querySelector('.leave-reports-cards-container');
  
  if (!container) return;

  const filteredReports = (reports || []).filter(r => 
    r.dean_status === 'dean_approved' && 
    (r.hr_status === 'hr_approved' || r.hr_status === 'hr_denied')
  );

  if (!filteredReports.length) {
    container.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">No leave reports found</p>';
    return;
  }

  container.innerHTML = filteredReports.map(req => {
    const employeeName = req.employee_name || 'N/A';
    const employeeId = req.employee_id || 'N/A';
    const departmentName = req.department_name || 'N/A';
    const positionTitle = req.position_title || 'N/A';
    const photoUrl = req.employee_photo_url || '';

    const leaveType = req.leave_type || 'N/A';
    const numDays = req.number_of_days || 0;
    const dateFiled = req.date_filed || 'N/A';
    const location = req.location || 'N/A';
    const notes = req.reason || '';

    const deanReviewer = req.dean_reviewer_name || null;
    const hrReviewer = req.hr_reviewer_name || null;
    const deanDecision = req.dean_status_display || null;
    const hrDecision = req.hr_status_display || null;
    const reviewedAt = req.dean_reviewed_at || req.hr_reviewed_at || '';
    const reviewComments = req.dean_comments || req.hr_comments || '';

    let statusText = '';
    if (deanDecision) statusText += deanDecision;
    if (hrDecision) statusText += (statusText ? ' → ' : '') + hrDecision;

    const statusColorMap = {
      'approved': '#4CAF50',
      'dean_approved': '#2196F3',
      'dean_denied': '#f44336',
      'hr_approved': '#4CAF50',
      'hr_denied': '#f44336',
      'pending': '#FFC107'
    };

    const status = statusText || 'N/A';
    const statusColor = statusColorMap[req.dean_status || req.hr_status] || '#999';
    const statusBg = status.toLowerCase().includes('approved') ? '#e8f5e9' : '#ffebee';
    const statusBorder = status.toLowerCase().includes('approved') ? '#4CAF50' : '#f44336';

    // Helper functions
    const formatDate = (dateStr) => {
      if (!dateStr || dateStr === 'N/A') return 'N/A';
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    };

    const getLeaveTypeLabel = (type) => {
      const types = {
        'vacation': 'Vacation Leave',
        'sick': 'Sick Leave',
        'maternity': 'Maternity Leave',
        'paternity': 'Paternity Leave',
        'emergency': 'Emergency Leave'
      };
      return types[type] || type;
    };

    const getLocationLabel = (loc) => {
      const locations = {
        'philippines': 'Within the Philippines',
        'abroad': 'Abroad',
        'hospital': 'In Hospital',
        'home': 'At Home'
      };
      return locations[loc] || loc;
    };

    return `
      <div class="leave-report-card">
        <!-- Form Header -->
        <div style="background: linear-gradient(180deg, #8B0000 0%, #5a0000 100%); color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center;">
          <h2 style="font-size: 18px; margin: 0;">Leave Application Report #${req.id || ''}</h2>
          <span style="padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: bold; background-color: ${statusColor}; color: white;">
            ${status.toUpperCase()}
          </span>
        </div>

        <!-- Section Title: Employee Information -->
        <div style="background: linear-gradient(180deg, #8B0000 0%, #5a0000 100%); color: white; padding: 12px 30px; font-size: 14px; font-weight: bold; letter-spacing: 1px;">
          EMPLOYEE INFORMATION
        </div>

        <!-- Form Content -->
        <div style="padding: 30px;">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
            <div>
              <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">Employee ID</label>
              <div style="padding: 10px 12px; border: 1px solid #d0d0d0; border-radius: 4px; background-color: #f9f9f9; font-size: 14px; color: #555;">
                ${employeeId}
              </div>
            </div>
            <div>
              <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">Employee Name</label>
              <div style="padding: 10px 12px; border: 1px solid #d0d0d0; border-radius: 4px; background-color: #f9f9f9; font-size: 14px; color: #555;">
                ${employeeName}
              </div>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
            <div>
              <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">Department</label>
              <div style="padding: 10px 12px; border: 1px solid #d0d0d0; border-radius: 4px; background-color: #f9f9f9; font-size: 14px; color: #555;">
                ${departmentName}
              </div>
            </div>
            <div>
              <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">Position</label>
              <div style="padding: 10px 12px; border: 1px solid #d0d0d0; border-radius: 4px; background-color: #f9f9f9; font-size: 14px; color: #555;">
                ${positionTitle}
              </div>
            </div>
            <div>
              <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">Date of Filing</label>
              <div style="padding: 10px 12px; border: 1px solid #d0d0d0; border-radius: 4px; background-color: #f9f9f9; font-size: 14px; color: #555;">
                ${formatDate(dateFiled)}
              </div>
            </div>
          </div>

          <!-- Leave Details Section -->
          <div style="background: linear-gradient(180deg, #8B0000 0%, #5a0000 100%); color: white; padding: 12px 30px; font-size: 14px; font-weight: bold; letter-spacing: 1px; margin: 20px -30px;">
            LEAVE DETAILS
          </div>

          <div style="border-top: 2px solid #e0e0e0; padding-top: 20px; margin-top: 10px;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
              <div>
                <div style="margin-bottom: 20px;">
                  <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">Type of Leave</label>
                  <div style="padding: 10px 12px; border: 1px solid #d0d0d0; border-radius: 4px; background-color: #f9f9f9; font-size: 14px; color: #555;">
                    ${getLeaveTypeLabel(leaveType)}
                  </div>
                </div>

                <div style="background-color: #f9f5f7; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0; text-align: center;">
                  <label style="display: block; margin-bottom: 10px; font-size: 13px; font-weight: 600; color: #333;">Employee Photo</label>
                  <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <div style="width: 120px; height: 120px; border-radius: 50%; overflow: hidden; border: 3px solid #8B0000; margin-bottom: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                      <img src="${photoUrl}" alt="Employee Photo" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    <div style="font-size: 16px; font-weight: bold; color: #222; margin-bottom: 4px;">${employeeName}</div>
                    <div style="font-size: 13px; color: #666; background: #f0f0f0; padding: 6px 12px; border-radius: 12px;">${employeeId}</div>
                  </div>
                </div>
              </div>

              <div>
                ${location ? `
                <div style="margin-bottom: 20px;">
                  <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">Where Leave Will Be Spent</label>
                  <div style="padding: 10px 12px; border: 1px solid #d0d0d0; border-radius: 4px; background-color: #f9f9f9; font-size: 14px; color: #555;">
                    ${getLocationLabel(location)}
                  </div>
                </div>
                ` : ''}

                <div style="margin-bottom: 20px;">
                  <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">Number of Days</label>
                  <div style="padding: 10px 12px; border: 1px solid #d0d0d0; border-radius: 4px; background-color: #f9f9f9; font-size: 14px; color: #555;">
                    ${numDays} day(s)
                  </div>
                </div>

                ${notes ? `
                <div style="margin-bottom: 20px;">
                  <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">Additional Notes</label>
                  <div style="padding: 10px 12px; border: 1px solid #d0d0d0; border-radius: 4px; background-color: #f9f9f9; font-size: 14px; color: #555; min-height: 60px; white-space: pre-wrap;">
                    ${notes}
                  </div>
                </div>
                ` : ''}

                <div style="background-color: ${statusBg}; padding: 15px; border-radius: 6px; border-left: 4px solid ${statusBorder};">
                  <h4 style="font-size: 13px; color: #333; margin: 0 0 8px 0;">
                    ${status.toLowerCase().includes('approved') ? '✓ Approved By' : '✗ Denied By'}
                  </h4>
                  <p style="font-size: 14px; color: #555; margin: 4px 0;">
                    <strong>Reviewer:</strong> ${deanReviewer || hrReviewer || 'Admin'}
                  </p>
                  <p style="font-size: 14px; color: #555; margin: 4px 0;">
                    <strong>Date:</strong> ${formatDate(reviewedAt)}
                  </p>
                  ${reviewComments ? `
                  <div style="background-color: #fff9c4; padding: 12px; border-radius: 6px; margin-top: 10px; border-left: 4px solid #fbc02d;">
                    <strong style="font-size: 13px;">Comments:</strong>
                    <p style="font-size: 13px; color: #666; font-style: italic; margin: 4px 0 0 0;">
                      ${reviewComments}
                    </p>
                  </div>
                  ` : ''}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}


async function approveLeaveRequest(id) {
  const comments = prompt('Enter comments for approval (optional):');
  if (comments === null) return;

  try {
    showLoader();
    const response = await fetch(`${API_BASE}/api/leave-requests/${id}/hr_approve/`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ comments: comments || '' })
    });

    const data = await response.json();
    if (response.ok && data.success) {
      showSuccess(data.message || 'Leave request approved by HR');
      await loadLeaveRequests();
      await loadLeaveReports();
    } else {
      showError(data.message || 'Failed to approve leave request');
    }
  } catch (error) {
    console.error('Error approving leave request:', error);
    showError('Failed to approve leave request');
  } finally {
    hideLoader();
  }
}

async function rejectLeaveRequest(id) {
  let comments = '';
  while (!comments) {
    comments = prompt('Enter rejection reason (required):');
    if (comments === null) return;
  }

  try {
    showLoader();
    const response = await fetch(`${API_BASE}/api/leave-requests/${id}/hr_deny/`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ comments })
    });

    const data = await response.json();
    if (response.ok && data.success) {
      showSuccess(data.message || 'Leave request denied by HR');
      await loadLeaveRequests();
      await loadLeaveReports();
    } else {
      showError(data.message || 'Failed to reject leave request');
    }
  } catch (error) {
    console.error('Error rejecting leave request:', error);
    showError('Failed to reject leave request');
  } finally {
    hideLoader();
  }
}

function openAddEmployeeModal() {
  const form = document.getElementById('employeeForm');
  if (form) form.reset();
  
  const modalTitle = document.getElementById('modalTitle');
  if (modalTitle) modalTitle.textContent = 'Add Employee';
  
  const modal = document.getElementById('employeeModal');
  if (modal) modal.style.display = 'flex';
  
  const avatarPreview = document.getElementById('avatarPreview');
  if (avatarPreview) {
    avatarPreview.innerHTML = `
      <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
        <circle cx="30" cy="30" r="30" fill="#e0e0e0" />
        <path d="M30 28C33.866 28 37 24.866 37 21C37 17.134 33.866 14 30 14C26.134 14 23 17.134 23 21C23 24.866 26.134 28 30 28Z" fill="#999" />
        <path d="M42 46C42 38.268 36.627 32 30 32C23.373 32 18 38.268 18 46" fill="#999" />
      </svg>
    `;
  }
  
  updateEmployeeId();
  currentPhotoFile = null;
  if (form) delete form.dataset.employeeId;
  loadPositions();
}

function closeModal() {
  const modal = document.getElementById('employeeModal');
  if (modal) modal.style.display = 'none';
  currentPhotoFile = null;
}

function openUpdateModal() {
  const modal = document.getElementById('updateModal');
  if (modal) modal.style.display = 'flex';
  displayEmployeeList();
}

function closeUpdateModal() {
  const modal = document.getElementById('updateModal');
  if (modal) modal.style.display = 'none';
}

function displayEmployeeList() {
  const container = document.getElementById('employeeList');
  if (!container) return;
  
  if (allEmployees.length === 0) {
    container.innerHTML = '<p style="text-align: center; padding: 20px;">No employees found</p>';
    return;
  }

  container.innerHTML = allEmployees.map(emp => `
    <div class="employee-list-item ${!emp.is_active ? 'inactive' : ''}">
      <div class="employee-info">
        <div class="employee-name-text">${emp.full_name}</div>
        <div style="font-size: 0.9em; color: #666;">
          ${emp.employee_id} - ${emp.position_title || 'N/A'}
          ${!emp.is_active ? '<span style="color: #d32f2f;"> (Inactive)</span>' : ''}
        </div>
      </div>
      <div class="employee-actions">
        <button onclick="editEmployee(${emp.id})" class="btn-edit">Edit</button>
        ${emp.is_active 
          ? `<button class="btn-deactivate" style="background: transparent;">✅</button>`

          : `<button onclick="activateEmployee(${emp.id})" class="btn-activate">Activate</button>`
        }
        ${!emp.is_active ? '' : `<button onclick="deleteEmployee(${emp.id})" class="btn-delete">Deactivate</button>`}
      </div>
    </div>
  `).join('');
}

async function activateEmployee(employeeId) {
  if (!confirm('Are you sure you want to activate this employee?')) return;
  
  try {
    showLoader();
    const response = await fetch(`${API_BASE}/api/employees/${employeeId}/activate/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json'
      }
    });

    const result = await response.json();

    if (response.ok) {
      showSuccess(result.message || "Employee activated successfully");
      await loadEmployees();
      displayEmployeeList();
    } else {
      showError(result.message || "Failed to activate employee");
    }
  } catch (error) {
    console.error("Error activating employee:", error);
    showError("Error activating employee");
  } finally {
    hideLoader();
  }
}

async function deleteEmployee(employeeId) {
  if (!confirm("Are you sure you want to deactivate this employee?")) return;

  try {
    showLoader();
    const response = await fetch(`${API_BASE}/api/employees/${employeeId}/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': csrftoken
      }
    });

    if (response.ok) {
      showSuccess("Employee deactivated successfully");
      await loadEmployees();
      displayEmployeeList();
    } else {
      const error = await response.json();
      showError(error.message || "Failed to deactivate employee");
    }
  } catch (error) {
    console.error("Error deactivating employee:", error);
    showError("Error deactivating employee");
  } finally {
    hideLoader();
  }
}

async function editEmployee(id) {
  const employee = allEmployees.find(e => e.id === id);
  if (!employee) return;

  closeUpdateModal();
  
  document.getElementById('modalTitle').textContent = 'Update Employee';
  document.getElementById('employeeId').value = employee.employee_id;
  document.getElementById('employeeName').value = employee.full_name;
  document.getElementById('employeeGender').value = employee.gender;
  document.getElementById('employeeAge').value = employee.age;
  document.getElementById('employeeWeight').value = employee.weight;
  document.getElementById('employeeHeight').value = employee.height;
  document.getElementById('employeePosition').value = employee.position;
  document.getElementById('employeeDepartment').value = employee.department;
  
  const mottoField = document.getElementById('employeeMotto');
  if (mottoField) mottoField.value = employee.motto_in_life || '';
  
  if (employee.photo_url) {
    document.getElementById('avatarPreview').innerHTML = 
      `<img src="${employee.photo_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
  }
  
  currentPhotoFile = null;
  document.getElementById('employeeForm').dataset.employeeId = id;
  document.getElementById('employeeModal').style.display = 'flex';
  
  await loadPositions();
}

async function handleEmployeeSubmit(e) {
  e.preventDefault();

  const formData = new FormData();
  const employeeId = e.target.dataset.employeeId;

  formData.append('full_name', document.getElementById('employeeName').value);
  formData.append('gender', document.getElementById('employeeGender').value);
  formData.append('age', document.getElementById('employeeAge').value);
  formData.append('weight', document.getElementById('employeeWeight').value);
  formData.append('height', document.getElementById('employeeHeight').value);
  formData.append('position', document.getElementById('employeePosition').value);
  formData.append('department', document.getElementById('employeeDepartment').value);
  
  const mottoField = document.getElementById('employeeMotto');
  if (mottoField) formData.append('motto_in_life', mottoField.value);

  if (currentPhotoFile) {
    formData.append('photo', currentPhotoFile);
  }

  try {
    showLoader();
    let url, method;
    
    if (employeeId) {
      url = `${API_BASE}/api/employees/${employeeId}/`;
      method = 'PUT';
    } else {
      url = `${API_BASE}/api/employees/`;
      method = 'POST';
    }

    const response = await fetch(url, {
      method: method,
      headers: {
        'X-CSRFToken': csrftoken
      },
      body: formData
    });

    const result = await response.json();

    if (response.ok) {
      showSuccess(employeeId ? 'Employee updated successfully' : 'Employee added successfully');
      closeModal();
      await loadEmployees();
      await loadPositions();
    } else {
      const errorMsg = result.message || JSON.stringify(result);
      showError('Error: ' + errorMsg);
    }
  } catch (error) {
    console.error('Error saving employee:', error);
    showError('Failed to save employee. Please try again.');
  } finally {
    hideLoader();
  }
}

function handlePhotoUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  if (file.size > 5 * 1024 * 1024) {
    showError('File size must be less than 5MB');
    event.target.value = '';
    return;
  }
  
  if (!file.type.startsWith('image/')) {
    showError('Please upload an image file');
    event.target.value = '';
    return;
  }
  
  currentPhotoFile = file;
  const reader = new FileReader();
  reader.onload = function(e) {
    document.getElementById('avatarPreview').innerHTML = 
      `<img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
  };
  reader.readAsDataURL(file);
}

async function updateEmployeeId() {
  try {
    const year = new Date().getFullYear();
    const response = await fetch(`${API_BASE}/api/employees/`);
    const employees = await response.json();
    
    const thisYearEmployees = employees.filter(e => e.employee_id.startsWith(`OC-${year}`));
    const nextNumber = thisYearEmployees.length + 1;
    
    document.getElementById('employeeId').value = `OC-${year}${String(nextNumber).padStart(4, '0')}`;
  } catch (error) {
    console.error('Error updating employee ID:', error);
    const year = new Date().getFullYear();
    document.getElementById('employeeId').value = `OC-${year}0001`;
  }
}

function openDepartmentModal() {
  const form = document.getElementById('departmentForm');
  if (form) form.reset();
  
  const modalTitle = document.getElementById('departmentModalTitle');
  if (modalTitle) modalTitle.textContent = 'Add Department';
  
  const modal = document.getElementById('departmentModal');
  if (modal) modal.style.display = 'flex';
}

function closeDepartmentModal() {
  const modal = document.getElementById('departmentModal');
  if (modal) modal.style.display = 'none';
}

async function handleDepartmentSubmit(e) {
  e.preventDefault();

  const data = {
    code: document.getElementById('departmentCode').value,
    name: document.getElementById('departmentName').value,
    description: document.getElementById('departmentDescription').value
  };

  try {
    showLoader();
    const response = await fetch(`${API_BASE}/api/departments/`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (response.ok) {
      showSuccess('Department added successfully');
      closeDepartmentModal();
      await loadDepartments();
      populateOrgChart();
    } else {
      showError('Error adding department: ' + JSON.stringify(result));
    }
  } catch (err) {
    console.error('Error:', err);
    showError('Failed to add department');
  } finally {
    hideLoader();
  }
}

function openPositionModal() {
  const form = document.getElementById('positionForm');
  if (form) form.reset();
  
  const modalTitle = document.getElementById('positionModalTitle');
  if (modalTitle) modalTitle.textContent = 'Add Position';
  
  const modal = document.getElementById('positionModal');
  if (modal) modal.style.display = 'flex';
}

function closePositionModal() {
  const modal = document.getElementById('positionModal');
  if (modal) modal.style.display = 'none';
}

async function handlePositionSubmit(e) {
  e.preventDefault();

  const data = {
    code: document.getElementById('positionCode').value,
    title: document.getElementById('positionTitle').value,
    description: document.getElementById('positionDescription').value
  };

  try {
    showLoader();
    const response = await fetch(`${API_BASE}/api/positions/`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (response.ok) {
      showSuccess('Position added successfully');
      closePositionModal();
      await loadPositions();
    } else {
      showError('Error adding position: ' + JSON.stringify(result));
    }
  } catch (err) {
    console.error('Error:', err);
    showError('Failed to add position');
  } finally {
    hideLoader();
  }
}

function switchSection(section, menuItem) {
  document.querySelectorAll('.menu-item').forEach(item => {
    item.classList.remove('active');
  });
  
  if (menuItem) {
    menuItem.classList.add('active');
  }

  const sections = [
    document.querySelector('.main-content'),
    document.getElementById('facultySection'),
    document.getElementById('LeaveRequestsSection'),
    document.getElementById('leaveReportsSection')
  ];

  sections.forEach(sec => {
    if (sec) sec.style.display = 'none';
  });

  if (section === 'dashboard') {
    const mainContent = document.querySelector('.main-content');
    if (mainContent) mainContent.style.display = 'block';
  } else {
    const sectionElement = document.getElementById(section);
    if (sectionElement) sectionElement.style.display = 'block';
  }
}

function toggleSection(section) {
  const sectionElement = document.getElementById(`${section}-section`);
  const toggleIcon = document.getElementById(`${section}-toggle`);
  
  if (!sectionElement || !toggleIcon) return;
  
  if (sectionElement.classList.contains('hidden')) {
    sectionElement.classList.remove('hidden');
    toggleIcon.textContent = '🔽';
  } else {
    sectionElement.classList.add('hidden');
    toggleIcon.textContent = '➕';
  }
}

function navigate(action) {
  if (action === 'Logout') {
    const modal = document.getElementById('logoutModal');
    if (modal) {
      modal.style.display = 'flex';
    }

    fetch('/logout/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      }
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setTimeout(() => {
            window.location.href = data.redirect_url || '/';
          }, 1500);
        }
      })
      .catch(err => {
        console.error('Logout failed:', err);
        window.location.href = '/';
      });
  }
}

function toggleHRInfo() {
  toggleHRModal();
}

window.openAddEmployeeModal = openAddEmployeeModal;
window.closeModal = closeModal;
window.openUpdateModal = openUpdateModal;
window.closeUpdateModal = closeUpdateModal;
window.handlePhotoUpload = handlePhotoUpload;
window.editEmployee = editEmployee;
window.deleteEmployee = deleteEmployee;
window.activateEmployee = activateEmployee;
window.openDepartmentModal = openDepartmentModal;
window.closeDepartmentModal = closeDepartmentModal;
window.openPositionModal = openPositionModal;
window.closePositionModal = closePositionModal;
window.toggleSection = toggleSection;
window.navigate = navigate;
window.showAlert = showError;
window.approveLeaveRequest = approveLeaveRequest;
window.rejectLeaveRequest = rejectLeaveRequest;
window.toggleHRModal = toggleHRModal;
window.toggleHRInfo = toggleHRInfo;
window.filterEmployeesByDepartment = filterEmployeesByDepartment;