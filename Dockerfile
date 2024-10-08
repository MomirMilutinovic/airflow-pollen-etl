# Use the official Airflow image as the base
FROM apache/airflow:2.10.2

USER root
RUN apt update && apt install -y procps && apt install -y default-jdk && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME='/usr/lib/jvm/java-17-openjdk-amd64'
USER airflow
# Install the Spark provider for Airflow
RUN pip install apache-airflow-providers-apache-spark