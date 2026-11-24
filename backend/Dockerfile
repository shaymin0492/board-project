# 11주차 강의자료의 Flask Dockerfile 구조를 그대로 따름
FROM python:3.11.2

WORKDIR /usr/src/app

COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY app.py .

EXPOSE 8001

# gunicorn 으로 8001번 포트에서 Flask 앱 실행
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8001", "--workers", "2"]
