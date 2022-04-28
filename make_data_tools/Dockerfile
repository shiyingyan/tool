FROM influxdb:1.6.1 as influxdb
# FROM python:3.8
FROM python:3.8.12-slim-buster

RUN sed -i 's/archive.ubuntu.com/mirrors.163.com/g' /etc/apt/sources.list && \
    sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's|security.debian.org/debian-security|mirrors.ustc.edu.cn/debian-security|g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y procps && \
    apt-get install -y inetutils-ping && \
    apt-get install -y vim && \
    apt-get install -y nano && \
    apt-get install -y telnet && \
    apt-get install -y psmisc

COPY --from=influxdb /usr/bin/influx /usr/bin

WORKDIR /opt/demo
# COPY *.py requirements.txt *.xlsx config /opt/demo/
COPY . .

ENV PYTHONPATH /opt/demo
RUN pip3 install -r requirements.txt -i https://pypi.doubanio.com/simple --trusted-host=pypi.doubanio.com

CMD ["python3","main.py"]
