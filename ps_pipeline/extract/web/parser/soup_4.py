from urllib.parse import urlparse, urljoin

# External library packages and modules
from bs4 import BeautifulSoup

from ps_pipeline.extract.web.soup_model import (
    ArticleSoup,
    remove_formatting,
)


def get_page_urls(page_source, url):
    soup = BeautifulSoup(page_source, "html.parser")
    jump_to_page = soup.find(string="Jump to page")

    paginator_1 = jump_to_page.parent if jump_to_page else None
    links_1 = paginator_1.find_next_siblings("a") if paginator_1 else []

    paginator_2 = soup.find("select", {"name": "page"})
    options_2 = paginator_2.find_all("option") if paginator_2 else []

    paginator_3 = paginator_1.parent if paginator_1 else None
    links_3 = paginator_3.find_all("a") if paginator_3 else []

    urls_1 = [urlparse(urljoin(url, a["href"])) for a in links_1 if a]
    urls_2 = [urlparse(urljoin(url, f"?page={o['value']}")) for o in options_2[1:] if o]
    urls_3 = [urlparse(urljoin(url, a["href"])) for a in links_3[1:] if a]

    return urls_1 or urls_2 or urls_3


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, "html.parser")
    article_titles = soup.find_all("td", {"class": "recordListTitle"})
    return [
        urlparse(urljoin(url, td.find("a")["href"]))
        for td in article_titles
        if td.find("a")
    ]


@ArticleSoup.register("title")
def article_title(soup):
    article_container = soup.find("article", {"class": "post"})
    title = (
        article_container.find(attrs={"class": "title"}) if article_container else None
    )
    return title.get_text(strip=True, separator=" ") if title else None


@ArticleSoup.register("timestamp")
def publish_date(soup):
    date_1 = soup.find("meta", {"name": "datewritten"})
    date_2 = soup.find("meta", {"property": "article:published_time"})
    date_3 = soup.find("span", {"class": "date"})

    date_1_text = date_1["content"] if date_1 else None
    date_2_text = date_2["content"] if date_2 else None
    date_3_text = date_3.get_text(strip=True, separator=" ") if date_3 else None

    return date_1_text or date_2_text or date_3_text


@ArticleSoup.register("text")
def article_text(soup):
    article_container = soup.find("article", {"class": "post"})
    content = (
        article_container.find("div", {"class": "content"})
        if article_container
        else None
    )
    cleaned = remove_formatting(content) if content is not None else content
    return cleaned.get_text(strip=True, separator="\n") if cleaned else ""


@ArticleSoup.register("url")
def article_url(soup):
    url_1 = soup.find("meta", {"property": "og:url"})
    url_2 = soup.find("link", {"rel": "canonical"})

    url_1_text = url_1["content"] if url_1 else None
    url_2_text = url_2["href"] if url_2 else None

    return url_1_text or url_2_text
