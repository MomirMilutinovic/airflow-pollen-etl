import argparse
import pyspark as spark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode
import api_scraper


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Downloads records from the pollens endpoint which are missing from the scraped dataset"
    )
    parser.add_argument(
        "pollens_path",
        help="Path to file/directory where the data from the /pollens endpoint is stored",
    )
    parser.add_argument(
        "concentrations_path",
        help="Path to file/directory where the data from the /concentrations endpoint is stored",
    )
    parser.add_argument("--download_concentrations", action="store_true")
    parser.add_argument("--download_pollens", action="store_true")
    return parser.parse_args()


def get_missing_pollen_ids(pollens_df, concentrations_df):
    return [
        row.pollen
        for row in concentrations_df.select("pollen")
        .subtract(pollens_df.select("id").alias("pollen"))
        .distinct()
        .collect()
    ]


def download_records(ids, record_type, destination_dir):
    for id in ids:
        api_scraper.main(
            [
                "--wrap_in_list",
                f"http://polen.sepa.gov.rs/api/opendata/{record_type}/{id}/",
                f"{destination_dir}/{id}.json",
            ]
        )

def download_concentrations(pollen_ids, destination_dir):
    url = f"http://polen.sepa.gov.rs/api/opendata/concentrations/?"
    batch_size = 40
    for i in range(0, len(pollen_ids), batch_size):
        last_id_in_batch = min(i+batch_size, len(pollen_ids))
        cur_url = url + "&".join([f"pollen_ids={id}" for id in pollen_ids[i:last_id_in_batch]])
        api_scraper.main(
            [
                "--paginated_api",
                cur_url,
                f"{destination_dir}/missing_concentrations_{i}.json",
            ]
        )



def get_missing_concentration_ids(pollens_df, concentrations_df):
    return [
        row.id
        for row in pollens_df.select(explode(col("concentrations")).alias("id"))
        .subtract(concentrations_df.select("id"))
        .distinct()
        .collect()
    ]


def get_pollen_ids_for_missing_concentration_ids(pollens_df, concentrations_df):
    exploded_pollen_df = pollens_df.withColumn(
        "concentration_id", explode("concentrations")
    ).withColumnRenamed("id", "pollen_id")
    return [
        row.pollen_id
        for row in exploded_pollen_df
        .join(concentrations_df, exploded_pollen_df.concentration_id == concentrations_df.id, "leftanti")
        .dropDuplicates(["pollen_id"]).select("pollen_id")
        .collect()
    ]


if __name__ == "__main__":
    args = parse_arguments()

    spark = SparkSession.builder.getOrCreate()
    pollens_df = spark.read.json(args.pollens_path)
    pollens_df = pollens_df.dropDuplicates()

    concentrations_df = spark.read.json(args.concentrations_path)

    if args.download_pollens:
        missing_ids = get_missing_pollen_ids(pollens_df, concentrations_df)
    elif args.download_concentrations:
        missing_ids = get_pollen_ids_for_missing_concentration_ids(pollens_df, concentrations_df)
    else:
        raise Exception("Must pass one of --download_polens --download_concentrations")

    print(list(sorted(missing_ids)))
    print(len(missing_ids))

    if args.download_pollens:
        download_records(missing_ids, "pollens", args.pollens_path)
    else:
        download_concentrations(missing_ids, args.concentrations_path)
