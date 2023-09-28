
# Built-ins
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
    paginator = soup.find('select', {'id': 'showing-page'})
    options = paginator.find_all('option')
    return [urlparse(urljoin(url, f"?pagenum_rs={option['value']}")) for option in options]


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, 'html.parser')
    article_titles = soup.find_all(attrs={'class': 'ArticleBlock__title'})
    return [urlparse(urljoin(url, a.find('a')['href'])) for a in article_titles if a.find('a')]


@ArticleSoup.register('title')
def article_title(soup):
    title = soup.find('h1', {'class': 'ArticleTitle'})
    return title.get_text(strip=True, separator=' ') if title else None


@ArticleSoup.register('timestamp')
def publish_date(soup):
    date = soup.find('div', {'class': 'ArticleHeader__date'})
    return date.get_text(strip=True, separator=' ') if date else None


@ArticleSoup.register('text')
def article_text(soup):
    content = soup.find('div', {'class': 'RawHTML'})
    if content:
        remove_formatting(content)
    return content.get_text(strip=True, separator='\n') if content else None


@ArticleSoup.register('tags')
def article_tags(soup):
    tag_container = soup.find('div', {'class': 'related-issues'})
    return [a.get_text(strip=True) for a in tag_container.find_all('a')] if tag_container else []


@ArticleSoup.register('url')
def article_url(soup):
    url = soup.find('meta', {'property': 'og:url'})
    return url['content'] if url else None
