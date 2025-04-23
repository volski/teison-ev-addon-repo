FROM python:3.11-slim

RUN pip install --no-cache-dir --upgrade paho-mqtt requests pycryptodome flask flask-cors

COPY run.sh /run.sh
COPY frontend /frontend
COPY assets /assets
COPY teison.py /teison.py
RUN chmod +x /run.sh

EXPOSE 5000:5000

CMD [ "/run.sh" ]
