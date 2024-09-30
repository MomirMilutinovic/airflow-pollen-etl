import argparse
import pyspark as spark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode
import api_scraper


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Scrapes the concentrations endpoint based on the ids of previously scraped records from the /pollens endpoint"
    )
    parser.add_argument(
        "concentrations_url",
        help="URL to the /concentrations endpoint of the pollen API",
    )
    parser.add_argument(
        "pollens_path",
        help="Path to the directory where the data from the /pollens endpoint is stored",
    )
    parser.add_argument(
        "concentrations_path",
        help="Path to the directory where the data from the /concentrations endpoint will be stored",
    )
    return parser.parse_args()


def download_concentrations(url, pollen_ids, destination_dir):
    url = url + "?"
    batch_size = 30
    for i in range(0, len(pollen_ids), batch_size):
        last_id_in_batch = min(i + batch_size, len(pollen_ids))
        cur_url = url + "&".join(
            [f"pollen_ids={id}" for id in pollen_ids[i:last_id_in_batch]]
        )
        api_scraper.main(
            [
                "--paginated_api",
                cur_url,
                f"{destination_dir}/concentrations_{i}.json",
            ]
        )


if __name__ == "__main__":
    args = parse_arguments()

    spark = SparkSession.builder.getOrCreate()
    pollens_df = spark.read.json(args.pollens_path)
    pollens_df = pollens_df.dropDuplicates()

    pollen_ids = [row.id for row in pollens_df.select("id").collect()]
    download_concentrations(
        args.concentrations_url, pollen_ids, args.concentrations_path
    )
