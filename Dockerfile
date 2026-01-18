FROM --platform=linux/amd64 continuumio/miniconda3:25.3.1-1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
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

RUN nextflow pull nf-core/sarek

COPY . .
