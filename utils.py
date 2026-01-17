import json
import random
import os
import requests
from bs4 import BeautifulSoup

def load_random_headers():
    current_dir = os.path.dirname(__file__)
    headers_path = os.path.join(current_dir, "headers.json")
    with open(headers_path, "r") as f:
        headers_list = json.load(f)
    return random.choice(headers_list)

def fetch_url(url):
    headers = load_random_headers()
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def clean_text(text):
    return text.strip().replace("\n", " ").replace("  ", " ")

def get_soup(html):
    return BeautifulSoup(html, "html.parser")
