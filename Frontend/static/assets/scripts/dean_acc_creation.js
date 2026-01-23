const toggleDeanBtn = document.getElementById('toggleDeanFormBtn');
const deanDiv = document.getElementById('create-dean-div');

const closeDeanBtn = document.getElementById('closeDeanFormBtn');

closeDeanBtn.addEventListener('click', () => {
  deanDiv.classList.add('hidden');
});

toggleDeanBtn.addEventListener('click', () => {
  deanDiv.classList.toggle('hidden');
  if (!deanDiv.classList.contains('hidden')) {
    document.getElementById('dean-username').focus();
  }
});


fetch('/api/departments/')
  .then(res => res.json())
  .then(data => {
    const select = document.getElementById('dean-department');
    data.forEach(dep => {
      const option = document.createElement('option');
      option.value = dep.id;
      option.textContent = dep.name;
      select.appendChild(option);
    });
  });


const form = document.getElementById('create-dean-form');
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const payload = {
    username: document.getElementById('dean-username').value,
    password: document.getElementById('dean-password').value,
    full_name: document.getElementById('dean-fullname').value,
    department: document.getElementById('dean-department').value
  };

  const messageEl = document.getElementById('create-dean-message');

  try {
    showLoader();
    const res = await fetch('/api/create-dean/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (data.success) {
      messageEl.style.color = 'green';
      messageEl.textContent = data.message;
      form.reset();
      setTimeout(() => location.reload(), 1500);
    } else {
      messageEl.style.color = 'red';
      messageEl.textContent = data.message;
    }
  } catch (err) {
    messageEl.style.color = 'red';
    messageEl.textContent = 'Error: ' + err;
  } finally {
    hideLoader();
  }
});

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

function showLoader() {
  const loader = document.getElementById('globalLoadingModal');
  if (loader) loader.style.display = 'flex';
}

function hideLoader() {
  const loader = document.getElementById('globalLoadingModal');
  if (loader) loader.style.display = 'none';
}

function toggleChangeKeyModal() {
  const modal = document.getElementById("change-key-Modal");
  modal.style.display = (modal.style.display === "flex") ? "none" : "flex";
}


function submitSecretKey(keyId) {
  const keyInput = document.getElementById("secretKeyInput").value;
  const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/;

  if (!regex.test(keyInput)) {
    alert("Secret key must be at least 8 characters long and include uppercase, lowercase, numbers, and special characters.");
    return;
  }
  showLoader();
  fetch(`/access-key/${1}/update/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: JSON.stringify({ key: keyInput })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error("Failed to update secret key");
    }
    return response.json();
  })
  .then(data => {
    alert(data.message || "Secret key updated successfully!");
    toggleChangeKeyModal();
  })
  .catch(error => {
    alert("Error: " + error.message);
  })
  .finally(() => {
    hideLoader();
  });
}
