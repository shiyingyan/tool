# -*- coding: utf-8 -*-
# Created By Shing At 2022/4/22
import dataclasses
import datetime
import inspect
import json
import os

import numpy
import pandas as pd


@dataclasses.dataclass
class Turbine:
    name: str  # 01#,02# etc
    type: str  # 风机类型
    circle: str  # 集电线
    farm: str
    project: str  # 项目期


class AbstractTable:
    def __init__(self, data: pd.DataFrame, config_dir, db, retention_policy, tags, **params):
        self.data = data
        self._config_dir = config_dir
        self.db = db
        self.retention_policy = retention_policy
        self.measurement = self.__class__.__name__
        self.tags = tags
        self.__dict__.update(**params)
        self.load_configs()

    def __str__(self):
        return self.__dict__.__str__()

    def load_configs(self):
        pass

    def clean_data(self, **kwargs) -> pd.DataFrame:
        '''清洗数据'''
        raise NotImplementedError

    def delete_data(self):
        raise NotImplementedError

    def make_points(self):
        yield self._make_points_core()

    def _make_points_core(self):
        points = []

        rows = self.data.to_dict('records')
        for row in rows:
            r = dict(row)
            point = {
                'measurement': self.measurement,
                'time': r['time'],
                'tags': {},
                'fields': {},
            }

            for tag in self.tags:
                if tag in r:
                    if r[tag]:
                        point['tags'][tag] = r[tag]
                    del r[tag]
            del r['time']
            for k in list(r.keys()):
                if r[k] == '' or r[k] == numpy.nan or str(r[k]).lower() == 'none':
                    del r[k]
            point['fields'].update(r)

            points.append(point)
        return points


class WindFarmData10m(AbstractTable):
    def clean_data(self, **kwargs) -> pd.DataFrame:
        turbines = kwargs['turbines']

        df = self.data
        df.dropna(axis=1, how='all', inplace=True)
        # df.fillna(method='ffill', inplace=True)
        df.fillna('', inplace=True)

        df['month'] = df['date'].apply(lambda x: x.strftime('%Y-%m'))
        df['year'] = df['date'].apply(lambda x: x.strftime('%Y'))
        df['week'] = df['date'].apply(
            lambda x: f"{x.strftime('%Y')}年{x.strftime('%m')}月第{(x.day + x.replace(day=1).weekday()) // 7 + 1}周")
        df['day'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))

        df['date'] = df.date.apply(lambda x: int(x.to_pydatetime().timestamp() * 1000))
        df['time'] = df.date
        df.drop(columns='date', inplace=True)

        for tag in self.tags:
            if tag not in df.columns:
                if tag in [f.name for f in dataclasses.fields(Turbine)]:
                    df[tag] = df['turbine'].apply(lambda x: getattr(turbines[x], tag))

        for c in df.columns:
            if c not in self.tags and c != 'time':
                df[c] = df[c].map(lambda x: float(x))

        return df

    def delete_data(self):
        measurement = self.measurement
        rp = self.retention_policy

        back_up_table = f'{measurement}_bk_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        sql = f'''delete from {back_up_table}'''
        yield sql

        df = self.data
        for _, row in df.iterrows():
            time = row['time']
            dt_time = today_0h(datetime.datetime.fromtimestamp(time / 1000))

            min_time = (dt_time + datetime.timedelta(hours=-8)).strftime('%Y-%m-%dT%H:%M:%SZ')
            max_time = (next_day_0h(dt_time) + + datetime.timedelta(hours=-8)).strftime('%Y-%m-%dT%H:%M:%SZ')

            d_table = f'{self.db}.{rp}.{back_up_table}'
            s_table = f'{self.db}.{rp}.{measurement}'
            sql = f'''select * into {d_table} from {s_table} where turbine = '{row["turbine"]}' and time >= '{min_time}' and time < '{max_time}' group by *;'''
            yield sql

            sql = f'''delete from {measurement} where turbine='{row["turbine"]}' and time>='{min_time}' and time<'{max_time}' '''
            yield sql


class WindFarmData1d(WindFarmData10m):
    pass


class WindFarmStateData(AbstractTable):
    def load_configs(self):
        for root, dirs, files in os.walk(self._config_dir):
            for f_name in files:
                if str(f_name).endswith('availabilitySta.json'):
                    with open(os.path.join(root, f_name), encoding='utf8') as f:
                        state_config = json.load(f)
                        self._state_map = {s['state']: s['desc'] for s in state_config}

    def _find_stat_code(self, code_desc):
        if not self._state_map:
            return -1
        x = [k for k, v in self._state_map.items() if v == code_desc]
        return x[0] if x else -1

    def clean_data(self, **kwargs) -> pd.DataFrame:
        turbines = kwargs['turbines']

        df = self.data
        df.dropna(axis=1, how='all', inplace=True)
        # df.fillna(method='ffill', inplace=True)
        df.fillna('', inplace=True)

        df['month'] = df['date'].apply(lambda x: x.strftime('%Y-%m'))
        df['year'] = df['date'].apply(lambda x: x.strftime('%Y'))
        df['week'] = df['date'].apply(
            lambda x: f"{x.strftime('%Y')}年{x.strftime('%m')}月第{(x.day + x.replace(day=1).weekday()) // 7 + 1}周")
        df['day'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))

        df['availabilitySta'] = df['availabilityStaDesc'].apply(lambda x: self._find_stat_code(x))
        tmp_df = df['availabilitySta'][~df['availabilitySta'].isin(self._state_map)]
        df.drop(index=list(tmp_df.index), inplace=True)

        df['finished'] = 1

        df['date'] = df.date.apply(lambda x: int(x.to_pydatetime().timestamp() * 1000))
        df['time'] = df.date
        df['endTime'] = df['endTime'].apply(
            lambda x: int(x.to_pydatetime().timestamp() * 1000))
        df['durationSec'] = (df['endTime'] - df['date']) / 1000

        # df['endTime'] = df['endTime'].apply(
        #     lambda x: int((x.to_pydatetime() + datetime.timedelta(hours=-8)).timestamp() * 1000))
        #
        # df['date_utc'] = df.date.apply(
        #     lambda x: int((x.to_pydatetime() + datetime.timedelta(hours=-8)).timestamp() * 1000))
        # df['durationSec'] = (df['endTime'] - df['date_utc']) / 1000
        # df.drop(columns='date_utc', inplace=True)

        df.drop(columns='date', inplace=True)

        for tag in self.tags:
            if tag not in df.columns:
                if tag in [f.name for f in dataclasses.fields(Turbine)]:
                    df[tag] = df['turbine'].apply(lambda x: getattr(turbines[x], tag))

        def format(x):
            try:
                return float(x)
            except:
                return str(x)

        for c in df.columns:
            if c not in self.tags and c != 'time':
                df[c] = df[c].map(format)

        return df

    def delete_data(self):
        backup_table = f'{self.__class__.__name__}_bk_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        sql = f'delete from {backup_table}'
        yield sql

        df = self.data
        for _, row in df.iterrows():
            time = row['time']
            dt_time = datetime.datetime.fromtimestamp(time / 1000) + datetime.timedelta(hours=-8)

            endTime = row['endTime']
            dt_endTime = datetime.datetime.fromtimestamp(endTime / 1000)
            from_time = dt_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            to_time = dt_endTime.strftime('%Y-%m-%dT%H:%M:%SZ')
            # sql = f'''delete from {self.__class__.__name__} where turbine='{row["turbine"]}' and time='{from_time}' and endTime='{to_time}' '''
            s_table = f'''{self.db}.{self.retention_policy}.{self.__class__.__name__}'''
            d_table = f'''{self.db}.{self.retention_policy}.{backup_table}'''
            sql = f'''select * into {d_table} from {s_table} where turbine='{row["turbine"]}' and time='{from_time}' group by * '''
            yield sql
            sql = f'''delete from {self.__class__.__name__} where turbine='{row["turbine"]}' and time='{from_time}' '''
            yield sql


class Xy(WindFarmStateData):
    pass


def today_0h(t: datetime.datetime):
    return t.replace(hour=0, minute=0, second=0, microsecond=0)


def next_day_0h(t: datetime.datetime):
    return today_0h(t) + datetime.timedelta(days=1)
