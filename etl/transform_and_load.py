import json
import argparse
import pyspark as spark
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, initcap
from cyrtranslit import to_latin
from typing import Mapping


def rename_columns(df: spark.sql.DataFrame, rename_mapping: Mapping[str, str]):
    for old_name, new_name in rename_mapping.items():
        df = df.withColumnRenamed(old_name, new_name)
    return df


def cast_columns(df: spark.sql.DataFrame, type_mapping: Mapping[str, str]):
    for column, type in type_mapping.items():
        if column not in df.columns:
            raise Exception(
                f"Column {column} is present in type_mapping but not in the data"
            )
        df = df.withColumn(column, col(column).cast(type))
    return df


def transliterate_column(df: spark.sql.DataFrame, column: str):
    transliterate_udf = udf(lambda text: to_latin(text, "sr"))
    return df.withColumn(column, transliterate_udf(col(column)))


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Spark job for transforming and loading pollen data into a SQL database"
    )
    parser.add_argument(
        "input_path", help="Path to file/directory where the data is stored"
    )
    parser.add_argument(
        "jdbc_url", help="JDBC url of the database in which to write the data"
    )
    parser.add_argument(
        "table_name", help="The name of the table in which to write the data"
    )
    parser.add_argument("--user", help="JDBC username", required=True)
    parser.add_argument("--password", help="JDBC password", required=True)
    parser.add_argument("--driver", help="JDBC driver", required=True)
    parser.add_argument("--driver_jar", help="Path to JDBC driver JAR", required=True)

    parser.add_argument(
        "--rename_mapping",
        help="JSON object where the keys are the current names of columns that need to be renamed, and the values are the new names of these columns",
        default="{}",
    )
    parser.add_argument(
        "--type_mapping",
        help="JSON object where the keys are the names of columns that need to be casted, and the values are the types to which they should be casted",
        default="{}",
    )
    parser.add_argument(
        "--columns_to_transliterate",
        nargs="*",
        help="The names of the columns that should be transliterated from cyrilic to latin",
        default=[]
    )
    parser.add_argument(
        "--initcap_columns",
        nargs="*",
        help="The names of the columns that should be formatted using titlecase",
        default=[]
    )
    parser.add_argument(
        "--drop_columns",
        nargs="*",
        help="The names of the columns that should be dropped",
    )
    parser.add_argument(
        "--input_is_parquet",
        action="store_true",
    )
    parser.add_argument(
        "--only_insert_new",
        action="store_true",
        help="Insert only the new data, not the whole input directory. Use only for small tables."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite all the data in the database with new data."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    spark = SparkSession.builder.config("spark.jars", args.driver_jar).getOrCreate()

    url = args.jdbc_url
    result_table_name = args.table_name

    properties = {"user": args.user, "password": args.password, "driver": args.driver}

    df = spark.read.parquet(args.input_path) if args.input_is_parquet else spark.read.json(args.input_path)

    rename_mapping = json.loads(args.rename_mapping)
    df = rename_columns(df, rename_mapping)

    type_mapping = json.loads(args.type_mapping)
    df = cast_columns(df, type_mapping)

    for column in args.columns_to_transliterate:
        df = transliterate_column(df, column)

    for column in args.initcap_columns:
        df = df.withColumn(column, initcap(col(column)))

    columns_to_drop = args.drop_columns
    if columns_to_drop is not None:
        df = df.drop(*columns_to_drop)

    df.show()

    if args.only_insert_new:
        df_in_db = spark.read.jdbc(url, result_table_name, properties=properties)
        df = df.join(df_in_db, df.id == df_in_db.id, "leftanti")


    df.dropDuplicates().write.jdbc(url, result_table_name, mode="append" if not args.overwrite else "overwrite", properties=properties)
