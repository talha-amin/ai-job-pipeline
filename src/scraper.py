"""
scraper.py - Fetches and extracts job description text from a URL or accepts raw text input.
"""

import requests
from bs4 import BeautifulSoup
import re
import sys


def scrape_job_posting(url: str) -> str:
    """Fetch a job posting URL and extract the main text content."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        print("Tip: Some sites block scraping. Try pasting the job description manually.")
        return ""

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = "\n".join(lines)

    # Trim to reasonable length (job descriptions rarely exceed 5000 chars)
    if len(cleaned) > 6000:
        cleaned = cleaned[:6000]

    return cleaned


def load_from_file(filepath: str) -> str:
    """Load a job description from a text file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <url_or_filepath>")
        sys.exit(1)

    source = sys.argv[1]

    if source.startswith("http"):
        text = scrape_job_posting(source)
    else:
        text = load_from_file(source)

    if text:
        print(f"Extracted {len(text)} characters")
        print("-" * 60)
        print(text[:1000])
    else:
        print("No text extracted.")
