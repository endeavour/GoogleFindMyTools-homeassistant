# https://hub.docker.com/_/python
FROM docker.io/python:3.13.5-slim

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
USER nobody

CMD [ "python3", "./publish_mqtt.py"]
