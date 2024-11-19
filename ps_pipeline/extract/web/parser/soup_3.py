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
    paginator = soup.find("select", {"title": "Select Page"})
    options = paginator.find_all("option") if paginator else []
    return [
        urlparse(urljoin(url, f"?pagenum_rs={option['value']}")) for option in options
    ]


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, "html.parser")
    article_titles = soup.find_all("h2", {"class": "title"})
    return [
        urlparse(urljoin(url, h2.find("a")["href"]))
        for h2 in article_titles
        if h2.find("a")
    ]


@ArticleSoup.register("title")
def article_title(soup):
    title = soup.find(attrs={"class": "main_page_title"})
    return title.get_text(strip=True, separator=" ") if title else None


@ArticleSoup.register("timestamp")
def publish_date(soup):
    date_1 = soup.find("meta", {"name": "date"})
    date_2 = soup.find("span", {"class": "date"})

    date_1_text = date_1["content"] if date_1 else None
    date_2_text = date_2.get_text(strip=True, separator=" ") if date_2 else None

    return date_1_text or date_2_text


@ArticleSoup.register("text")
def article_text(soup):
    press_content = soup.find("div", {"id": ["press", "pressrelease"]})
    texts = []
    if press_content:
        # remove_formatting(press_content)
        for el in press_content.contents:
            if el.name and el.attrs not in (
                {"class": ["date", "black"]},
                {"class": ["main_page_title"]},
            ):
                cleaned_el = remove_formatting(el)
                texts.append(
                    cleaned_el.get_text(strip=True, separator="\n")
                    if cleaned_el
                    else ""
                )

    # subtitle = '\n'.join([s.get_text(strip=True, separator='\n') for s in content.find_all(attrs={'class':'subtitle'})])
    # paragraphs = '\n'.join([p..get_text(strip=True, separator='\n') for p in content.find_all('p')])
    # ul = '\n'.join([u.text.strip() for u in content.find_all('ul') if u.text])

    return "\n".join(texts)


@ArticleSoup.register("url")
def article_url(soup):
    url = soup.find("meta", {"property": "og:url"})
    return url["content"] if url else None
