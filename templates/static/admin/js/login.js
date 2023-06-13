/*
 +----------------------------------------------------------------------
 | login.js 后台登录javascript
 +----------------------------------------------------------------------
*/

layui.use(['layer', 'form'], function () {
    const layer = layui.layer;
    const form = layui.form;
    const $ = layui.$;

    /*表单提交验证*/
    form.verify({
        username: function (value, item) {
            if (!/^.+$/.test(value)) {
                $(item).focus();
                return '用户名不能为空';
            }
        },
        password: function (value, item) {   //密码验证
            if (!/^.+$/.test(value)) {
                $(item).focus();
                return '密码不能为空';
            }
            if (!/^[a-zA-Z\d\-_\.!@]{6,26}$/.test(value)) {
                $(item).focus();
                return '密码格式错误';
            }
        },
    });
    form.on('submit(api/login)', function (data) {
        //登录
        const load_index = layer.load(0);
        $.ajax({
            url: data.form.action,
            type: data.form.method,
            data: data.field,
            dataType: 'JSON',
            success(res) {
                if (res.code === 0) {  //登录成功
                    window.location = 'view/auth/index';
                    return;
                }
                layer.msg(res.msg, {icon: 2});
            },
            error() {
                layer.msg("网络错误，请重试", {icon: 2});
            },
            complete() {
                layer.close(load_index);
            }
        });
        return false;
    });
    form.render();
});