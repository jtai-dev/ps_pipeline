from urllib.parse import urlparse, urljoin

# External library packages and modules
from bs4 import BeautifulSoup

from extract.web.model import (
    ArticleSoup,
    remove_formatting,
)


def get_page_urls(page_source, url):

    soup = BeautifulSoup(page_source, "html.parser")
    paginator = soup.find("div", {"class": "wp-pagenavi"})

    last_page_el = paginator.find("a", {"class": "last"})
    last_page_link = urlparse(last_page_el["href"]) if last_page_el else None

    first_page = paginator.find("span", {"class": "current"}).text
    last_page = last_page_link.path.strip("/").rpartition("/")[-1]

    return [
        urlparse(urljoin(url, f"page/{i}"))
        for i in range(int(first_page), int(last_page) + 1)
    ]


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, "html.parser")
    main_section = soup.find("section", {"class": "page-heading"})
    articles_container = main_section.find_next_sibling("div")

    articles = articles_container.find_all("div", {"class": "item"})
    return [
        urlparse(urljoin(url, art.find("a")["href"]))
        for art in articles
        if art.find("a")
    ]


@ArticleSoup.register("title")
def article_title(soup):
    header = soup.find("div", {"class": "post-header"})
    title_container = header.find_next_sibling("div") if header else None
    return (
        title_container.get_text(strip=True, separator=" ") if title_container else None
    )


@ArticleSoup.register("timestamp")
def publish_date(soup):
    date = soup.find("span", {"class": "date"})
    return date.get_text(strip=True, separator=" ") if date else None


@ArticleSoup.register("type")
def article_type(soup):
    category = soup.find("span", {"class": "post-category"})
    return category.get_text(strip=True, separator=" ") if category else None


@ArticleSoup.register("text")
def article_text(soup):
    header = soup.find("div", {"class": "post-header"})
    texts = []
    for p in header.find_next_siblings("p"):
        remove_formatting(p)
        texts.append(p.get_text(strip=True, separator="\n"))

    return "\n".join(texts)


@ArticleSoup.register("url")
def article_url(soup):
    url = soup.find("link", {"rel": "canonical"})
    return url["href"] if url else None
