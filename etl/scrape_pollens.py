import argparse
from typing import List
from datetime import timedelta, date
import datetime
from api_scraper import scrape_pages, export_to_json
import asyncio
import aiohttp


def parse_arguments():
    parser = argparse.ArgumentParser(description="Scrapes the pollens endpoint")
    parser.add_argument(
        "pollens_url",
        help="URL to the /pollens endpoint of the pollen API",
    )
    parser.add_argument(
        "pollens_path",
        help="Path to the directory where the scraped data will be stored",
    )
    parser.add_argument(
        "start_date",
        help="Start of the date interval for which to download the data in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "end_date",
        help="End of the date interval for which to download the data in YYYY-MM-DD format.",
    )

    args = parser.parse_args()
    return {
        "pollens_url": args.pollens_url,
        "pollens_path": args.pollens_path,
        "start_date": date.fromisoformat(args.start_date),
        "end_date": date.fromisoformat(args.end_date),
    }


def generate_batch_urls(
    start_date: date, end_date: date, batch_interval: timedelta, pollens_url: str
):
    iso_format = "%Y-%m-%d"
    batch_urls = []

    batch_start = start_date
    while batch_start < end_date:
        batch_end = batch_start + batch_interval - timedelta(days=1)
        batch_start_iso = batch_start.strftime(iso_format)
        batch_end_iso = batch_end.strftime(iso_format)
        batch_urls.append(
            f"{pollens_url}?date_after={batch_start_iso}&date_before={batch_end_iso}",
        )
        batch_start += batch_interval

    return batch_urls


async def scrape_pollens(batch_urls: List[str]):
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=10)
    ) as session:
        pollen_record_batches = await asyncio.gather(
            *(scrape_pages(batch_url, "results", session) for batch_url in batch_urls)
        )
        pollen_records = [
            record
            for pollen_record_batch in pollen_record_batches
            for record in pollen_record_batch
        ]
        return pollen_records


if __name__ == "__main__":
    args = parse_arguments()

    start_date = args["start_date"]
    end_date = args["end_date"]
    batch_interval = timedelta(weeks=2)
    batch_urls = generate_batch_urls(
        start_date, end_date, batch_interval, args["pollens_url"]
    )
    pollen_records = asyncio.run(scrape_pollens(batch_urls))
    export_to_json(pollen_records, f"{args['pollens_path']}/pollens.json")
