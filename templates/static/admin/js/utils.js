function getCsrfTokenHeaders() {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    return {
        "Accept": "application/json; charset=utf-8",
        "X-CSRFToken": csrftoken
    };
}

$.csrfToken = getCsrfTokenHeaders

function debounce(func, timeout = 1000){
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => { func.apply(this, args); }, timeout);
  };
}