FROM tiangolo/uwsgi-nginx-flask:python3.12

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade -r /requirements.txt


COPY run.sh /run.sh
COPY frontend /frontend
COPY assets /assets
COPY teison.py /teison.py
RUN chmod +x /run.sh

EXPOSE 5000

CMD [ "/run.sh" ]


