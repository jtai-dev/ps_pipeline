"""
HTML Parser using BeautifulSoup and heavy utilization of soup_model.py
"""
__author__ = "Johanan Tai"

from urllib.parse import urlparse, urljoin

# External library packages and modules
from bs4 import BeautifulSoup

from ps_pipeline.extract.web.soup_model import (
    ArticleSoup,
    remove_formatting,
)


def get_page_urls(page_source, url):
    soup = BeautifulSoup(page_source, "html.parser")
    paginator = soup.find("select", {"id": "showing-page"})
    options = paginator.find_all("option") if paginator else []
    return [
        urlparse(urljoin(url, f"?pagenum_rs={option['value']}")) for option in options
    ]


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, "html.parser")
    article_titles = soup.find_all(
        attrs={"class": ["ArticleBlock__title", "ArticleBlock__titleContainer"]}
    )
    return [
        urlparse(urljoin(url, a.find("a")["href"]))
        for a in article_titles
        if a.find("a")
    ]


@ArticleSoup.register("title")
def article_title(soup):
    title = soup.find("span", {"class": "Heading__title"})
    return title.get_text(strip=True, separator=" ") if title else None


@ArticleSoup.register("timestamp")
def publish_date(soup):
    date = soup.find("time", {"class": ["Heading--time", "Heading--overline"]})
    return date["datetime"] if date else None


@ArticleSoup.register("text")
def article_text(soup):
    content = soup.find("div", {"class": "RawHTML"})
    cleaned = remove_formatting(content) if content is not None else content
    return cleaned.get_text(strip=True, separator="\n") if cleaned else ""


@ArticleSoup.register("tags")
def article_tags(soup):
    related_links = soup.find_all("li", {"class": "RelatedIssuesLink"})
    return [
        li.get_text(strip=True, separator=" ") if li.text else ""
        for li in related_links
    ]


@ArticleSoup.register("url")
def article_url(soup):
    url = soup.find("meta", {"property": "og:url"})
    return url["content"] if url else None
