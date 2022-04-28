# 补录数据工具

## 使用方法1 ，python启动


1. 云之家网盘下载代码（云之家扫码登录），链接https://pan.yunzhijia.com/index#/collabfile/226578/459318521659195393
2. 找到下载的压缩文件，并解压。解压之后，打开make_data_sec代码目录
3. 安装python: 双击python安装包python-3.8.6-amd64（已安装跳过）
4. 修改配置文件config.py，修改influxdb连接信息options，influxdb数据表信息table_info，
5. 拷贝数据文件到excel目录，(**excel目录下,除了template目录和config目录，不要放其它任何无关文件**)
6. 拷贝配置：并把scada服务器上目录/home/scada/software/sync/config下的turbine.json、availabilitySta.json两个文件，下载到excel/config
7. docker click start.bat to start program
8. 等待程序运行结束，通过浏览器访问scada相应报表数据，确认数据是否修改正确


## 使用方法2，打包成windows应用

1. pip3 install pyinstaller
2. 切换到代码目录，并执行pyinstaller main.py
3. copy excel目录到dist/main目录下
4. 修改配置文件config.json到dist/main目录下，修改influxdb连接信息
5. 拷贝数据文件到excel目录，(**excel目录下,除了template目录和config目录，不要放其它任何无关文件**)
6. 拷贝配置：并把scada服务器上目录/home/scada/software/sync/config下的turbine.json、availabilitySta.json两个文件，下载到excel/config目录
7. 双击执行make.exe文件 启动程序
8. 程序正常运行结束后，窗口自动小时。 可以在logs/main.log查看日志
9. 通过浏览器访问scada相应报表数据，确认数据是否修改正确

## 使用方法3 -- docker方式启动

1. 下载并加载镜像

- 拉取镜像```docker pull harbor.sanywind.net/other/make_data_sec:1.0```
- 保存为压缩文件```docker save -o make_data_sec.tar```
- 上传到scada服务器
- 加载镜像```docker load < make_data_sec.tar```

2. 组件make_data_sec的配置，copy到/home/scada/docker-compose.yml。

         ```
         services:
           make_data_sec:
             container_name: make_data_sec
             networks:
               - scada
             dns_search: .
             image: harbor.sanywind.net/other/make_data_sec:1.0
             volumes:
               - /etc/localtime:/etc/localtime:ro
               - /root/excel:/opt/demo/excel
             environment:
               - INFLUXDB_HOST=influxdb
               - INFLUXDB_PORT=58086
               - INFLUXDB_USERNAME=root
               - INFLUXDB_PASSWORD=root
         ```

3. copy完成后，在docker-compose.yml文件中修改刚才copy的内容

    1) 修改对应的环境变量，influxdb数据表连接信息。 **程序启动前，一定要确认好**

    2) 路径挂载/root/excel:/opt/demo/excel

        - /root/excel为宿主机中，数据文件存在的目录。**目录下只能存放当前修改数据库的数据文件,.xlsx文件格式，不能存放其它文件**
        - /opt/demo/excel为容器中，数据文件存在目录。**不可修改**
        - /root/excel目录增加config目录，并copy服务器上目录/home/scada/software/sync/config下的turbine.json、availabilitySta.json两个文件，下载到这里

4. 启动组件

    - 请切换到目录，/home/scada

    - 启动方式1：第一次启动，或者重新修改docker-compose.yml后启动
      ```docker-compose up -d make_data_sec```

    - 启动方式2：重启
      ```docker-compose restart```

5. 查看日志

   ```
   docker logs -f --tail 200 make_data_sec
   ```

6. 后续处理。（重要）
    - 删除宿主机上挂载目录（本文档中指的是/root/excel）内所有文件

