# cv_sampling dockerfile

FROM python:3.10

WORKDIR /app

# 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN ln -snf /usr/share/zoneinfo/Asia/Taipei /etc/localtime && echo "Asia/Taipei" > /etc/timezone


# 設定環境變數
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3001", "app:app"]
# docker run -d --name cv_sampling --restart always --net ai -v C:\Projects\cv_sampling\app:/app cv_sampling:v2.0.0