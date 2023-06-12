layui.define(["jquery", "element", 'layer'], function (exports) {
    const $ = layui.jquery;
    const element = layui.element
    const layer = layui.layer
    const tabLayFilter = "menu_tab"

    const frameTabIdAttr = "tab-id"
    const frameClsAttr = "tab_frame"

    function resizeIFrame() {
        let h = $(window).height() - 100;
        console.log("resizeIFrame window = ", $(window).height())
        console.log("resizeIFrame h = ", h)
        $("iframe").css("height", h + "px");
    }

    function initTabRightButton(id) {
        //取消右键
        // const tab_op_menu = $('.layui-tab-title li')
        // tab_op_menu.on('contextmenu', function () {
        //     return false;
        // })
        // $('.layui-tab-title,.layui-tab-title li').on('click', function () {
        //     $('.rightMenu').hide();
        // });
        //
        // //桌面点击右击
        // tab_op_menu.on('contextmenu', function (e) {
        //     const aid = $(this).attr("lay-id"); //获取右键时li的lay-id属性
        //     const popupmenu = $(".rightMenu");
        //     popupmenu.find("li").attr("data-id", aid);
        //     console.log("popopmenuId:" + popupmenu.find("li").attr("data-id"));
        //     l = ($(document).width() - e.clientX) < popupmenu.width() ? (e.clientX - popupmenu.width()) : e.clientX;
        //     t = ($(document).height() - e.clientY) < popupmenu.height() ? (e.clientY - popupmenu.height()) : e.clientY;
        //     popupmenu.css({
        //         left: l,
        //         top: t
        //     }).show();
        //
        //     //alert("右键菜单")
        //     return false;
        // });
    }

    const tab = {
        tempTab: [],

        add: function (id, title, url) {
            //判断当前id的元素是否存在于tab中
            let li = $("#menu_tab_id li[lay-id=" + id + "]").length;
            console.log("li is empty >> ", li);
            if (li > 0) {
                this.change(id)
                return;
            }
            const content = `<iframe class="${frameClsAttr}" name="frame_content_${id}" ${frameTabIdAttr}="${id}" width="100%"
frameborder="0" src="${url}" scrolling="auto" style="height: 100%"></iframe>`;
            element.tabAdd(tabLayFilter, {
                id: id,
                title: title,
                content: content
            })
            tab.tempTab.push({
                id: id,
                title: title,
                url: url,
            })
            initTabRightButton();
            resizeIFrame();
        },
        delete: function (id) {
            element.tabDelete(tabLayFilter, id)
        },
        deleteAll: function (){

        },
        change: function (id) {
            element.tabChange(tabLayFilter, id)
            resizeIFrame();
        },
        exists: function (id) {
            for (let tab in this.tempTab) {
                if (tab.id == id) {
                    return true;
                }
            }
            return false;
        }
    };

    $(".tab_nav_a").each(function (index) {
        let self = $(this);
        let url = self.attr("href");
        let title = self.html();
        index = index + 1;
        console.log("注册导航栏点击跳转iframe事件, id = ", index, ", title = ", title, ", url = ", url);
        if (url !== undefined && url !== '' && url.indexOf("javascript") === -1) {
            self.attr({
                "target": "frame_content_" + index,
                "nav_index": index,
            });
            self.on("click", function (event) {
                let navIndex = self.attr("nav_index");
                let frames = $(`.${frameClsAttr}`);
                for (let i = 0; i < frames.length; i++) {
                    if (frames.eq(i).attr(frameTabIdAttr) === navIndex) {
                        console.log("存在iframe窗口，切换到窗口");
                        tab.change(navIndex);
                        event.stopPropagation();
                        return;
                    }
                }

                tab.add(navIndex, title, url)
                tab.change(navIndex)
                event.stopPropagation()
            })
        }
    })

    element.on(`tabDelete(${tabLayFilter})`, function (data) {
        console.log("监听到tab栏被删除 data = ", data);
    });

    element.on(`tab(${tabLayFilter})`, function (data) {
        console.log("监听到tab栏被改变 data = ", data);
    });

    $("#rightMenu li").click(function () {
        const type = $(this).attr("data-type");
        const layId = $(this).attr("data-id")
        if (type == "current") {
            //console.log("close this:" + layId);
            tab.delete(layId);
        } else if (type == "all") {
            //console.log("closeAll");
            const tabtitle = $(".layui-tab-title li");
            const ids = new Array();
            $.each(tabtitle, function (i) {
                ids[i] = $(this).attr("lay-id");
            })
            tab.deleteAll(ids);
        } else if (type == "fresh") {
            //console.log("fresh:" + layId);
            tab.change($(this).attr("data-id"));
            const othis = $('.layui-tab-title').find('>li[lay-id="' + layId + '"]'),
                index = othis.parent().children('li').index(othis),
                parents = othis.parents('.layui-tab').eq(0),
                item = parents.children('.layui-tab-content').children('.layui-tab-item'),
                src = item.eq(index).find('iframe').attr("src");
            item.eq(index).find('iframe').attr("src", src);
        } else if (type == "other") {
            const thisId = layId;
            $('.layui-tab-title').find('li').each(function (i, o) {
                var layId = $(o).attr('lay-id');
                if (layId != thisId && layId != 0) {
                    tab.delete(layId);
                }
            });
        }
        $('.rightMenu').hide();
    });

    exports("menu_tab", {
        tab: tab,
        resizeIFrame: resizeIFrame
    })
})