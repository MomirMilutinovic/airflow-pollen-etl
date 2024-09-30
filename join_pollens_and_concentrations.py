import argparse
import pyspark as spark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, to_date, max
import api_scraper

spark = SparkSession.builder.getOrCreate()


def load_and_join(pollens_path, concentrations_path):
    pollens_df = spark.read.json(args.pollens_path)
    pollens_df = pollens_df.dropDuplicates()
    pollens_df = pollens_df.withColumnRenamed("id", "pollen")

    concentrations_df = spark.read.json(args.concentrations_path).dropDuplicates()

    joined_df = concentrations_df.join(pollens_df, ["pollen"], "inner")

    assert joined_df.count() == concentrations_df.count()
    return joined_df


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Spark job for joining the data from the /pollens and /concentrations endpoints"
    )
    parser.add_argument(
        "pollens_path",
        help="Path to file/directory where the data from the /pollens endpoint is stored",
    )
    parser.add_argument(
        "concentrations_path",
        help="Path to file/directory where the data from the /concentrations endpoint is stored",
    )
    parser.add_argument("output_path", help="Path where to store the data")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    joined_df = load_and_join(args.pollens_path, args.concentrations_path)
    joined_df.drop("concentrations", "pollen")

    joined_df.write.parquet(args.output_path)
