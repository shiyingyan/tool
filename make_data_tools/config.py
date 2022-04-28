# -*- coding: utf-8 -*-
# Created By Shing At 2022/4/20
import os, sys
import json

host = os.getenv('influxdb_host'.upper())
port = os.getenv('influxdb_port'.upper())
username = os.getenv('influxdb_username'.upper())
password = os.getenv('influxdb_password'.upper())

options = {
    # 'host': 'influxdb',
    'host': host or '10.162.138.19',  # scada服务器IP
    'port': port or '58086',  # influxdb访问端口号
    'username': username or 'root',  # influxdb登录用户名
    'password': password or 'root',  # influxdb登录密码
}

try:
    with open(os.path.join(os.curdir, 'config.json'), 'r', encoding='utf8') as f:
        options = json.load(f)
except:
    pass
