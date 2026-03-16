import httpx
from bs4 import BeautifulSoup


async def fetch_webpage_content(url: str) -> dict:
    """Fetch and extract the main text content from a webpage.

    Args:
        url: The URL of the webpage to fetch content from.

    Returns:
        A dict with 'url', 'title', and 'content' keys.
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "LearningPlatformBot/1.0"},
            )
            response.raise_for_status()
    except httpx.HTTPError as e:
        return {"url": url, "title": "", "content": f"Error fetching URL: {e}"}

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script/style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    text = soup.get_text(separator="\n", strip=True)

    # Truncate to avoid oversized context
    max_chars = 5000
    if len(text) > max_chars:
        text = text[:max_chars] + "... [truncated]"

    return {"url": url, "title": title, "content": text}
