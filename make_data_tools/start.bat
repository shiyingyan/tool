@echo off

pip install -r requirements.txt -i https://pypi.doubanio.com/simple --trusted-host=pypi.doubanio.com

python main.py

cmd /k