const authToken = getCookie('csrftoken');

function showLoader() {
  const loader = document.getElementById('globalLoadingModal');
  if (loader) loader.style.display = 'flex';
}

function hideLoader() {
  const loader = document.getElementById('globalLoadingModal');
  if (loader) loader.style.display = 'none';
}

function LoadOtherPositions() {
  showLoader();
  fetch(`${API_BASE}/positions/`, {
    headers: {
      "Authorization": `Bearer ${authToken}`
    }
  })
  .then(res => res.json())
  .then(data => {
    const list = document.getElementById("positions_list");
    list.innerHTML = "";

    renderPositions(data);

    const searchInput = document.getElementById("positionSearch");
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        const term = searchInput.value.toLowerCase();
        const filtered = data.filter(pos =>
          pos.title.toLowerCase().includes(term) ||
          pos.code.toLowerCase().includes(term) ||
          (pos.description && pos.description.toLowerCase().includes(term))
        );
        renderPositions(filtered);
      });
    }
  })
  .catch(() => alert("Error loading positions"))
  .finally(() => hideLoader());
}

function renderPositions(positions) {
  const list = document.getElementById("positions_list");
  list.innerHTML = "";
  positions.forEach(pos => {
    const div = document.createElement("div");
    div.classList.add("position-item");
    div.innerHTML = `
      <label>Title:</label>
      <input type="text" class="pos-title" value="${pos.title}" data-id="${pos.id}" /><br>
      <label>Code:</label>
      <input type="text" class="pos-code" value="${pos.code}" data-id="${pos.id}" /><br>
      <label>Description:</label>
      <textarea style="height: 140px" class="pos-desc" data-id="${pos.id}">${pos.description || ""}</textarea><br>
      <button style="border-radius: 12px; background: green;" class="save-btn" data-id="${pos.id}">UPDATE</button>
      <button style="background: red;" class="delete-btn" data-id="${pos.id}">DELETE</button>
      <hr>
    `;
    list.appendChild(div);
  });

  document.querySelectorAll(".save-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const title = document.querySelector(`.pos-title[data-id="${id}"]`).value;
      const code = document.querySelector(`.pos-code[data-id="${id}"]`).value;
      const description = document.querySelector(`.pos-desc[data-id="${id}"]`).value;
      showLoader();
      fetch(`${API_BASE}/positions/update/${id}/`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`
        },
        body: JSON.stringify({ title, code, description })
      })
      .then(res => res.json())
      .then(resp => {
        alert(resp.message || "Updated successfully");
        setTimeout(() => location.reload(), 5000);
      })
      .catch(() => alert("Error updating position"))
      .finally(() => hideLoader());
    });
  });

  document.querySelectorAll(".delete-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      if (!confirm("Are you sure you want to delete this position?")) return;
      showLoader();
      fetch(`${API_BASE}/positions/delete/${id}/`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${authToken}`
        }
      })
      .then(async res => {
        const resp = await res.json().catch(() => ({}));
        if (!res.ok) {
          alert(resp.message || "Error deleting position");
        } else {
          alert(resp.message || "Deleted successfully");
          btn.parentElement.remove();
        }
      })
      .catch(() => alert("Error deleting position"))
      .finally(() => hideLoader());
    });
  });
}

function openHiddenDiv() {
  document.getElementById("hiddenDiv").style.display = "flex";
  LoadOtherPositions();
}

function closeHiddenDiv() {
  document.getElementById("hiddenDiv").style.display = "none";
}

document.getElementById("dept_position").addEventListener("click", openHiddenDiv);