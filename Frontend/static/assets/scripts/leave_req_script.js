//const API_BASE_URL = "http://127.0.0.1:8000/api";
const API_BASE_URL = "https://kt2980zx-8000.asse.devtunnels.ms";

let failedAttempts = 0;
let lockUntil = null;
let countdownInterval = null;

// ---------------- Secret Key Verification ----------------
function checkKey() {
    const now = new Date().getTime();
    if (lockUntil && now < lockUntil) return;

    const inputKey = document.getElementById("secretKeyInput").value;
    
    if (!inputKey.trim()) {
        document.getElementById("loginMessage").innerText = "Please enter a key";
        return;
    }

    document.getElementById("loadingSpinner").style.display = "block";
    document.querySelector("#loginDiv button").disabled = true;
    document.getElementById("loginMessage").innerText = "";

    fetch("/api/verify-key/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie('csrftoken')
        },
        body: JSON.stringify({ key: inputKey }),
        credentials: 'same-origin'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            failedAttempts = 0;
            const notif = document.getElementById("loginNotification");
            notif.style.display = "block";
            setTimeout(() => {
                document.getElementById("loginDiv").style.display = "none";
                document.getElementById("loginOverlay").style.display = "none";
                document.getElementById("formDiv").style.display = "block";
                notif.style.display = "none";
            }, 1000);
        } else {
            failedAttempts++;
            if (failedAttempts >= 3) {
                lockUntil = now + 60 * 1000; // 1 min lock
                startCountdown(60);
                failedAttempts = 0;
            } else {
                document.getElementById("loginMessage").innerText = `Invalid key! (${failedAttempts}/3 attempts)`;
            }
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        document.getElementById("loginMessage").innerText = "Error verifying key. Please try again.";
    })
    .finally(() => {
        document.getElementById("loadingSpinner").style.display = "none";
        if (!lockUntil || now >= lockUntil) {
            document.querySelector("#loginDiv button").disabled = false;
        }
    });
}

function startCountdown(seconds) {
    const messageEl = document.getElementById("loginMessage");
    const inputEl = document.getElementById("secretKeyInput");
    const buttonEl = document.querySelector("#loginDiv button");
    let remaining = seconds;
    
    inputEl.disabled = true;
    buttonEl.disabled = true;
    messageEl.style.color = "red";
    messageEl.innerText = `Too many failed attempts. Try again in ${remaining}s`;

    countdownInterval = setInterval(() => {
        remaining--;
        if (remaining > 0) {
            messageEl.innerText = `Too many failed attempts. Try again in ${remaining}s`;
        } else {
            clearInterval(countdownInterval);
            messageEl.innerText = "";
            inputEl.disabled = false;
            buttonEl.disabled = false;
            lockUntil = null;
        }
    }, 1000);
}

// Allow Enter key to submit login
document.addEventListener('DOMContentLoaded', function() {
    const secretKeyInput = document.getElementById('secretKeyInput');
    if (secretKeyInput) {
        secretKeyInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                checkKey();
            }
        });
    }
});

// ---------------- Leave Type Logic ----------------
// Verify employee when name is entered
let employeeVerified = false;
let verificationTimeout = null;

// Debounced input listener for employee code
document.getElementById('employeeCode').addEventListener('input', debounce(async function (e) {
    const employeeCode = e.target.value.trim();
    const validationMsg = document.getElementById('employeeValidationMsg');

    // Reset state
    employeeVerified = false;
    document.getElementById('employeeId').value = '';
    document.getElementById('remainingDays').value = '0';
    document.getElementById('remainingDaysDisplay').innerText = 'Not verified';
    validationMsg.style.color = '#666';
    validationMsg.innerText = '';

    if (employeeCode.length < 3) return;

    // Trigger verification
    await verifyEmployee(employeeCode);
}, 500));

// Debounce helper
function debounce(fn, delay) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn(...args), delay);
    };
}

async function verifyEmployee(employeeCode) {
    const validationMsg = document.getElementById('employeeValidationMsg');
    validationMsg.style.color = '#666';
    validationMsg.innerText = 'Verifying employee...';

    try {
        const response = await fetch(`${API_BASE_URL}/api/employees/verify-employee/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || '' // fallback if cookie missing
            },
            body: JSON.stringify({ employee_id: employeeCode }),
            credentials: 'include' // ensures cookies are sent/received even in incognito
        });

        let result;
        try {
            result = await response.json();
        } catch {
            validationMsg.style.color = 'red';
            validationMsg.innerText = '✗ Server returned an invalid response';
            return;
        }

        if (response.ok && result.success) {
            employeeVerified = true;
            document.getElementById('employeeId').value = result.employee_id; // internal DB id
            document.getElementById('remainingDays').value = result.remaining_days;
            document.getElementById('remainingDaysDisplay').innerText = result.remaining_days;

            // Show full name field
            document.getElementById('employeeName').value = result.full_name;
            document.getElementById('fullNameGroup').style.display = 'block';

            validationMsg.style.color = 'green';
            validationMsg.innerText = `✓ Employee verified (${result.employee_code})`;
        } else {
            // Reset fields on failure
            employeeVerified = false;
            document.getElementById('employeeId').value = '';
            document.getElementById('remainingDays').value = '0';
            document.getElementById('remainingDaysDisplay').innerText = 'Not verified';

            validationMsg.style.color = 'red';
            validationMsg.innerText = result.message || '✗ Employee not found in records';
        }
    } catch (error) {
        console.error('Error verifying employee:', error);
        validationMsg.style.color = 'red';
        validationMsg.innerText = '✗ Error verifying employee';
    }
}


document.getElementById('leaveType').addEventListener('change', function() {
    const vacationGroup = document.getElementById('vacationLocationGroup');
    const sickGroup = document.getElementById('sickLocationGroup');
    const vacationSelect = document.getElementById('vacationLocation');
    const sickSelect = document.getElementById('sickLocation');

    vacationGroup.style.display = 'none';
    sickGroup.style.display = 'none';
    vacationSelect.value = '';
    sickSelect.value = '';
    vacationSelect.removeAttribute('required');
    sickSelect.removeAttribute('required');

    if (this.value === 'vacation') {
        vacationGroup.style.display = 'block';
        vacationSelect.setAttribute('required', 'required');
    } else if (this.value === 'sick') {
        sickGroup.style.display = 'block';
        sickSelect.setAttribute('required', 'required');
    }
});

// ---------------- Form Validation ----------------
const formFields = document.querySelectorAll('input[required], select[required]');
formFields.forEach(field => {
    field.addEventListener('blur', () => validateField(field));
    field.addEventListener('input', () => {
        if (field.classList.contains('error')) validateField(field);
    });
});

// Real-time remaining days validation
document.getElementById('numberOfDays').addEventListener('input', function() {
    const numberOfDays = parseInt(this.value, 10) || 0;
    const remainingDays = parseInt(document.getElementById('remainingDays').value, 10) || 0;
    const errorMsg = this.parentElement.querySelector('.error-message');
    
    if (numberOfDays > 15) {
        this.classList.add('error');
        if (errorMsg) {
            errorMsg.innerText = 'Maximum 15 days per leave application';
            errorMsg.classList.add('show');
        }
    } else if (numberOfDays > remainingDays && employeeVerified) {
        this.classList.add('error');
        if (errorMsg) {
            errorMsg.innerText = `You only have ${remainingDays} days remaining`;
            errorMsg.classList.add('show');
        }
    } else if (numberOfDays < 1) {
        this.classList.add('error');
        if (errorMsg) {
            errorMsg.innerText = 'Number of days must be at least 1';
            errorMsg.classList.add('show');
        }
    } else {
        this.classList.remove('error');
        if (errorMsg) errorMsg.classList.remove('show');
    }
});

// ---------------- Form Submission ----------------
document.getElementById('leaveApplicationForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    // Check if employee is verified
    if (!employeeVerified) {
        alert('Please enter a valid employee name. The name must match our records exactly.');
        document.getElementById('employeeName').focus();
        return;
    }

    let isValid = true;
    formFields.forEach(field => {
        if (!validateField(field)) isValid = false;
    });

    const numberOfDays = parseInt(document.getElementById('numberOfDays').value, 10);
    const remainingDays = parseInt(document.getElementById('remainingDays').value, 10);

    // Validate number of days
    if (numberOfDays > 15) {
        alert('Maximum leave application is 15 days per request.');
        isValid = false;
    }

    if (numberOfDays > remainingDays) {
        alert(`You only have ${remainingDays} remaining leave days this year. Please adjust your request.`);
        isValid = false;
    }

    if (numberOfDays < 1) {
        alert('Number of days must be at least 1.');
        isValid = false;
    }

    if (!isValid) {
        alert('Please fill in all required fields correctly.');
        return;
    }

    const formData = new FormData(this);
    const data = {};
    
    // Convert FormData to JSON, excluding empty optional fields
    formData.forEach((value, key) => {
        if (value !== '' && value !== null && key !== 'full_name') {
            data[key] = value;
        }
    });

    // Ensure employee ID is included
    const employeeId = document.getElementById('employeeId').value;
    if (!employeeId) {
        alert('Employee verification failed. Please re-enter your name.');
        return;
    }
    data['employee'] = employeeId;

    const submitButton = document.getElementById('submitButton');
    const loadingScreen = document.getElementById('loadingScreen');

    submitButton.disabled = true;
    submitButton.innerHTML = 'SUBMITTING<span class="loading"></span>';
    loadingScreen.style.display = 'flex';

    try {
        const response = await fetch(`${API_BASE_URL}/api/leave-applications/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data),
            credentials: 'same-origin'
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // Show success message
            const successMsg = document.getElementById('successMessage');
            successMsg.classList.add('show');
            
            // Reset form
            this.reset();
            employeeVerified = false;
            document.getElementById('employeeId').value = '';
            document.getElementById('remainingDays').value = '0';
            document.getElementById('remainingDaysDisplay').innerText = 'Not verified';
            document.getElementById('employeeValidationMsg').innerText = '';
            
            // Hide conditional fields
            document.getElementById('vacationLocationGroup').style.display = 'none';
            document.getElementById('sickLocationGroup').style.display = 'none';
            
            // Hide success message after 5 seconds
            setTimeout(() => {
                successMsg.classList.remove('show');
            }, 5000);
            
        } else {
            const errorMessage = result.message || result.errors || 'Failed to submit application';
            
            // Handle specific error messages
            if (typeof errorMessage === 'string' && errorMessage.includes('not found')) {
                alert('Error: Employee not found in our records. Please verify your name.');
            } else if (typeof errorMessage === 'string' && errorMessage.includes('remaining days')) {
                alert('Error: ' + errorMessage);
            } else {
                alert('Error: ' + (typeof errorMessage === 'object' ? JSON.stringify(errorMessage) : errorMessage));
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while submitting the form. Please try again.');
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = 'SUBMIT APPLICATION';
        loadingScreen.style.display = 'none';
    }
});

// ---------------- Helper Functions ----------------
function validateField(field) {
    const errorMessage = field.parentElement.querySelector('.error-message');

    // Skip validation for hidden fields
    if (field.offsetParent === null) {
        return true;
    }

    if (field.hasAttribute('required') && !field.value.trim()) {
        field.classList.add('error');
        if (errorMessage) errorMessage.classList.add('show');
        return false;
    } else {
        field.classList.remove('error');
        if (errorMessage) errorMessage.classList.remove('show');
        return true;
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(cookie => {
            const c = cookie.trim();
            if (c.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}
