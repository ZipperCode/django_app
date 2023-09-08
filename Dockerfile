# 建立 python3.10 环境
FROM python:3.11

# ensure local python is preferred over distribution python
ENV PATH /usr/local/bin:$PATH

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

ENV PYTHON_VERSION 3.9.1
ENV IN_DOCKER 1

ADD jdk-11.0.1_linux-x64_bin.tar.gz /usr/local/java

# RUN tar -czvf /usr/local/jdk-11.0.1_linux-x64_bin.tar.gz /usr/local/java

ENV JAVA_HOME /usr/local/java/jdk-11.0_1
ENV CLASSPATH $JAVA_HOME/lib/dt.jar:$JAVA_HOME/lib/tools.jar
ENV PATH $PATH:$JAVA_HOME/bin
RUN ln -s /usr/local/java/jdk-11.0.1/bin/java /usr/bin/java


RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster main contrib non-free" > /etc/apt/sources.list
RUN echo "deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ buster main contrib non-free" >> /etc/apt/sources.list

# CMD [ "python3" , "--version"]
RUN apt-get update && apt-get upgrade -y
# 安装netcat
RUN apt install -y netcat-traditional
RUN apt install -y gcc && apt install -y python3-dev
RUN apt-get install -y vim

# 设置 python 环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 容器内创建 myproject 文件夹
ENV APP_HOME=/var/www/html/django_app
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# 将当前目录加入到工作目录中（. 表示当前目录）
ADD . $APP_HOME

#RUN pip3 config set global.index-url http://mirrors.aliyun.com/pypi/simple
#RUN pip3 config set install.trusted-host mirrors.aliyun.com
RUN pip3 install uwsgi

# 更新pip版本
RUN /usr/local/bin/python -m pip install --upgrade pip

# 安装项目依赖
RUN pip3 install -r requirements.txt

# 移除\r in windows
RUN sed -i 's/\r//' ./start.sh

# 给start.sh可执行权限
RUN chmod +x ./start.sh

# 数据迁移，并使用uwsgi启动服务
ENTRYPOINT /bin/bash ./start.sh