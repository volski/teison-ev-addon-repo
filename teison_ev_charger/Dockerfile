ARG BUILD_FROM
FROM $BUILD_FROM

# Install dependencies
RUN apk add --no-cache \
    python3-dev \
    libffi-dev \
    openssl-dev \
    musl-dev \
    gcc \
    libgcc \
    make \
    g++ \
    linux-headers

COPY requirements.txt /requirements.txt

RUN python3 --version

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
