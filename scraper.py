import requests
from bs4 import BeautifulSoup, Comment
from ddgs import DDGS
from googlesearch import search as google_search
from .utils import load_random_headers, clean_text
from time import sleep
import random

# Keywords to verify if a page is actually about coins
COIN_KEYWORDS = [
    'numismatic', 'coin', 'mint', 'obverse', 'reverse', 'dynasty',
    'ruler', 'bullion', 'drachm', 'tetradrachm', 'aureus', 'denarius',
    'ancient', 'currency', 'collection', 'emperor', 'king'
]


def fetch_full_text(url, delay=1):
    """
    Intelligently fetch and clean the main content from a URL.
    """
    headers = load_random_headers()
    try:
        # Use a session for better connection management
        with requests.Session() as s:
            resp = s.get(url, headers=headers, timeout=15)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove irrelevant parts of the page
        for element in soup(["script", "style", "header", "footer", "nav", "aside", "form", "button"]):
            element.decompose()
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Try to find the main content of the article
        main_content_selectors = ["article", "main", ".post-content", ".entry-content", "#content", "#main",
                                  ".td-post-content"]
        content_div = None
        for selector in main_content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                break

        if not content_div:
            content_div = soup.body  # Fallback to the whole body

        if content_div:
            full_text = " ".join(clean_text(text) for text in content_div.stripped_strings)
        else:
            full_text = ""

        sleep(delay)  # Be polite to servers
        return full_text

    except requests.RequestException as e:
        print(f"[Scraper] Network error fetching {url}: {e}")
        return f"[Error: Could not fetch content due to network issue.]"
    except Exception as e:
        print(f"[Scraper] Error processing {url}: {e}")
        return f"[Error: Could not process the page content.]"


def is_content_relevant(text, threshold=3):
    """
    Check if the text contains enough coin-related keywords to be considered relevant.
    """
    if not text:
        return False

    text_lower = text.lower()
    found_keywords = 0
    for keyword in COIN_KEYWORDS:
        if keyword in text_lower:
            found_keywords += 1

    return found_keywords >= threshold


def multi_search_snippets(query, max_results=3):
    """
    Search multiple engines, fetch full content, verify relevance, and return the best results.
    """
    all_results = []
    urls_seen = set()

    # --- Search Google ---
    print(f"[Scraper] Searching Google for: '{query}'")
    try:
        for url in google_search(query, num_results=max_results, sleep_interval=2):
            if url not in urls_seen:
                all_results.append({"link": url, "engine": "Google", "title": "", "snippet": ""})
                urls_seen.add(url)
    except Exception as e:
        print(f"[Scraper] Google search failed: {e}")

    # --- Search DuckDuckGo ---
    print(f"[Scraper] Searching DuckDuckGo for: '{query}'")
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                url = r.get("href")
                if url and url not in urls_seen:
                    all_results.append({
                        "link": url,
                        "engine": "DuckDuckGo",
                        "title": clean_text(r.get("title", "")),
                        "snippet": clean_text(r.get('body', ''))
                    })
                    urls_seen.add(url)
    except Exception as e:
        print(f"[Scraper] DuckDuckGo search failed: {e}")

    # --- Process and Verify Results ---
    final_results = []
    print(f"[Scraper] Found {len(all_results)} total initial results. Fetching and verifying content...")

    for result in all_results:
        link = result.get("link")
        if not link:
            continue

        print(f"  -> Fetching: {link}")
        full_text = fetch_full_text(link)

        if is_content_relevant(full_text):
            print("     -> Content is RELEVANT.")
            # If Google result, we need to get the title now
            if not result['title']:
                try:
                    soup = BeautifulSoup(requests.get(link, headers=load_random_headers()).text, 'html.parser')
                    result['title'] = clean_text(soup.title.string) if soup.title else "No Title Found"
                except:
                    result['title'] = "No Title Found"

            result['full_text'] = full_text
            final_results.append(result)
        else:
            print("     -> Content is NOT RELEVANT. Discarding.")

    # Randomly shuffle to mix results from different engines
    random.shuffle(final_results)
    return final_results[:max_results]  # Return the best N results

