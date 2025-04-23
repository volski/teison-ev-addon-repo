ARG BUILD_FROM
FROM $BUILD_FROM



# Install requirements for add-on
RUN \
  apk add --no-cache \
    python3


# Set working directory
WORKDIR /data

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

COPY run.sh /run.sh
COPY frontend /frontend
COPY assets /assets
COPY teison.py /teison.py
RUN chmod +x /run.sh

EXPOSE 5000

CMD [ "/run.sh" ]

#Launch nginx with debug options.
# CMD [ "nginx","-g","daemon off;error_log /dev/stdout debug;" ]
