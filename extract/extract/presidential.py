
# Built-ins
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin

# External library packages and modules
from bs4 import BeautifulSoup

# Internal library packages and modules
if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

from extract.extract_model import (
    ArticleSoup,
    remove_formatting,
)


def get_page_urls(page_source, url):
    soup = BeautifulSoup(page_source, 'html.parser')
    paginator = soup.find('ul', {'class': 'page-numbers'})
    pages = paginator.find_all('li')

    first_page = "".join(re.findall(r'\d+', pages[0].text)) if pages else 1
    last_page = "".join(re.findall(r'\d+', pages[-1].text)) if pages else 1

    return [urlparse(urljoin(url, f"page/{i}")) for i in range(int(first_page), int(last_page)+1)]


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, 'html.parser')
    article_titles = soup.find_all('a', {'class': 'news-item__title'})
    return [urlparse(urljoin(url, a['href'])) for a in article_titles]


@ArticleSoup.register('title')
def article_title(soup):
    title = soup.find('h1', {'class': 'page-title'})
    return title.get_text(strip=True, separator=' ') if title else None


@ArticleSoup.register('timestamp')
def publish_date(soup):
    date = soup.find('time', {'class': 'posted-on'})
    return date['datetime'] if date else None


@ArticleSoup.register('type')
def article_type(soup):
    cat_tag = soup.find('a', {'rel': 'category tag'})
    return cat_tag.get_text(strip=True, separator=' ') if cat_tag else None


@ArticleSoup.register('text')
def article_text(soup):
    content = soup.find('section', {'class': 'body-content'})
    if content:
        remove_formatting(content)
    return content.get_text(strip=True, separator='\n') if content else None


@ArticleSoup.register('url')
def article_url(soup):
    url = soup.find('meta', {'property': 'og:url'})
    return url['content'] if url else None
