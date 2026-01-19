const CONFIG = {
  DEV_URL: "https://kt2980zx-8000.asse.devtunnels.ms",
  //DEV_URL: "http://127.0.0.1:8000/api",
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

    await loadLeaveData();

    populateOrgChart();
  } catch (error) {
    console.error('Error initializing dashboard:', error);
    showError('Failed to initialize dashboard. Please refresh the page.');
  } finally {
    hideLoader();
  }
}

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
      location.reload();
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

const photoInput = document.getElementById('hrPhoto');
  const photoPreview = document.getElementById('photoPreview');

  photoInput.addEventListener('change', function () {
    const file = this.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
        photoPreview.src = e.target.result;
        photoPreview.style.display = 'block';
      };
      reader.readAsDataURL(file);
    } else {
      photoPreview.src = "";
      photoPreview.style.display = "none";
    }
  });

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

async function loadLeaveData() {
  try {
    const response = await fetch(`${API_BASE}/api/leave-requests/`);
    if (!response.ok) throw new Error('Failed to load leave data');
    
    const result = await response.json();

    const allRequests = Array.isArray(result) ? result : (result.data || []);

    const deanApprovedRequests = allRequests.filter(req => req.status === 'dean_approved');
    const nonPendingReports = allRequests.filter(req => req.status !== 'pending' && req.status !== 'Pending');

    displayLeaveRequests(deanApprovedRequests);
    displayLeaveReports(nonPendingReports);
  } catch (error) {
    console.error('Error loading leave data:', error);
    displayLeaveRequests([]);
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

  const filteredReports = (reports || []).filter(r => r.status === 'dean_approved');

  if (!filteredReports.length) {
    container.innerHTML =
      '<p style="text-align: center; padding: 40px; color: #666;">No dean-approved leave requests found</p>';
    return;
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  //console.log(`Data: ${JSON.stringify(filteredReports)}`);

  container.innerHTML = filteredReports.map(req => {
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

    const statusDisplay = req.status_display || 'Unknown Status';

    //console.log(`Data To Be Displayed: ${JSON.stringify(req)}`); --> Pangcheck

    return `
      <div class="leave-report-card">
        <div style="background: linear-gradient(180deg, #8B0000 0%, #5a0000 100%);
                    color: white; padding: 20px 30px; display: flex;
                    justify-content: space-between; align-items: center;">
          <h2 style="margin: 0; font-size: 13px;">Leave Request #${req.id}</h2>
          <span style="padding: 8px 16px; border-radius: 20px; font-size: 12px;
                       font-weight: bold; background-color: #FFC107; color: #000;">
            ${statusDisplay}
          </span>
        </div>

        <div style="padding: 30px;">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                      gap: 15px; margin-bottom: 20px;">
            <div><label>Employee ID</label><div>${employeeId}</div></div>
            <div><label>Employee Name</label><div>${employeeName}</div></div>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                      gap: 15px; margin-bottom: 20px;">
            <div><label>Department</label><div>${departmentName}</div></div>
            <div><label>Position</label><div>${positionTitle}</div></div>
            <div><label>Date Filed</label><div>${formatDate(dateFiled)}</div></div>
          </div>

          <div style="background-color: #f5f5f5; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3>Leave Details</h3>
            <p><strong>Type:</strong> ${leaveType}</p>
            <p><strong>Location:</strong> ${location}</p>
            <p><strong>Number of Days:</strong> ${numDays}</p>
            ${reason ? `<p><strong>Reason:</strong> ${reason}</p>` : ''}
          </div>

          <div style="background-color: #e8f5e9; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="color: #2e7d32;">Dean Approval</h3>
            <p><strong>Reviewed By:</strong> ${deanReviewerName}</p>
            <p><strong>Reviewed At:</strong> ${formatDate(deanReviewedAt)}</p>
            ${deanComments ? `<p><strong>Comments:</strong> ${deanComments}</p>` : ''}
          </div>

          <div style="display: flex; gap: 10px;">
            <button class="approve-btn" data-id="${req.id}">✓ Approve</button>
            <button class="reject-btn" data-id="${req.id}">✕ Reject</button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  container.querySelectorAll('.approve-btn').forEach(btn => {
    btn.addEventListener('click', () => approveLeaveRequest(btn.dataset.id));
  });
  container.querySelectorAll('.reject-btn').forEach(btn => {
    btn.addEventListener('click', () => rejectLeaveRequest(btn.dataset.id));
  });
}

function displayLeaveReports(reports) {
  const container = document.querySelector('.leave-reports-cards-container');
  
  if (!container) return;

  const filteredReports = (reports || []).filter(r => 
    r.status === 'denied' || r.status === 'approved'
  );

  if (!filteredReports.length) {
    container.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">No leave reports found</p>';
    return;
  }

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

  container.innerHTML = filteredReports.map(req => {
    const app = req.application || {};

    const employeeName = app.employee_name || 'N/A';
    const employeeId = app.employee_id_display || 'N/A';
    const departmentName = app.department_name || 'N/A';
    const positionTitle = app.position_title || 'N/A';
    const photoUrl = app.employee_photo_url || '';

    const leaveType = app.leave_type || 'N/A';
    const numDays = app.number_of_days || 0;
    const dateFiled = app.date_filed || 'N/A';
    const location = app.vacation_location || app.sick_location || '';
    const notes = app.reason || '';

    const deanReviewer = req.dean_reviewer_name || null;
    const deanReviewedAt = req.dean_reviewed_at || '';
    const deanComments = req.dean_comments || '';

    const hrReviewer = req.hr_reviewer_name || null;
    const hrReviewedAt = req.hr_reviewed_at || '';
    const hrComments = req.hr_comments || '';

    const statusDisplay = req.status_display || 'Unknown Status';
    const status = req.status;

    const statusColorMap = {
      'approved': '#4CAF50',
      'dean_approved': '#2196F3',
      'pending': '#FFC107'
    };

    const statusColor = statusColorMap[status] || '#ff0e0e';
    const statusBg = status === 'approved' ? '#e8f5e9' : '#e3f2fd';
    const statusBorder = status === 'approved' ? '#4CAF50' : '#2196F3';

    let approvalSection = '';
    
    if (status === 'approved') {
      approvalSection = `
        <div style="background-color: ${statusBg}; padding: 15px; border-radius: 6px; border-left: 4px solid ${statusBorder};">
          <h4 style="font-size: 13px; color: #333; margin: 0 0 8px 0;">
            ✓ Approved By Dean
          </h4>
          <p style="font-size: 14px; color: #555; margin: 4px 0;">
            <strong>Reviewer:</strong> ${deanReviewer || 'Dean'}
          </p>
          <p style="font-size: 14px; color: #555; margin: 4px 0;">
            <strong>Date:</strong> ${formatDate(deanReviewedAt)}
          </p>
          ${deanComments ? `
          <div style="background-color: #fff9c4; padding: 12px; border-radius: 6px; margin-top: 10px; border-left: 4px solid #fbc02d;">
            <strong style="font-size: 13px;">Dean Comments:</strong>
            <p style="font-size: 13px; color: #666; font-style: italic; margin: 4px 0 0 0;">
              ${deanComments}
            </p>
          </div>
          ` : ''}
        </div>

        <div style="background-color: #e8f5e9; padding: 15px; border-radius: 6px; border-left: 4px solid #4CAF50; margin-top: 15px;">
          <h4 style="font-size: 13px; color: #333; margin: 0 0 8px 0;">
            ✓ Approved By HR
          </h4>
          <p style="font-size: 14px; color: #555; margin: 4px 0;">
            <strong>Reviewer:</strong> ${hrReviewer || 'HR'}
          </p>
          <p style="font-size: 14px; color: #555; margin: 4px 0;">
            <strong>Date:</strong> ${formatDate(hrReviewedAt)}
          </p>
          ${hrComments ? `
          <div style="background-color: #fff9c4; padding: 12px; border-radius: 6px; margin-top: 10px; border-left: 4px solid #fbc02d;">
            <strong style="font-size: 13px;">HR Comments:</strong>
            <p style="font-size: 13px; color: #666; font-style: italic; margin: 4px 0 0 0;">
              ${hrComments}
            </p>
          </div>
          ` : ''}
        </div>
      `;
    } else if (status === 'approved' || status === 'denied') {
      approvalSection = `
        <div style="background-color: ${statusBg}; padding: 15px; border-radius: 6px; border-left: 4px solid ${statusBorder};">
          <h4 style="font-size: 13px; color: #333; margin: 0 0 8px 0;">
            ✓ Approved By Dean
          </h4>
          <p style="font-size: 14px; color: #555; margin: 4px 0;">
            <strong>Reviewer:</strong> ${deanReviewer || 'Dean'}
          </p>
          <p style="font-size: 14px; color: #555; margin: 4px 0;">
            <strong>Date:</strong> ${formatDate(deanReviewedAt)}
          </p>
          ${deanComments ? `
          <div style="background-color: #fff9c4; padding: 12px; border-radius: 6px; margin-top: 10px; border-left: 4px solid #fbc02d;">
            <strong style="font-size: 13px;">Dean Comments:</strong>
            <p style="font-size: 13px; color: #666; font-style: italic; margin: 4px 0 0 0;">
              ${deanComments}
            </p>
          </div>
          ` : ''}
        </div>

        <div style="background-color: #f60707; padding: 15px; border-radius: 6px; border-left: 4px solid #FF9800; margin-top: 15px;">
          <h4 style="font-size: 18px; color: #f2eeee; margin: 0 0 8px 0; font-family: monospace;">
             ✖ DENIED REQUEST
          </h4>
        </div>
      `;
    }

    return `
      <div class="leave-report-card">
        <!-- Form Header -->
        <div style="background: linear-gradient(180deg, #8B0000 0%, #5a0000 100%); color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center;">
          <h2 style="font-size: 12px; margin: 12px;">Leave Application Report #${req.id || ''}</h2>
          <span style="padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: bold; background-color: ${statusColor}; color: white; filter: drop-shadow(2px 4px 6px black);">
            ${statusDisplay.toUpperCase()}
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
                      <img src="${photoUrl}" alt="Employee Photo" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22%3E%3Crect fill=%22%23ddd%22 width=%22120%22 height=%22120%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2218%22 fill=%22%23999%22%3ENo Photo%3C/text%3E%3C/svg%3E'">
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

                <!-- Approval Status Sections -->
                ${approvalSection}
                
                <!-- Archive Button (only for approved status and not archived) -->
                
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
  
  container.querySelectorAll('.archive-btn').forEach(btn => {
    btn.addEventListener('mouseenter', (e) => {
      e.target.style.background = 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)';
      e.target.style.transform = 'translateY(-2px)';
      e.target.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
    });
    btn.addEventListener('mouseleave', (e) => {
      e.target.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
      e.target.style.transform = 'translateY(0)';
      e.target.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.3)';
    });
    btn.addEventListener('click', () => archiveLeaveRequest(btn.dataset.id));
  });
}

function isHRUser() {
  // Option 1: Check from global user object
  // return window.currentUser && window.currentUser.role === 'HR';
  
  // Option 2: Check from localStorage
  // return localStorage.getItem('userRole') === 'HR';
  
  // Option 3: Check from a data attribute on the page
  // return document.body.dataset.userRole === 'HR';
  
  // For now, return true - replace with your actual check
  // TODO: Implement proper HR user detection
  return true;
}

function getCSRFToken() {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
}

async function archiveLeaveRequest(requestId) {
  if (!isHRUser()) {
    alert('⚠️ Access Denied\n\nOnly HR users can archive leave requests.');
    return;
  }
  
  const confirmed = confirm(
    '📦 Archive Leave Request\n\n' +
    'This will permanently archive this leave request to the archive database.\n\n' +
    'Are you sure you want to continue?'
  );
  
  if (!confirmed) return;
  
  try {
    const response = await fetch(`/api/leave-requests/${requestId}/archive/`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      }
    });

    const result = await response.json();
    
    if (result.success) {
      const notification = document.createElement('div');
      notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 10000;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 16px 24px; border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-size: 14px; font-weight: 600;
        animation: slideIn 0.3s ease;
      `;
      notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 20px;">✅</span>
          <span>Request archived successfully!</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
      }, 3000);
      
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } else {
      alert('❌ Error: ' + result.message);
    }
  } catch (error) {
    console.error('Archive error:', error);
    alert('❌ Failed to archive request. Please try again.');
  }
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
      await loadLeaveData();
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
      await loadLeaveData();
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
      setTimeout(() => location.reload(), 1500);
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
      setTimeout(() => location.reload(), 1500);
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
    const confirmed = window.confirm("You'll be redirected to starting page, and you'll need to login again?");
    if (!confirmed) {
      return;
    }

    const modal = document.getElementById('globalLoadingModal');
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

document.addEventListener("DOMContentLoaded", async () => {
  const container = document.getElementById("orgChartContainer");

  container.innerHTML = `
    <div class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading organizational chart...</p>
    </div>
  `;

  try {
    const response = await fetch("/api/org-chart/", {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });

    if (!response.ok) throw new Error("Failed to load org chart");

    const data = await response.json();
    container.innerHTML = "";

    renderHRs(container, data.hrs);
    renderDeans(container, data.deans);

  } catch (error) {
    console.error(error);
    container.innerHTML = `
      <div class="error-state">
        Unable to load organizational chart.
      </div>
    `;
  }
});


function renderHRs(container, hrs) {
  if (!hrs || hrs.length === 0) {
    container.innerHTML += `
      <div class="empty-state">
        <p>No HR records found.</p>
      </div>
    `;
    return;
  }

  const validHRs = hrs.filter(hr => {
    const name = hr.full_name?.trim().toLowerCase() || "";
    const placeholders = [
      "hr-name of osmeña",
      "hr-name of example",
      "test hr"
    ];
    return !placeholders.includes(name);
  });

  if (validHRs.length === 0) {
    container.innerHTML += `
      <div class="empty-state">
        <p>No HR records found.</p>
      </div>
    `;
    return;
  }

  const level = document.createElement("div");
  level.classList.add("org-level");

  validHRs.forEach(hr => {
    const photo = hr.photo || "/static/assets/media/examplePIC.jpg";
    const card = document.createElement("div");
    card.classList.add("org-card");

    card.innerHTML = `
      <div class="org-card-header">${hr.full_name}</div>
      <div class="org-avatar">
        <img src="${photo}" alt="${hr.full_name}" />
      </div>
      <div class="org-title">${hr.full_name}</div>
      <div class="org-subtitle">${hr.position}</div>
    `;

    level.appendChild(card);
  });

  container.appendChild(level);
}

function renderDeans(container, deans) {
  if (!deans || deans.length === 0) {
    container.innerHTML += `
      <div class="empty-state">
        <p>No Deans yet. <strong onclick="alert('Add Dean form goes here')">Create One Now</strong></p>
      </div>
    `;
    return;
  }

  const maxDisplay = 15;

  for (let i = 0; i < deans.length && i < maxDisplay; i += 3) {
    const level = document.createElement("div");
    level.classList.add("org-level-two");

    deans.slice(i, i + 3).forEach(dean => {
      const photo = dean.photo || "/static/assets/media/examplePIC.jpg";

      const card = document.createElement("div");
      card.classList.add("org-card");
      card.style.position = "relative";

      const detailsHTML = `
        <div class="dean-details-bubble" style="display:none;">
          <button class="close-details">&times;</button>
          <h4>${dean.full_name}</h4>
          <p><strong>Username:</strong> ${dean.username}</p>
          <p><strong>Department:</strong> ${dean.department}</p>
          <p><strong>Position:</strong> ${dean.position}</p>
          <p><strong>Gender:</strong> ${dean.gender || 'N/A'}</p>
          <p><strong>Age:</strong> ${dean.age || 'N/A'}</p>
          <p><strong>Height:</strong> ${dean.height || 'N/A'}</p>
          <p><strong>Weight:</strong> ${dean.weight || 'N/A'}</p>
        </div>
      `;

      card.innerHTML = `
        <div class="org-avatar">
          <img src="${photo}" alt="${dean.full_name}" />
        </div>
        <div class="org-title">${dean.full_name}</div>
        <div class="org-subtitle">Dean of ${dean.department}</div>
        ${detailsHTML}
      `;

      card.addEventListener("click", e => {
        if (e.target.classList.contains("close-details")) return;

        const panel = card.querySelector(".dean-details-bubble");
        if (panel) {
          panel.style.display = panel.style.display === "none" ? "block" : "none";
        }
      });

      const closeBtn = card.querySelector(".close-details");
      closeBtn.addEventListener("click", e => {
        const panel = card.querySelector(".dean-details-bubble");
        if (panel) panel.style.display = "none";
        e.stopPropagation();
      });

      level.appendChild(card);
    });

    container.appendChild(level);
  }
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