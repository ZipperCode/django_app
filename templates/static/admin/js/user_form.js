layui.use(['layer', 'form'], function () {
    const form = layui.form;
    const $ = layui.$;
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

    function openLayer(config) {
        layer.open({
            type: 2
            , title: config.title
            , content: config.url
            , area: [config.width ?? '420px', config.height ?? '420px']
            , btn: ['确定', '取消']
            , yes: function (index, layero) {
                const iframeWindow = window['layui-layer-iframe' + index]
                    , submitID = 'layer_submit'
                    , submit = layero.find('iframe').contents().find('#' + submitID);

                //监听提交
                iframeWindow.layui.form.on('submit(' + submitID + ')', function (data) {
                    config.formCallback(data, index)
                });
                submit.trigger('click');
            }
        });
    }

    $.openLayer = openLayer
});