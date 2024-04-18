import re
from urllib.parse import urlparse, urljoin

# External library packages and modules
from bs4 import BeautifulSoup

from extract.web.model import (
    ArticleSoup,
    remove_formatting,
)


def get_page_urls(page_source, url):

    soup = BeautifulSoup(page_source, "html.parser")

    last = soup.find(string="Last")
    last_page_link = urlparse(last.parent["href"]) if last else None
    last_page = "".join(re.findall(r"\d+", last_page_link.query))

    return [urlparse(urljoin(url, f"?page={i}")) for i in range(1, int(last_page) + 1)]


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, "html.parser")
    article_titles = soup.find_all("h1", {"class": "title"})
    return [
        urlparse(urljoin(url, a.find("a")["href"]))
        for a in article_titles
        if a.find("a")
    ]


@ArticleSoup.register("title")
def article_title(soup):
    title = soup.find("h1", {"class": "title"})
    return title.get_text(strip=True, separator=" ") if title else None


@ArticleSoup.register("timestamp")
def publish_date(soup):
    date = soup.find("span", {"class": "date"})
    return date.get_text(strip=True, separator=" ") if date else None


@ArticleSoup.register("tag")
def article_tag(soup):
    tag_container = soup.find("div", {"class": "tag-list"})
    tags = tag_container.find_all(attrs={"class": "label"})
    return [tag.get_text(strip=True, separator=" ") for tag in tags]


@ArticleSoup.register("text")
def article_text(soup):
    content = soup.find("div", {"class": "post-content"})
    if content:
        remove_formatting(content)
    return content.get_text(strip=True, separator="\n") if content else None


@ArticleSoup.register("url")
def article_url(soup):
    url = soup.find("meta", {"property": "og:url"})
    return url["content"] if url else None
