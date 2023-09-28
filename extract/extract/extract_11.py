
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


def get_article_urls(page_source, url):
    soup = BeautifulSoup(page_source, 'html.parser')
    article_titles = soup.find_all('h2', {'class': 'preview-title'})
    return [urlparse(urljoin(url, h2.parent['href'])) for h2 in article_titles if h2.parent]


@ArticleSoup.register('title')
def article_title(soup):
    title = soup.find('h1', {'class': 'post-title'})
    return title.get_text(strip=True, separator=' ') if title else None


@ArticleSoup.register('timestamp')
def publish_date(soup):
    date_1 = soup.find('meta', {'property': 'article:published_time'})
    date_2 = soup.find('time', {'class': 'date-block'})

    date_1_text = date_1['content'] if date_1 else None
    date_2_text = date_2.get_text(
        strip=True, separator=' ') if date_2 else None

    return date_1_text or date_2_text


@ArticleSoup.register('type')
def article_type(soup):
    category = soup.find('span', {'class': 'post-category'})
    return category.get_text(strip=True, separator=' ') if category else None


@ArticleSoup.register('text')
def article_text(soup):
    main_content = soup.find('main', {'class': 'main-content'})
    wrapper = main_content.find(
        'div', {'class': 'row'}) if main_content else None
    final_wrap = wrapper.find('div') if wrapper else None

    texts = []
    if final_wrap:
        remove_formatting(final_wrap)
        for el in final_wrap.contents:
            if (el.name and el.attrs not in ({'class': ['videoWrapper']},
                                             {'class': ['tag-container']},
                                             {'class': ['post-social']})):
                texts.append(el.get_text(strip=True))

    return '\n'.join(texts)


@ArticleSoup.register('tags')
def article_tags(soup):
    tag_container = soup.find('div', {'class': 'tag-container'})
    tags = tag_container.find_all('a')
    return [a.get_text(strip=True, separator=' ') for a in tags]


@ArticleSoup.register('url')
def article_url(soup):
    url = soup.find('meta', {'property': 'og:url'})
    return url['content'] if url else None
