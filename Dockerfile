From python:3.11-buster

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/
RUN chmod +x ./resources/log-deleter.sh

CMD ["python","manage.py", "runserver", "0.0.0.0:8000"]