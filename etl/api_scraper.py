import sys
import json
import requests
import argparse


def get_request(url):
    """
    Returns the JSON response from the api at url as a dict.
    """
    return requests.get(url).json()


def scrape_pages(url, content_key):
    """
    Scrapes the paginated api endpoint at url. Returns a list of dicts.
    The dicts are retrieved from the content_key key from each page.
    """
    result = []
    has_more_pages = url is not None
    while has_more_pages:
        current_page = get_request(url)
        result.extend(current_page[content_key])
        url = current_page.get("next")
        has_more_pages = url is not None

    return result


def export_to_json(data, location):
    json.dump(data, open(location, "w"))

def main(args):
    parser = argparse.ArgumentParser(description="SEPA pollen API scraper")
    parser.add_argument("url", type=str, help="URL of the API endpoint to scrape")
    parser.add_argument(
        "destination", type=str, help="The path to which to store the scraped data"
    )
    parser.add_argument(
        "--paginated_api", action="store_true", help="Is the API endpoint paginated"
    )
    parser.add_argument(
        "--wrap_in_list", action="store_true",
    )
    parser.add_argument(
        "--content_key",
        type=str,
        default="results",
        help="The key under which the content of a paginated api is stored",
    )

    args = parser.parse_args(args)
    url = args.url

    if args.paginated_api:
        data = scrape_pages(url, args.content_key)
    else:
        data = get_request(url)

    if args.wrap_in_list:
        data = [data]
    
    export_to_json(data, args.destination)

if __name__ == "__main__":
    main(sys.argv[1:])