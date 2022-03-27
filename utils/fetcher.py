import requests
import json


def fetch_raw_data(url: str) -> dict:
    """Fetch the URL and transforms response JSON text into an object"""
    res = requests.get(url)
    raw_data = json.loads(res.text)
    return raw_data
