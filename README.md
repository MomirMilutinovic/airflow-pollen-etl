# Pollen Data Scraping and Visualization System

## Overview

This repository contains a system that automates the process of scraping pollen data from the Scottish Environment Protection Agency's (SEPA) API, transforming and loading it into a SQLite database using Apache Spark, and visualizing the data in Grafana. The entire workflow is orchestrated by Apache Airflow.

## System Components

- Pollen Data Scraper: A Python script that scrapes pollen data from SEPA's API and stores it in a JSON file.
- Spark ETL Pipeline: A Spark job that reads the JSON file, transforms the data, and loads it into a SQLite database.
- Apache Airflow: A workflow management system that orchestrates the entire process, scheduling the scraper and ETL pipeline to run at regular intervals.
    Grafana Visualization: A dashboard that visualizes the pollen data stored in the SQLite database.

## Requirements

- Python 3.7+
- Apache Spark 3.1+
- Apache Airflow 2.0+
- SQLite 3.30+
- Grafana 7.0+

## Setup
TODO

## Usage
TODO

# License

This project is licensed under the MIT License.

# Acknowledgments

This project uses data from the Serbian Environment Protection Agency's (SEPA) API.
