
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

from extract.model import (
    ArticleSoup,
    remove_formatting,
)


def get_page_urls(page_source, url):

    soup = BeautifulSoup(page_source, 'html.parser')
    paginator = soup.find('nav', {'class': 'elementor-pagination'})

    prev_el = paginator.find(attrs={'class': 'page-numbers prev'})
    next_el = paginator.find(attrs={'class': 'page-numbers next'})

    first_page_el = prev_el.find_next(attrs={'class': 'page-numbers'})
    last_page_el = next_el.find_previous(attrs={'class': 'page-numbers'})

    first_page = "".join(re.findall(r'\d+', first_page_el.text)) or 1
    last_page = "".join(re.findall(r'\d+', last_page_el.text)) or 1

    return [urlparse(urljoin(url, f"page/{i}")) for i in range(int(first_page), int(last_page)+1)]


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, 'html.parser')
    articles_container = soup.find_all('article', {'class': 'elementor-post'})
    return [urlparse(urljoin(url, a.find('a')['href'])) for a in articles_container if a.find('a')]


@ArticleSoup.register('title')
def article_title(soup):
    title = soup.find('div', {'class': 'elementor-page-title'})
    return title.get_text(strip=True, separator=' ') if title else None


@ArticleSoup.register('timestamp')
def publish_date(soup):
    date_1 = soup.find('meta', {'property': 'article:published_time'})
    date_2 = soup.find(
        'span', {'class': 'elementor-post-info__item--type-date'})

    date_1_text = date_1['content'] if date_1 else None
    date_2_text = date_2.get_text(
        strip=True, separator=' ') if date_2 else None

    return date_1_text or date_2_text


@ArticleSoup.register('text')
def article_text(soup):
    content = soup.find(
        'div', {'data-widget_type': 'theme-post-content.default'})
    if content:
        remove_formatting(content)
    return content.get_text(strip=True, separator='\n') if content else None


@ArticleSoup.register('url')
def article_url(soup):
    url = soup.find('meta', {'property': 'og:url'})
    return url['content'] if url else None
