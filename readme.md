## to install python on linux automation
```
sh install_python.sh
```

_使用 [conda](https://docs.conda.io/projects/conda/en/latest) 免安装python。_


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


