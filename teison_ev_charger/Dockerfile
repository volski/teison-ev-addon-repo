FROM python:3.11-slim

RUN pip install flask requests paho-mqtt

COPY run.sh /run.sh
COPY teison.py /teison.py
RUN chmod +x /run.sh

CMD [ "/run.sh" ]
