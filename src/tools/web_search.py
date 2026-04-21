"""
Tool: search_web + scrape_url
Searches for financial news and scrapes article content.
"""

import requests
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def search_web(query: str, num_results: int = 5) -> dict:
    """
    Search for financial news using DuckDuckGo instant answer API.

    Args:
        query: Search query string
        num_results: Max number of results to return

    Returns:
        Dict with search results list
    """
    try:
        url    = "https://api.duckduckgo.com/"
        params = {
            "q":      query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = resp.json()

        results = []

        # Abstract (top answer)
        if data.get("AbstractText"):
            results.append({
                "title":   data.get("Heading", ""),
                "snippet": data["AbstractText"][:500],
                "url":     data.get("AbstractURL", ""),
                "source":  data.get("AbstractSource", ""),
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title":   topic.get("Text", "")[:100],
                    "snippet": topic.get("Text", "")[:400],
                    "url":     topic.get("FirstURL", ""),
                    "source":  "DuckDuckGo",
                })

        # Fallback: use news search via RSS
        if not results:
            results = _search_rss(query, num_results)

        logger.info(f"Web search: '{query}' → {len(results)} results")
        return {
            "query":   query,
            "results": results[:num_results],
            "count":   len(results[:num_results]),
        }

    except Exception as e:
        logger.error(f"search_web failed: {e}")
        # Try RSS fallback
        try:
            results = _search_rss(query, num_results)
            return {"query": query, "results": results, "count": len(results)}
        except:
            return {"error": str(e), "query": query, "results": []}


def _search_rss(query: str, num_results: int = 5) -> list:
    """Fallback: Google News RSS search."""
    try:
        encoded = requests.utils.quote(query)
        url     = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
        resp    = requests.get(url, headers=HEADERS, timeout=10)
        soup    = BeautifulSoup(resp.content, "xml")
        items   = soup.find_all("item")[:num_results]

        results = []
        for item in items:
            results.append({
                "title":   item.find("title").text if item.find("title") else "",
                "snippet": item.find("description").text[:300] if item.find("description") else "",
                "url":     item.find("link").text if item.find("link") else "",
                "source":  "Google News",
                "date":    item.find("pubDate").text if item.find("pubDate") else "",
            })
        return results
    except Exception as e:
        logger.error(f"RSS search failed: {e}")
        return []


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
def scrape_url(url: str, max_chars: int = 3000) -> dict:
    """
    Scrape and extract clean text from a financial article URL.

    Args:
        url: URL to scrape
        max_chars: Maximum characters to return

    Returns:
        Dict with title, text content, and url
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        soup  = BeautifulSoup(resp.content, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "advertisement", "iframe"]):
            tag.decompose()

        # Try article tag first, then fall back to body
        article = soup.find("article") or soup.find("main") or soup.find("body")
        if not article:
            article = soup

        # Extract paragraphs
        paragraphs = article.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)

        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else url

        result = {
            "url":     url,
            "title":   title_text[:200],
            "content": text[:max_chars],
            "chars":   len(text),
        }

        logger.info(f"Scraped {url} → {len(text)} chars")
        return result

    except Exception as e:
        logger.error(f"scrape_url failed for {url}: {e}")
        return {"error": str(e), "url": url, "content": ""}
