from datetime import datetime
from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.contrib.operators.spark_submit_operator import SparkSubmitOperator
import subprocess
import json

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
}

pollen_base_url = Variable.get("POLLEN_BASE_URL")
postgres_url = Variable.get("POSTGRES_URL")
postgres_user = Variable.get("POSTGRES_USER")
postgres_password = Variable.get("POSTGRES_PASSWORD")
postgres_driver = Variable.get("POSTGRES_DRIVER")


def run_python_script(script_path, args):
    result = subprocess.run(
        ["python", script_path] + args, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception(f"Script failed with error: {result.stderr}")
    else:
        print(result.stdout)


def run_scraper(path):
    run_python_script(
        "/opt/airflow/etl/api_scraper.py",
        [
            pollen_base_url + f"{path}/",
            f"/usr/local/spark/resources/data/{path}/{path}.json",
        ],
    )


def get_spark_job_arguments(input_dir, columns_to_transliterate=None, initcap_columns=None, drop_columns=None, type_mapping=None, rename_mapping=None, input_is_parquet=False):
    args = [
        f"/usr/local/spark/resources/data/{input_dir}",
        postgres_url,
        input_dir.replace("-", "_"), # - is a prohibited character in postgres table names
        "--user",
        postgres_user,
        "--password",
        postgres_password,
        "--driver",
        postgres_driver,
        "--driver_jar",
        "/usr/local/spark/app/postgresql-42.7.4.jar"
    ]

    if columns_to_transliterate is not None:
        args.append("--columns_to_transliterate")
        args.extend(columns_to_transliterate)
    if initcap_columns is not None:
        args.append("--initcap_columns")
        args.extend(initcap_columns)
    if drop_columns is not None:
        args.append("--drop_columns")
        args.extend(drop_columns)
    if rename_mapping is not None:
        args.append("--rename_mapping")
        args.append(json.dumps(rename_mapping))
    if type_mapping is not None:
        args.append("--type_mapping")
        args.append(json.dumps(type_mapping))
    if input_is_parquet:
        args.append("--input_is_parquet")

    return args

def get_transform_and_load_spark_submit_operator(name, args, dag):
    return SparkSubmitOperator(
        task_id=name,
        application="/usr/local/spark/app/transform_and_load.py",
        name=name.replace("_", "-"),
        conn_id="spark_default",
        verbose=True,
        conf={"spark.jars": "/usr/local/spark/app/postgresql-42.7.4.jar"},
        application_args=args,
        dag=dag,
    )

def scrape_allergen_types():
    run_scraper("allergen-types")


def scrape_allergens():
    run_scraper("allergens")


def scrape_locations():
    run_scraper("locations")


def scrape_pollens():
    run_python_script(
        "/opt/airflow/etl/download_pollens.py",
        [pollen_base_url + "pollens/", "/usr/local/spark/resources/data/pollens"],
    )


dag = DAG(
    "etl",
    default_args=default_args,
    start_date=datetime(2024, 10, 7),
    catchup=False,
)

make_directories_task = BashOperator(
    task_id="bash_task",
    bash_command="mkdir /usr/local/spark/resources/data/locations && mkdir /usr/local/spark/resources/data/concentrations && mkdir /usr/local/spark/resources/data/pollens && mkdir /usr/local/spark/resources/data/allergens && mkdir /usr/local/spark/resources/data/allergen-types",
)

scrape_allergen_types_task = PythonOperator(
    task_id="scrape_allergen_types",
    python_callable=scrape_allergen_types,
    dag=dag,
)
scrape_allergens_task = PythonOperator(
    task_id="scrape_allergens",
    python_callable=scrape_allergens,
    dag=dag,
)
scrape_locations_task = PythonOperator(
    task_id="scrape_locations",
    python_callable=scrape_locations,
    dag=dag,
)
scrape_pollens_task = PythonOperator(
    task_id="scrape_pollens",
    python_callable=scrape_pollens,
    dag=dag,
)
scrape_concentrations_task = SparkSubmitOperator(
    task_id="scrape_concentrations",
    application="/usr/local/spark/app/download_concentrations.py", 
    name="scrape-concentrations",
    conn_id="spark_default",
    verbose=True,
    application_args=[
        pollen_base_url + "concentrations/",
        "/usr/local/spark/resources/data/pollens",
        "/usr/local/spark/resources/data/concentrations",
    ],
    dag=dag,
)
join_pollens_and_concentrations_task = SparkSubmitOperator(
    task_id="join_pollens_and_concentrations",
    application="/usr/local/spark/app/join_pollens_and_concentrations.py",
    name="join-pollens-and-concentrations",
    conn_id="spark_default",
    conf={"spark.submit.user": "spark"},
    env_vars={"SPARK_USER": "spark"},
    verbose=True,
    application_args=[
        "/usr/local/spark/resources/data/pollens",
        "/usr/local/spark/resources/data/concentrations",
        "/usr/local/spark/resources/data/measurements",
    ],
    dag=dag,
)

load_allergen_types_args = get_spark_job_arguments(
    "allergen-types",
    rename_mapping={"name": "localized_name"},
    columns_to_transliterate=["localized_name"],
    initcap_columns=["localized_name"]
)
load_allergen_types_task = get_transform_and_load_spark_submit_operator("load_allergen_types", load_allergen_types_args, dag)

load_allergens_args = get_spark_job_arguments(
    "allergens",
    rename_mapping={"type": "type_id"},
    columns_to_transliterate=["localized_name"],
    initcap_columns=["name", "localized_name"],
    drop_columns=["margine_top", "margine_bottom", "allergenicity_display"]
)
load_allergens_task = get_transform_and_load_spark_submit_operator("load_allergens", load_allergens_args, dag) 

load_allergen_thresholds_args = get_spark_job_arguments("allergen-thresholds")
load_allergen_thresholds_task = get_transform_and_load_spark_submit_operator("load_allergen_thresholds", load_allergen_thresholds_args, dag)

load_locations_args = get_spark_job_arguments(
    "locations",
    columns_to_transliterate=["name"],
    initcap_columns=["name"],
    type_mapping={"longitude": "double", "latitude": "double"}
)
load_locations_task = get_transform_and_load_spark_submit_operator("load_locations", load_locations_args, dag)

load_measurements_args = get_spark_job_arguments(
    "measurements",
    rename_mapping={"value": "concentration", "allergen": "allergen_id", "location": "location_id"},
    type_mapping={"date": "date"},
    drop_columns=["pollen", "concentrations"],
    input_is_parquet=True
)
load_measurements_task = get_transform_and_load_spark_submit_operator("load_measurements", load_measurements_args, dag)

make_directories_task >> [
    scrape_allergen_types_task,
    scrape_allergens_task,
    scrape_locations_task,
    scrape_pollens_task,
    scrape_concentrations_task,
]
scrape_pollens_task >> scrape_concentrations_task >> join_pollens_and_concentrations_task >> load_measurements_task
scrape_allergen_types_task >> load_allergen_types_task
scrape_allergens_task >> load_allergen_types_task
scrape_locations_task >> load_locations_task

load_allergen_types_task >> load_allergens_task
load_allergens_task >> load_allergen_thresholds_task
load_measurements_task << [load_allergens_task, load_locations_task]

