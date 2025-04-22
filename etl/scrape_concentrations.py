import argparse
from api_scraper import scrape_pages, export_to_json
import pyspark as spark
from pyspark.sql import SparkSession
import asyncio
import aiohttp


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


async def _scrape_concentrations(batch_urls):
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=10)
    ) as session:
        concentrations_batches = await asyncio.gather(
            *(scrape_pages(batch_url, "results", session) for batch_url in batch_urls)
        )
        concentrations = [
            concentration
            for concentrations_batch in concentrations_batches
            for concentration in concentrations_batch
        ]
        return concentrations


def generate_batch_urls(url, pollen_ids, batch_size: int = 20):
    batch_urls = []
    url = url + "?"
    for i in range(0, len(pollen_ids), batch_size):
        last_id_in_batch = min(i + batch_size, len(pollen_ids))
        cur_url = url + "&".join(
            [f"pollen_ids={id}" for id in pollen_ids[i:last_id_in_batch]]
        )
        batch_urls.append(cur_url)
    return batch_urls


def download_concentrations(url, pollen_ids, destination_dir):
    batch_urls = generate_batch_urls(url, pollen_ids)
    concentrations = asyncio.run(_scrape_concentrations(batch_urls))
    export_to_json(concentrations, f"{destination_dir}/concentrations.json")


if __name__ == "__main__":
    args = parse_arguments()

    spark = SparkSession.builder.getOrCreate()
    pollens_df = spark.read.json(args.pollens_path)
    pollens_df = pollens_df.dropDuplicates()

    pollen_ids = [row.id for row in pollens_df.select("id").collect()]
    download_concentrations(
        args.concentrations_url, pollen_ids, args.concentrations_path
    )
