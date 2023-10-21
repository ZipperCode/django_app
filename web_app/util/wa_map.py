from web_app.model.users import USER_BACK_TYPE_WA, USER_BACK_TYPE_WA2, USER_BACK_TYPE_WA3, USER_BACK_TYPE_WA4, \
    USER_BACK_TYPE_WA5

MENU_MAP = {
    USER_BACK_TYPE_WA: {
        'title': "WhatsApp管理",
        "wa_id": {
            "path": f"/view/auth/wa/account_id/list?back_type={USER_BACK_TYPE_WA}",
            "name": "WA ID管理"
        },
        "wa_id_rec": {
            "path": f"/view/auth/wa/aid_record/list?back_type={USER_BACK_TYPE_WA}",
            "name": "WA ID分配数据"
        },
        "wa_qr": {
            "path": f"/view/auth/wa/account_qr/list?back_type={USER_BACK_TYPE_WA}",
            "name": "WA 二维码管理"
        },
        "wa_qr_rec": {
            "path": f"/view/auth/wa/qr_record/list?back_type={USER_BACK_TYPE_WA}",
            "name": "WA 二维码分配数据"
        },
    },
    USER_BACK_TYPE_WA2: {
        'title': "WhatsApp2管理",
        "wa_id": {
            "path": f"/view/auth/wa/account_id/list?back_type={USER_BACK_TYPE_WA2}",
            "name": "WA2 ID管理"
        },
        "wa_id_rec": {
            "path": f"/view/auth/wa/aid_record/list?back_type={USER_BACK_TYPE_WA2}",
            "name": "WA2 ID分配数据"
        },
        "wa_qr": {
            "path": f"/view/auth/wa/account_qr/list?back_type={USER_BACK_TYPE_WA2}",
            "name": "WA2 二维码管理"
        },
        "wa_qr_rec": {
            "path": f"/view/auth/wa/qr_record/list?back_type={USER_BACK_TYPE_WA2}",
            "name": "WA2 二维码分配数据"
        },
    },
    USER_BACK_TYPE_WA3: {
        'title': "WhatsApp3管理",
        "wa_id": {
            "path": f"/view/auth/wa/account_id/list?back_type={USER_BACK_TYPE_WA3}",
            "name": "WA3 ID管理"
        },
        "wa_id_rec": {
            "path": f"/view/auth/wa/aid_record/list?back_type={USER_BACK_TYPE_WA3}",
            "name": "WA3 ID分配数据"
        },
        "wa_qr": {
            "path": f"/view/auth/wa/account_qr/list?back_type={USER_BACK_TYPE_WA3}",
            "name": "WA3 二维码管理"
        },
        "wa_qr_rec": {
            "path": f"/view/auth/wa/qr_record/list?back_type={USER_BACK_TYPE_WA3}",
            "name": "WA3 二维码分配数据"
        },
    },
    USER_BACK_TYPE_WA4: {
        'title': "WhatsApp4管理",
        "wa_id": {
            "path": f"/view/auth/wa/account_id/list?back_type={USER_BACK_TYPE_WA4}",
            "name": "WA4 ID管理"
        },
        "wa_id_rec": {
            "path": f"/view/auth/wa/aid_record/list?back_type={USER_BACK_TYPE_WA4}",
            "name": "WA4 ID分配数据"
        },
        "wa_qr": {
            "path": f"/view/auth/wa/account_qr/list?back_type={USER_BACK_TYPE_WA4}",
            "name": "WA4 二维码管理"
        },
        "wa_qr_rec": {
            "path": f"/view/auth/wa/qr_record/list?back_type={USER_BACK_TYPE_WA4}",
            "name": "WA4 二维码分配数据"
        },
    },
    USER_BACK_TYPE_WA5: {
        'title': "WhatsApp5管理",
        "wa_id": {
            "path": f"/view/auth/wa/account_id/list?back_type={USER_BACK_TYPE_WA5}",
            "name": "WA5 ID管理"
        },
        "wa_id_rec": {
            "path": f"/view/auth/wa/aid_record/list?back_type={USER_BACK_TYPE_WA5}",
            "name": "WA5 ID分配数据"
        },
        "wa_qr": {
            "path": f"/view/auth/wa/account_qr/list?back_type={USER_BACK_TYPE_WA5}",
            "name": "WA5 二维码管理"
        },
        "wa_qr_rec": {
            "path": f"/view/auth/wa/qr_record/list?back_type={USER_BACK_TYPE_WA5}",
            "name": "WA5 二维码分配数据"
        },
    }
}
