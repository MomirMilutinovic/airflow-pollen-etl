# Pollen Data Scraping and Visualization System

## Overview

This repository contains a system that automates the process of scraping pollen data from the Serbian Environment Protection Agency's (SEPA) API, transforming and loading it into a PostgreSQL database using Apache Spark, and visualizing the data in Grafana. The entire workflow is orchestrated by Apache Airflow.

## System Components

The system consists of the following components:

- PostgreSQL: A relational database management system used to store the scraped pollen data
- Grafana: A visualization platform that provides a dashboard for visualizing the data.
- Airflow: A workflow management system that orchestrates the ETL (Extract, Transform, Load) pipeline
- Apache Spark Cluster: A distributed computing system that processes the data before loading it into the PostgreSQL database

## Requirements

- Docker and Docker Compose installed on the system
- Approximately 4GB of RAM available to run all the system components

## Setup

To set up the system, run the following command:

```
docker compose up
```

This will start all the necessary containers and services.

## Usage

1. *Run the Airflow DAG:*
    - Open a web browser and navigate to http://localhost:8081 to access the Airflow UI. Log in with the default credentials (username: airflow, password: password).
    - Trigger the DAG named `etl` in the Airflow UI to run the ETL pipeline.
    - Specify the time range for which to download the data. Note that the SEPA API provides data starting at 2016.
    - Wait for the DAG to complete. The DAG should finish in about 10 minutes.

2. *Visualize the Data in Grafana:*
    - Open a new web browser tab and navigate to http://localhost:3000 to access the Grafana dashboard.
    - Log in with the default credentials (username: admin, password: admin)
    - Open the "Pollen map" dashboard and set the desired date as the start date for the time range to view the data. The end date is ignored.
    - This will display a map showing the pollen load classes for each location.
    - To view the concentration of an individual kind of pollen, click the map marker at the desired location and expand the tab with the name of the allergen. This will display the concentration of the selected pollen type at the specified location.


# License

This project is licensed under the MIT License.

# Acknowledgments

This project uses data from the Serbian Environment Protection Agency's (SEPA) API.
