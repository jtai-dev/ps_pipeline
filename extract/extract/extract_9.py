
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
    paginator = soup.find('div', {'class': 'item-list'})

    next_page = paginator.find(attrs={'class': 'pager-next'})
    last_page = paginator.find(attrs={'class': 'pager-last'})

    next_page_link = urlparse(next_page.find(
        'a')['href']) if next_page and next_page.find('a') else None
    last_page_link = urlparse(last_page.find(
        'a')['href']) if last_page and last_page.find('a') else None

    first_page_num = int(next_page_link.query.split('=')
                         [-1]) - 1 if next_page_link else 1
    last_page_num = int(last_page_link.query.split('=')
                        [-1]) if last_page_link else 0

    return [urlparse(urljoin(url, f'?page={i}')) for i in range(int(first_page_num), int(last_page_num) + 1)]


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, 'html.parser')
    articles_container = soup.find('div', {'class': 'view-content'})
    articles = articles_container.find_all('div', {'class': 'views-row'})
    return [urlparse(urljoin(url, art.find('a')['href'])) for art in articles if art.find('a')]


@ArticleSoup.register('title')
def article_title(soup):
    title = soup.find(attrs={'id': 'page-title'})
    return title.get_text(strip=True, separator=' ') if title else None


@ArticleSoup.register('timestamp')
def publish_date(soup):
    date_1 = soup.find('meta', {'property': 'article:published_time'})
    date_2 = soup.find('div', {'class': 'pr_date'})

    date_1_text = date_1['content'] if date_1 else None
    date_2_text = date_2.get_text(
        strip=True, separator=' ') if date_2 else None

    return date_1_text or date_2_text


@ArticleSoup.register('text')
def article_text(soup):
    article_container = soup.find('article', {'class': 'node-press-release'})
    content = article_container.find(
        'div', {'class': 'field-items'}) if article_container else None
    if content:
        remove_formatting(content)
    return content.get_text(strip=True, separator='\n') if content else None


@ArticleSoup.register('url')
def article_url(soup):
    url = soup.find('meta', {'property': 'og:url'})
    return url['content'] if url else None
