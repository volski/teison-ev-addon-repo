ARG BUILD_FROM
FROM $BUILD_FROM

RUN pip install --no-cache-dir --upgrade paho-mqtt requests pycryptodome flask flask-cors
#Add nginx and create the run folder for nginx.
# RUN \
#   apk --no-cache add \
#     nginx \
#   \
#   && mkdir -p /run/nginx

COPY run.sh /run.sh
COPY frontend /frontend
COPY assets /assets
COPY teison.py /teison.py
RUN chmod +x /run.sh

# COPY ingress.conf /etc/nginx/http.d/
EXPOSE 5000

CMD [ "/run.sh" ]

#Launch nginx with debug options.
# CMD [ "nginx","-g","daemon off;error_log /dev/stdout debug;" ]
