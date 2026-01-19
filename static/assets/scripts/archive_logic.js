async function archiveLeaveRequest(requestId) {
    const response = await fetch(`/api/leave-requests/${requestId}/archive/`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
        }
    });
    const result = await response.json();
    console.log(result);
}