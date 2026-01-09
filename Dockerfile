FROM python:3.11-slim-bookworm

WORKDIR /app

ENV JAVA_TOOL_OPTIONS="-Xint"

RUN apt-get update && apt-get install -y \
    git \
    curl \
    git \
    openjdk-17-jdk-headless \
    unzip \
    zip \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN curl -s https://get.nextflow.io | bash \
    && mv nextflow /usr/local/bin/nextflow \
    && chmod +x /usr/local/bin/nextflow

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
