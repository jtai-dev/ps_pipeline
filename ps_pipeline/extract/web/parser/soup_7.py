from urllib.parse import urlparse, urljoin

# External library packages and modules
from bs4 import BeautifulSoup

from extract.web.model import (
    ArticleSoup,
    remove_formatting,
)

URL_QUERY = "?page="


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, "html.parser")
    article_containers = soup.find_all("div", {"class": "media-body"})
    return [
        urlparse(urljoin(url, div.find("a")["href"]))
        for div in article_containers
        if div.find("a")
    ]


@ArticleSoup.register("title")
def article_title(soup):
    title = soup.find("h1", {"class": "display-4"})
    return title.get_text(strip=True, separator=" ") if title else None


@ArticleSoup.register("timestamp")
def publish_date(soup):

    date_1 = soup.find("meta", {"property": "article:published_time"})
    date_2_container = soup.find("div", {"class": "evo-create-type"})
    date_2 = (
        date_2_container.find("div", {"class": "col-auto"})
        if date_2_container
        else None
    )

    date_1_text = date_1["content"] if date_1 else None
    date_2_text = date_2.get_text(strip=True, separator=" ") if date_2 else None

    return date_1_text or date_2_text


@ArticleSoup.register("type")
def article_type(soup):
    type_container = soup.find("div", {"class": "evo-create-type"})
    a_type = type_container.find("a") if type_container else None
    return a_type.get_text(strip=True, separator=" ") if a_type else None


@ArticleSoup.register("text")
def article_text(soup):
    content = soup.find(
        "div",
        {
            "class": [
                "evo-article__body",
                "evo-press-release__body",
                "evo-in-the-news__body",
            ]
        },
    )
    if content:
        remove_formatting(content)
    return content.get_text(strip=True, separator="\n") if content else None


@ArticleSoup.register("url")
def article_url(soup):
    url = soup.find("meta", {"property": "og:url"})
    return url["content"] if url else None
