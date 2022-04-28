#!/usr/bin/python3
# -*- coding:utf-8 -*-
import logging

from concurrent_log import ConcurrentTimedRotatingFileHandler
from influxdb import InfluxDBClient
from influxdb.resultset import ResultSet
from typing import List

from config import options
from tables import *


@dataclasses.dataclass
class Measurement:
    db: str
    rp: str
    name: str


@dataclasses.dataclass
class InfluxdbConnectionInfo:
    host: str
    port: str
    username: str
    password: str


@dataclasses.dataclass
class Turbine:
    name: str  # 01#,02# etc
    type: str  # 风机类型
    circle: str  # 集电线
    farm: str
    project: str  # 项目期


measurements = [
    Measurement(db='sany', rp='rp_infinite_1d', name='WindFarmData1d'),
    Measurement(db='sany', rp='rp_infinite', name='WindFarmData10m'),
    Measurement(db='sany', rp='rp_infinite', name='WindFarmStateData'),
    Measurement(db='sany', rp='rp_infinite', name='Xy'),
]

table_tag_keys_map = {
    'WindFarmData1d': ['turbine', 'type', 'circle', 'farm', 'project', 'day', 'month', 'year', 'week'],
    'WindFarmStateData': ['turbine', 'type', 'circle', 'farm', 'project', 'availabilitySta', 'availabilityStaDesc',
                          'day', 'month', 'year', 'week'],
    'Xy': ['turbine', 'type', 'circle', 'farm', 'project', 'availabilitySta', 'availabilityStaDesc',
           'day', 'month', 'year', 'week'],
}

ldir = os.path.join(os.curdir, 'excel')

assert os.path.exists(ldir), f'目录{ldir}不存在，请参照说明文档'

config_dir = os.path.join(ldir, 'config')
os.makedirs(config_dir, exist_ok=True)

client = InfluxDBClient(**options)

with open(os.path.join(config_dir, 'turbine.json'), encoding='utf8') as f:
    turbine_config = json.load(f)
    turbines = {turbine['turbine']: Turbine(turbine['turbine'],
                                            turbine['type'],
                                            turbine['circle'],
                                            turbine['farm'],
                                            turbine['project'])
                for turbine in turbine_config}


def write_log(msg):
    logging.info(msg)
    print(msg)


def query_influxdb(database, retention_policy, sql) -> List[ResultSet]:
    '''sql可以多条语句；如果多条语句，则每个sql对应结果以数组形式返回'''
    write_log(sql)
    r = client.query(sql, database=database, method='POST', params={
        'rp': retention_policy
    })
    # list(r) 返回非预期结果
    return r if isinstance(r, list) else [r]


def tags(m: Measurement):
    if m.name in table_tag_keys_map:
        return table_tag_keys_map[m.name]

    sql = f'show tag keys on "{m.db}" from "{m.name}" '
    r = query_influxdb(m.db, m.rp, sql)
    return [v for p in r[0].get_points() for k, v in p.items()]


def main(path):
    df = pd.read_excel(path, skiprows=0, header=1, parse_dates={'date': [1]})
    table_name = df.at[0, 'table_name']
    df.drop(columns=['table_name'], inplace=True)

    tables = [m for m in measurements if m.name == table_name]
    assert tables, 'excel文件内容不正确。请内容第一列和模板文件一致'

    m: Measurement = tables[0]
    if m.name == 'WindFarmData1d':
        m_10m = [x for x in measurements if x.name == 'WindFarmData10m'][0]
        if m_10m:
            tables.append(m_10m)

    for m in tables:
        t: AbstractTable = eval(m.name)(data=pd.DataFrame(df),
                                        config_dir=config_dir,
                                        db=m.db,
                                        retention_policy=m.rp,
                                        tags=tags(m))
        # t: AbstractTable = eval(influxdb_config.measurement)(influxdb_config.db, influxdb_config.rp)
        t.clean_data(**{
            'turbines': turbines
        })

        for sql in t.delete_data():
            query_influxdb(m.db, m.rp, sql)

        # continue

        for points in t.make_points():
            write_log(points)
            s = 0
            while True:
                e = s + 100
                e = len(points) if e >= len(points) else e

                r = client.write_points(points=points[s:e],
                                        database=m.db,
                                        time_precision='ms',
                                        retention_policy=m.rp,
                                        )

                if r:
                    write_log(f'total rows:{len(points)},{s / 100} paged write rows:{e - s} successed')
                else:
                    write_log(f'rows:{e - s},write failed')
                if e == len(points):
                    write_log(f'total rows:{len(points)} write completed。数据写入完成')
                    break
                s = e


def drop_backup_tables():
    db = 'sany',
    rp = 'rp_infinite_1d'
    r = query_influxdb(db, rp, 'show measurements;show databases')
    tables = [v for p in r[0].get_points()
              for k, v in p.items()
              for m in measurements
              if str(v).startswith(f'{m.name}_bk')]
    for t in tables:
        write_log(query_influxdb(db, rp, f'drop measurement {t}'))


def config_log():
    log_level = logging.INFO
    log_dir = os.path.join(os.curdir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'main.log')

    log_handler = ConcurrentTimedRotatingFileHandler(filename=log_path, when='H', interval=24)
    log_handler.setLevel(log_level)
    log_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)s:%(message)s'))
    logging.basicConfig(**{'handlers': [log_handler], 'level': log_level})


if __name__ == '__main__':
    config_log()
    write_log('-----------------------------------------start--------------------------------------')
    for root, dirs, files in os.walk(ldir):
        if os.path.split(root)[1] == 'templates':
            continue
        for f in files:
            if f.endswith('.xlsx'):
                path = os.path.join(root, f)
                main(path)

    # drop_backup_tables()

    write_log('数据写入完成，请检查数据')
