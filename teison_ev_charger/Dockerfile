FROM python:3.11-slim

RUN pip install --no-cache-dir --upgrade paho-mqtt requests pycryptodome flask

COPY run.sh /run.sh
COPY teison.py /teison.py
RUN chmod +x /run.sh

CMD [ "/run.sh" ]
