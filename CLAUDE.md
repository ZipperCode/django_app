# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 Django 4.1 的 Line/WhatsApp 账号分配管理后台系统，支持多平台（Line、WhatsApp 1-7、Line Pair）的账号 ID 和二维码的管理、分配、导出。

## 常用命令

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 启动开发服务器
python manage.py runserver

# 收集静态文件
python manage.py collectstatic --noinput
```

### Docker 部署
```bash
# 启动所有服务 (MySQL + Web + Nginx)
docker-compose up -d

# 查看日志
docker-compose logs -f web

# 重启 web 服务
docker-compose restart web
```

### Heroku 部署
```bash
heroku login
heroku create
git push heroku main
heroku ps:scale web=1
heroku open
heroku logs --tail
```

## 项目架构

### 目录结构
```
├── web_app/
│   ├── settings.py          # Django 配置
│   ├── urls.py              # 路由定义（API + 页面）
│   ├── wsgi.py / asgi.py    # 入口
│   ├── views.py             # 页面视图（渲染 HTML 模板）
│   ├── config/              # 初始化配置
│   ├── dao/                 # 数据访问层 (line_account_dao, user_dao, wa_dao, wa2_dao)
│   ├── decorators/          # 装饰器 (权限、POST验证、日志)
│   ├── forms/               # 表单验证
│   ├── middlewares/         # 中间件 (登录验证、异常处理)
│   ├── model/               # 数据模型 (accounts, users, wa_accounts 等)
│   ├── restfuls/            # REST API 接口 (user, account, wa, link 等)
│   ├── service/             # 业务逻辑层
│   └── util/                # 工具类 (dispatch, wa_util, rest_list_util)
├── templates/               # HTML 模板 + 静态文件
├── compose/                 # Docker 配置 (nginx, mysql, uwsgi)
├── Dockerfile               # 容器镜像 (Python 3.11 + JDK 11)
├── docker-compose.yml       # 多容器编排 (db + web + nginx)
└── start.sh                 # 容器启动脚本 (等待 MySQL -> 迁移 -> uwsgi)
```

### 三层架构
- **REST API 层** (`web_app/restfuls/`) - 处理 HTTP 请求，使用装饰器验证权限和参数
- **Service 层** (`web_app/service/`) - 业务逻辑处理
- **DAO 层** (`web_app/dao/`) - 直接数据库操作

### 数据模型
- `User` / `UserMenu` / `UserAccountRecord` - 用户、菜单权限、分配记录 (`web_app/model/users.py`)
- `LineAccount` 等 - Line 账号 ID/QR 模型 (`web_app/model/accounts.py`)
- `WaAccount` 系列 - WhatsApp 1-7 账号模型 (`web_app/model/wa_accounts*.py`)
- `Link` - 链接管理 (`web_app/model/link.py`)

### 用户角色
- `-1` 超级管理员 / `0` 管理员 / `1` 粉端账号 / `2` 业务员

### 业务类型 (back_type)
- Line (1), WhatsApp 1-7 (2-8), Line Pair (9)

### 路由约定
- `/admin/view/*` - 管理后台页面
- `/view/*` - 普通用户页面
- `/api/*` - REST API 接口（POST 为主，使用 `@api_post` 装饰器）

### 中间件
- `LoginMiddleware` - 拦截 `/view/auth/` 路径验证登录状态，`/api/` 和 `/media/` 放行
- `ExceptionMiddleware` - 全局异常处理

### 装饰器
- `@api_post` - 限制仅 POST 请求
- `@op_admin` - 管理员权限验证
- `@api_op_user` - 登录用户验证

### 数据库
- 默认使用 MySQL (`line` 库 / `contact` 库)
- Docker 环境下连接到 `db` 主机，本地开发连接 `127.0.0.1`
- 用户名: `root` / `telegram`，密码: `949389`

## 注意事项

- 项目使用 Session 认证，不使用 JWT
- CSRF 中间件已注释
- CORS 全放开 (`CORS_ORIGIN_ALLOW_ALL = True`)
- 静态文件通过 `/media/` 和 `/static/` 路径提供
- 部署时需先运行 `python manage.py migrate` 再启动 uwsgi
