function modifyPassword(layer, data, success) {
    console.log(typeof $);
    let username = data.username;
    let password = $.md5(data.password);
    let password_new = $.md5(data.password_new);
    let password_new2 = $.md5(data.password_new2);

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const headers = {
        "Accept": "application/json; charset=utf-8",
        "X-CSRFToken": csrftoken
    };
    console.log("password = " + password + ", password_new = " + password_new + ", password_new2 = " + password_new2);
    const load_index = layer.load(0);
    $.ajax({
        url: '/api/modify_pwd',
        type: 'post',
        dataType: 'JSON',
        headers:headers,
        data: {
            username,
            password,
            password_new,
            password_new2,
        },
        success: success,
        error() {
            layer.msg("网络错误，请重试", {icon: 2});
        },
        complete() {
            layer.close(load_index)
        }
    })
}