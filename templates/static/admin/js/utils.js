function getCsrfTokenHeaders() {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    return {
        "Accept": "application/json; charset=utf-8",
        "X-CSRFToken": csrftoken
    };
}

$.csrfToken = getCsrfTokenHeaders