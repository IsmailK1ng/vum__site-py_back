function updateField(selectElement, fieldName, objectId) {
    const value = selectElement.value;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(`/admin/main/kgfeedback/${objectId}/change/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: `${fieldName}=${value}`
    }).then(() => {
        selectElement.style.transform = 'scale(1.1)';
        setTimeout(() => {
            selectElement.style.transform = 'scale(1)';
        }, 200);
    });
}