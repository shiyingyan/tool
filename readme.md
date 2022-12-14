## to install python on linux automation 安装python3的自动化脚本
```
sh install_python.sh
```

_使用 [conda](https://docs.conda.io/projects/conda/en/latest) 快速安装python环境。_


## R&W influxdb database
_项目参照make_data_tools_

- 安装依赖包 ```pip install influxdb```

- read data
```

client.query(sql, database=database, method='POST', params={
    'rp': retention_policy
})
```
- write data
```
# influxdb point对应关系数据库mysql的row
client.write_points(points=points[s:e],
                        database=m.db,
                        time_precision='ms',
                        retention_policy=m.rp,
                        )


```

- influxdb读写数据库的核心还是http，因此自己封装了一个简化版[客户端](make_data_tools/influxdb_client.py)，请参考。
（写入时，没有对数据类型的适配）


