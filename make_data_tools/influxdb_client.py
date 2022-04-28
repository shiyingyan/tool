# -*- coding: utf-8 -*-
# Created By Shing At 2022/4/22
import dataclasses

import requests

from requests.auth import HTTPBasicAuth
from typing import List


@dataclasses.dataclass
class RowData:
    time: int
    measurement: str
    tags: dict
    fields: dict


class InfluxdbClient:
    def __init__(self, host, port, username, password, precision='ms'):
        self.host = host
        self.port = port
        self.precision = precision
        self.session = requests.session()
        self.session.auth = HTTPBasicAuth(username, password)

    def make_url(self, query_or_write, **params):
        assert query_or_write in ['query', 'write'], 'influxdb仅支持两种方法query、write'
        ps = {
            'precision': self.precision
        }
        ps.update(params)
        return f'''http://{self.host}:{self.port}/{query_or_write}?{"&".join([k + '=' + v for k, v in ps.items()])} '''

    def request_core(self, query_or_write, data, **table_info):
        return self.session.post(self.make_url(query_or_write, **table_info), data, )

    def query(self, db, retention_policy, sql):
        r = self.request_core('query', {'q': sql}, **{
            'db': db,
            'rp': retention_policy,
        })
        if r.status_code == 200:
            print(f'{sql} successed')
            return r.content.decode('utf8')
        print(f'{sql} failed')
        print(r.__dict__)
        return ''

    def write(self, db, retention_policy, row_datas: List[RowData]):
        lines = [
            f'''{rd.measurement},{','.join([k + '=' + str(v) for k, v in rd.tags.items()])} {','.join([k + '=' + str(v) for k, v in rd.fields.items()])} {rd.time}'''
            for rd in row_datas]
        return self.write_core(db, retention_policy, lines)

    def write_json(self, db, retention_policy, json):
        if not isinstance(json, list):
            json = [json]
        return self.write(db, retention_policy, [RowData(**row) for row in json])

    def write_core(self, db, retention_policy, lines):
        if not isinstance(lines, list):
            lines = [lines]
        r = self.request_core('write', '\n'.join(lines).encode('utf8'), **{
            'db': db,
            'rp': retention_policy,
        })
        if r.status_code == 204:
            print(f'{lines} successed')
            return True
        print(f'{lines} failed')
        print(r.__dict__)
        return False
