FROM python:3.10

RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    iproute2 \
    tcpdump \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY main.py .

CMD ["python3", "main.py"]
