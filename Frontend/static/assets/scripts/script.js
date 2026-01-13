//const API_BASE = "https://kt2980zx-8000.asse.devtunnels.ms";

document.querySelectorAll(".letter").forEach((el, i) => {
  el.style.setProperty("--i", i);
  el.addEventListener("animationend", () => {
    el.style.opacity = "1";
    el.style.transform = "scale(1) rotateX(0deg)";
  });
});

document.querySelectorAll(".tag-word").forEach((el, j) => {
  el.style.setProperty("--j", j);
});

function GotoForm() {
  window.location.href = "/appointment_form/";
}

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

function toggleDropdown() {
  const dropdown = document.getElementById('adminDropdown');
  dropdown.classList.toggle('show');
}

document.addEventListener('click', function(event) {
  const dropdown = document.getElementById('adminDropdown');
  const dropdownContainer = document.querySelector('.admin-dropdown-container');
  
  if (dropdown && dropdownContainer && !dropdownContainer.contains(event.target)) {
    dropdown.classList.remove('show');
  }
});

let hrFailedAttempts = 0;
let hrLockUntil = null;
let hrCountdownInterval = null;

function showHRLogin() {
  const modal = document.getElementById('loginModalHR');
  modal.style.display = 'flex';
  document.getElementById('adminDropdown').classList.remove('show');
  
  document.getElementById('loginMessageHR').textContent = '';
}

function closeHRLogin() {
  const modal = document.getElementById('loginModalHR');
  modal.style.display = 'none';
  document.getElementById('usernameHR').value = '';
  document.getElementById('passwordHR').value = '';
  document.getElementById('loginMessageHR').textContent = '';

  if (hrCountdownInterval) {
    clearInterval(hrCountdownInterval);
    hrCountdownInterval = null;
  }
  
  document.getElementById('usernameHR').disabled = false;
  document.getElementById('passwordHR').disabled = false;
}

async function validateHRLogin() {
  const now = new Date().getTime();
  const messageEl = document.getElementById('loginMessageHR');

  if (hrLockUntil && now < hrLockUntil) {
    return;
  }

  const username = document.getElementById('usernameHR').value;
  const password = document.getElementById('passwordHR').value;

  if (!username || !password) {
    messageEl.textContent = 'Please fill in all fields';
    messageEl.style.color = '#ff0000';
    return;
  }

  document.getElementById('loadingModal').style.display = "flex";

  try {
    const response = await fetch("/hr_login/", { 
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie('csrftoken')
      },
      body: JSON.stringify({ username, password }),
      credentials: 'same-origin'
    });

    const result = await response.json();

    if (result.success) {
      hrFailedAttempts = 0;

      localStorage.setItem('hrData', JSON.stringify({
        username: result.username,
        full_name: result.full_name,
        photo_url: result.photo_url
      }));

      messageEl.textContent = 'Login successful! Redirecting...';
      messageEl.style.color = '#28a745';

      setTimeout(() => {
        window.location.href = "/hr_dashboard/";
      }, 1000);
    } else {
      hrFailedAttempts++;
      if (hrFailedAttempts >= 3) {
        hrLockUntil = now + 60 * 1000;
        startHRCountdown(60);
        hrFailedAttempts = 0;
      } else {
        messageEl.textContent = result.message || `Invalid credentials. ${3 - hrFailedAttempts} attempt(s) remaining.`;
        messageEl.style.color = '#ff0000';
      }
    }
  } catch (error) {
    console.error('HR Login Error:', error);
    messageEl.textContent = "Error connecting to server. Please try again.";
    messageEl.style.color = '#ff0000';
  } finally {
    document.getElementById('loadingModal').style.display = "none";
  }
}

function startHRCountdown(seconds) {
  const messageEl = document.getElementById("loginMessageHR");
  let remaining = seconds;

  document.getElementById("usernameHR").disabled = true;
  document.getElementById("passwordHR").disabled = true;

  messageEl.style.color = "#ff0000";
  messageEl.textContent = `Too many failed attempts. Try again in ${remaining}s`;

  hrCountdownInterval = setInterval(() => {
    remaining--;
    if (remaining > 0) {
      messageEl.textContent = `Too many failed attempts. Try again in ${remaining}s`;
    } else {
      clearInterval(hrCountdownInterval);
      hrCountdownInterval = null;
      messageEl.textContent = "";
      document.getElementById("usernameHR").disabled = false;
      document.getElementById("passwordHR").disabled = false;
      hrLockUntil = null;
    }
  }, 1000);
}

let deanFailedAttempts = 0;
let deanLockUntil = null;
let deanCountdownInterval = null;

function showDeanLogin() {
  const modal = document.getElementById('loginModalDean');
  modal.style.display = 'flex';
  document.getElementById('adminDropdown').classList.remove('show');
  
  document.getElementById('loginMessageDean').textContent = '';
}

function closeDeanLogin() {
  const modal = document.getElementById('loginModalDean');
  modal.style.display = 'none';
  document.getElementById('usernameDean').value = '';
  document.getElementById('passwordDean').value = '';
  document.getElementById('loginMessageDean').textContent = '';
  
  if (deanCountdownInterval) {
    clearInterval(deanCountdownInterval);
    deanCountdownInterval = null;
  }
  
  document.getElementById('usernameDean').disabled = false;
  document.getElementById('passwordDean').disabled = false;
}

async function validateDeanLogin() {
  const now = new Date().getTime();
  const messageEl = document.getElementById('loginMessageDean');
  
  if (deanLockUntil && now < deanLockUntil) {
    return;
  }

  const username = document.getElementById('usernameDean').value;
  const password = document.getElementById('passwordDean').value;

  if (!username || !password) {
    messageEl.textContent = 'Please fill in all fields';
    messageEl.style.color = '#ff0000';
    return;
  }

  document.getElementById('loadingModal').style.display = 'flex';

  try {
    const response = await fetch("/api/dean-login/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie('csrftoken')
      },
      body: JSON.stringify({ username: username, password: password }),
      credentials: 'same-origin'
    });

    const result = await response.json();

    if (result.success) {
      deanFailedAttempts = 0;
      
      messageEl.textContent = 'Login successful! Redirecting...';
      messageEl.style.color = '#28a745';
      
      setTimeout(() => {
        window.location.href = "/dean_dashboard/";
      }, 1000);
    } else {
      deanFailedAttempts++;
      
      if (deanFailedAttempts >= 3) {
        deanLockUntil = now + 60 * 1000;
        startDeanCountdown(60);
        deanFailedAttempts = 0;
      } else {
        messageEl.textContent = result.message || `Invalid credentials. ${3 - deanFailedAttempts} attempt(s) remaining.`;
        messageEl.style.color = '#ff0000';
      }
    }
  } catch (error) {
    console.error('Dean Login Error:', error);
    messageEl.textContent = "Error connecting to server. Please try again.";
    messageEl.style.color = '#ff0000';
  } finally {
    document.getElementById('loadingModal').style.display = 'none';
  }
}

function startDeanCountdown(seconds) {
  const messageEl = document.getElementById("loginMessageDean");
  let remaining = seconds;

  document.getElementById("usernameDean").disabled = true;
  document.getElementById("passwordDean").disabled = true;

  messageEl.style.color = "#ff0000";
  messageEl.textContent = `Too many failed attempts. Try again in ${remaining}s`;

  deanCountdownInterval = setInterval(() => {
    remaining--;
    if (remaining > 0) {
      messageEl.textContent = `Too many failed attempts. Try again in ${remaining}s`;
    } else {
      clearInterval(deanCountdownInterval);
      deanCountdownInterval = null;
      messageEl.textContent = "";
      document.getElementById("usernameDean").disabled = false;
      document.getElementById("passwordDean").disabled = false;
      deanLockUntil = null;
    }
  }, 1000);
}

window.onclick = function(event) {
  const hrModal = document.getElementById('loginModalHR');
  const deanModal = document.getElementById('loginModalDean');
  
  if (event.target === hrModal) {
    closeHRLogin();
  }
  if (event.target === deanModal) {
    closeDeanLogin();
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const hrUsernameInput = document.getElementById('usernameHR');
  const hrPasswordInput = document.getElementById('passwordHR');
  
  if (hrUsernameInput && hrPasswordInput) {
    [hrUsernameInput, hrPasswordInput].forEach(input => {
      input.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          validateHRLogin();
        }
      });
    });
  }
  
  const deanUsernameInput = document.getElementById('usernameDean');
  const deanPasswordInput = document.getElementById('passwordDean');
  
  if (deanUsernameInput && deanPasswordInput) {
    [deanUsernameInput, deanPasswordInput].forEach(input => {
      input.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          validateDeanLogin();
        }
      });
    });
  }
});