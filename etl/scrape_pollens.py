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
        "end_date": date.fromisoformat(args.end_date)
    }


if __name__ == "__main__":
    args = parse_arguments()

    start_date = args["start_date"]
    end_date = args["end_date"]
    batch_interval = timedelta(weeks=2)

    batch_start = start_date
    iso_format = "%Y-%m-%d"
    while batch_start < end_date:
        batch_end = batch_start + batch_interval - timedelta(days=1)
        batch_start_iso = batch_start.strftime(iso_format)
        batch_end_iso = batch_end.strftime(iso_format)
        api_scraper.main(
            [
                "--paginated_api",
                f"{args['pollens_url']}?date_after={batch_start_iso}&date_before={batch_end_iso}",
                f"{args['pollens_path']}/pollens_{batch_start_iso}-{batch_end_iso}.json",
            ]
        )
        batch_start += batch_interval
        
