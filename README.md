## 使用说明

### 准备工作


#### 1、首先在 [https://my.telegram.org/apps](https://my.telegram.org/apps) 登录获得
- api_id : 12345XXX (数字)
- api_hash: "xxxxx56sdffasda" (hash值)

#### 2、配置
##### 2.1 `config.json`配置
这部分可以不必改动
```json
{
  "debug": true,
  "proxy_type": "http",
  "proxy_ip": "127.0.0.1",
  "proxy_port": 7890,
  "def_commute_is_open": false,
  "def_commute_start_msg": "请稍后，正在快马加鞭赶来",
  "def_commute_end_msg": "客服不在线，请稍后再试"
}
```
- `debug` : 是否debug模式，主要用于debug下会使用读取proxy_x的值进行代理，*本地调试时使用*
- `proxy_type` : 代理类型（http/socks5）
- `proxy_ip` : 代理ip，本地电脑的代理为`127.0.0.1`
- `proxy_port` : 代理ip，本地电脑的代理的端口，如果时crash正常是: 7890 v2ray一般是: 1080
- `def_commute_is_open` : 兜底数据，是否上班状态，仅在未获取到用户配置的值时使用（正常情况下不可能会使用到这个）
- `def_commute_start_msg` : 兜底数据，上班文案，仅在未获取到用户配置的值时使用（正常情况下不可能会使用到这个）
- `def_commute_end_msg` : 兜底数据，下班文案，仅在未获取到用户配置的值时使用（正常情况下不可能会使用到这个）

#### 2.2 环境变量配置 `.env`
下面配置也可以不用改动，如果需要自定义web的登录密码，可以修改下面的账号和密码，目前配置仅有一个web账号
``
DEBUG=False
ADMIN_USERNAME=admin_100
ADMIN_PASSWORD=admin_100
``
- `ADMIN_USERNAME` : 用于web登录的用户名
- `ADMIN_PASSWORD` : 用于web登录的密码

### 3、注册Heroku
[https://id.heroku.com/login](https://id.heroku.com/login)

heroku 免费账户每个月可以使用550小时，大约时22天左右，如果无法满足一个月运行，可以注册多个账号。

最近收到heroku的通知消息：heroku免费容器会在2022-11-28停用免费容器，即到时候无法使用免费的容器了，可选择购买付费
目前了解到的dyno价格为25美元一个月

注意：如果有两个账号的时候，切换账号运行的时候，需要到heroku控制台，停止掉项目，保证一次只运行一个

#### 3.1 使用heroku

- 下载脚手架
[heroku-cli 说明与下载方式](https://devcenter.heroku.com/articles/heroku-cli)

下载安装完成后，打开命令行使用heroku进行登录，复制以下命令到cmd中，heroku会跳转到浏览器登录

```shell
$ heroku login
heroku: Press any key to open up the browser to login or q to exit
 ›   Warning: If browser does not open, visit
 ›   https://cli-auth.heroku.com/auth/browser/***
heroku: Waiting for login...
Logging in... done
Logged in as me@example.com
```
如果跳转浏览器登录失败了，可以使用 `heroku login -i` 方式进行登录（跳转浏览器登录成功后可不看这一步）
```shell
$ heroku login -i
heroku: Enter your login credentials
Email: me@example.com
Password: ***************
Two-factor code: ********
Logged in as me@heroku.com
```

#### 3.2 进入到项目目录中

如（具体看自己的目录）：
```shell
cd D:\Project\web_tg_chat
```

进入到目录后，执行 heroku create：
```shell
$ D:\Project\web_tg_chat> 
```

执行 `heroku create`命令
```shell
$ D:\Project\web_tg_chat> heroku create
Creating app... done,  serene-caverns-82714
https://serene-caverns-82714.herokuapp.com/ | https://git.heroku.com/serene-caverns-82714.git
```
执行 `git push heroku main`命令 (如果没有git命令，需要安装一个git [git下载](https://git-scm.com/downloads))
```shell
$ D:\Project\web_tg_chat> git push heroku main
Enumerating objects: 708, done.
Counting objects: 100% (708/708), done.
Delta compression using up to 8 threads
Compressing objects: 100% (311/311), done.
Writing objects: 100% (708/708), 128.11 KiB | 64.05 MiB/s, done.
Total 708 (delta 352), reused 708 (delta 352), pack-reused 0
remote: Compressing source files... done.
remote: Building source:
remote:
remote: -----> Building on the Heroku-22 stack
remote: -----> Determining which buildpack to use for this app
remote: -----> Python app detected
remote: -----> Using Python version specified in runtime.txt
remote: -----> Installing python-3.10.6
remote: -----> Installing pip 22.1.2, setuptools 60.10.0 and wheel 0.37.1
remote: -----> Installing SQLite3
remote: -----> Installing requirements with pip
remote:        Collecting django<5.0,>=4.0
remote:          Downloading Django-4.1-py3-none-any.whl (8.1 MB)
remote:        Collecting gunicorn<21.0,>=20.0
remote:          Downloading gunicorn-20.1.0-py3-none-any.whl (79 kB)
remote:        Collecting dj-database-url<2.0,>=1.0
remote:          Downloading dj_database_url-1.0.0-py3-none-any.whl (6.6 kB)
remote:        Collecting whitenoise<7.0,>=6.0
remote:          Downloading whitenoise-6.2.0-py3-none-any.whl (19 kB)
remote:        Collecting psycopg2<3.0,>=2.0
remote:          Downloading psycopg2-2.9.3.tar.gz (380 kB)
remote:          Preparing metadata (setup.py): started
remote:          Preparing metadata (setup.py): finished with status 'done'
remote:        Collecting sqlparse>=0.2.2
remote:          Downloading sqlparse-0.4.2-py3-none-any.whl (42 kB)
remote:        Collecting asgiref<4,>=3.5.2
remote:          Downloading asgiref-3.5.2-py3-none-any.whl (22 kB)
remote:        Building wheels for collected packages: psycopg2
remote:          Building wheel for psycopg2 (setup.py): started
remote:          Building wheel for psycopg2 (setup.py): finished with status 'done'
remote:          Created wheel for psycopg2: filename=psycopg2-2.9.3-cp310-cp310-linux_x86_64.whl size=159240 sha256=3399f4acef86b87602002c03ed36cdabaf0a70abc8fa3f412196a8a3d34715c0
remote:          Stored in directory: /tmp/pip-ephem-wheel-cache-7q6yuegd/wheels/81/b6/3d/091aad3e8919ea76c84c2674b02ce3ab52de882e091c39249e
remote:        Successfully built psycopg2
remote:        Installing collected packages: whitenoise, sqlparse, psycopg2, gunicorn, asgiref, django, dj-database-url
remote:        Successfully installed asgiref-3.5.2 dj-database-url-1.0.0 django-4.1 gunicorn-20.1.0 psycopg2-2.9.3 sqlparse-0.4.2 whitenoise-6.2.0
remote: -----> $ python manage.py collectstatic --noinput
remote:        131 static files copied to '/tmp/build_b1795ac0/staticfiles', 385 post-processed.
remote:
remote: -----> Discovering process types
remote:        Procfile declares types -> web
remote:
remote: -----> Compressing...
remote:        Done: 29.3M
remote: -----> Launching...
remote:        Released v5
remote:        https://serene-caverns-82714.herokuapp.com/ deployed to Heroku
remote:
remote: Verifying deploy... done.
To https://git.heroku.com/serene-caverns-82714.git
 * [new branch]      main -> main
```

获取tg的session
```
$ D:\Project\web_tg_chat> heroku run python debug_get_tg_session.py
Running python debug_get_tg_session.py on  stormy-sands-06242... up, run.9005 (Free)

请输入从 my.telegram.org 获得的参数 【api_id】【api_hash】

输入api_id:

```

检查项目是否在运行
```shell
$ D:\Project\web_tg_chat> heroku ps:scale web=1
```

打开网页

```shell
$ D:\Project\web_tg_chat> heroku open
```

ps: 如果项目无法打开，可使用命令 `heroku logs --tail` 查看运行日志


```shell
# 停止所有docker容器
docker stop $(docker ps -a -q)
# 进入容器
docker exec -it <id> /bin/bash
# 重启容器
docker restart <id>
```