FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir --upgrade paho-mqtt requests pycryptodome flask

COPY run.sh /run.sh
COPY teison.py /teison.py
RUN chmod +x /run.sh

CMD [ "/run.sh" ]
