import argparse
from datetime import timedelta, date
import datetime
import api_scraper



def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Scrapes the pollens endpoint"
    )
    parser.add_argument(
        "pollens_url",
        help="URL to the /pollens endpoint of the pollen API",
    )
    parser.add_argument(
        "pollens_path",
        help="Path to the directory where the scraped data will be stored",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    iso_format = "%Y-%m-%d"
    start_date = date.fromisoformat("2016-01-01")
    current_date = date.today()
    batch_interval = timedelta(weeks=2)

    batch_start = start_date
    while batch_start < current_date:
        batch_end = batch_start + batch_interval - timedelta(days=1)
        batch_start_iso = batch_start.strftime(iso_format)
        batch_end_iso = batch_end.strftime(iso_format)
        api_scraper.main(
            [
                "--paginated_api",
                f"{args.pollens_url}?date_after={batch_start_iso}&date_before={batch_end_iso}",
                f"{args.pollens_path}/pollens_{batch_start_iso}-{batch_end_iso}.json",
            ]
        )
        batch_start += batch_interval
        
