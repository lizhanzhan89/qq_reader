
## 创建
```
docker run -d \
  --name qq_reader \
  -p 5001:5001 \
  -v $(pwd):/app \
  -w /app/qq_reader \
  python \
  /bin/bash -c "cd /app/qq_reader && pip install flask beautifulsoup4 requests APScheduler html5lib -i https://pypi.tuna.tsinghua.edu.cn/simple && python app.py"
```
## 停止
```
docker stop qq_reader
```
## 启动
```
docker start qq_reader
```