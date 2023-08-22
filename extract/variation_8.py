
## Built-ins
import json

from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin
from collections import defaultdict
from concurrent import futures

## External library packages and modules
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from tqdm import tqdm

## Internal library packages and modules
from scrapi import ArticleSoup


def get_page_source(url):

    chrome_service = Service('chromedriver')
    chrome_options = Options()
    chrome_options.add_argument('incognito')
    chrome_options.add_argument('headless')
    chrome_driver = webdriver.Chrome(service=chrome_service, options=chrome_options) 

    chrome_driver.get(url)
    page_source = chrome_driver.page_source

    chrome_driver.quit()
    
    return page_source

def get_page_urls(page_source):
    
    soup = BeautifulSoup(page_source, 'html.parser')

    jump_to_page = soup.find(string='Jump to page')
    paginator = jump_to_page.find_previous('ul') if jump_to_page else None
    options = paginator.find_all('a') if paginator else []

    return [urlparse(urljoin(URL, option['href'])) for option in options[1:] if option]

def get_articles(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    article_list = soup.find('div', {'class': 'recordList'})
    article_containers = article_list.find_all('article') if article_list else []

    return article_containers

@ArticleSoup.register('title')
def article_title(soup):
    title = soup.find('h1', {'class': 'title'})
    return title.get_text(strip=True, separator=' ') if title else None

@ArticleSoup.register('timestamp')
def publish_date(soup):
    date = soup.find('span', {'class': 'date'})
    return date.get_text(strip=True, separator=' ') if date else None

@ArticleSoup.register('tag')
def article_tag(soup):
    tag_container = soup.find('div', {'class': 'tag-list'})
    tags = tag_container.find_all(attrs={'class':'label'})
    return [tag.get_text(strip=True, separator=' ') for tag in tags]

@ArticleSoup.register('text')
def article_text(soup):
    content = soup.find('div', {'class':'content'})
    return content.get_text(strip=True, separator='\n') if content else None

@ArticleSoup.register('url')
def article_url(soup):
    header = soup.find(attrs={'class':'title'})
    url = header.find('a') if header else None
    return urljoin(URL, url['href']) if url else None

def extract_articles(articles:list):
    return [article.extract() for article in tqdm(articles, desc='Extracting...')]

def extract_from_file(files:list):
    articles = []

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            article = ArticleSoup(f.read())
            articles.append(article)

    extracted = extract_articles(articles)
    save_extract({'records': extracted}, 'variation-8_extract')
    
    return extracted

def save_extract(extracted, filename):

    EXTRACT_FILES = EXPORT_DIR / "EXTRACT_FILES"
    EXTRACT_FILES.mkdir(exist_ok=True)
    timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d-%H%M%S-%f')

    if len(filename) > 225:
        filename = filename[:225]

    with open (EXTRACT_FILES / f"{filename}_{timestamp}.json", 'w') as f:
        json.dump(extracted, f, indent=4)


def main():

    chrome_service = Service('chromedriver')
    chrome_options = Options()
    chrome_options.add_argument('incognito')
    chrome_options.add_argument('headless')

    chrome_driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    
    chrome_driver.get(URL)

    articles = []
    page_urls = get_page_urls(chrome_driver.page_source)
    pages_with_errors = defaultdict(list)

    listing_p_bar = tqdm(total=len(page_urls), desc='Article listing iterated...')
    articles_p_bar = tqdm(total=0, desc='Articles gathered...')

    for p_link in page_urls:

        try:
            chrome_driver.get(p_link.geturl())

            articles_html = get_articles(chrome_driver.page_source)
            articles_p_bar.total = int((articles_p_bar.n + len(articles_html))/listing_p_bar.n  * listing_p_bar.total)
            articles_p_bar.refresh()

            for a_html in articles_html:

                article = ArticleSoup(str(a_html))
                partial_url = article.url.strip('/').rpartition('/')[-1] if article.url else "article_title"
                articles.append(article)
                article.save_source(partial_url, filepath=EXPORT_DIR)

                articles_p_bar.update(1)

            listing_p_bar.update(1)

        except WebDriverException:
            pages_with_errors[p_link.geturl()]
            continue
    
    extracted = extract_articles(articles)
    save_extract({'records': extracted}, 'variation-8_extract')


    ## ASYCHRONOUS PROCESS (will get IP banned quicker - use proxy or VPN)
    # page_urls = get_page_urls(get_page_source(URL))
    # extracted = []

    # gather_p_bar = tqdm(total=len(page_urls), desc='Getting Article URLs...')
    # extract_p_bar = tqdm(total=0, desc='Extracting Articles...')

    # with futures.ThreadPoolExecutor(max_workers=5) as e:
    #     page_futures = [e.submit(lambda url: get_page_source(url.geturl()), url) for url in page_urls]

    #     for pft in futures.as_completed(page_futures):
    #         articles = get_articles(pft.result())
    #         gather_p_bar.update(1)

    #         extract_p_bar.total += len(articles)
    #         extract_p_bar.refresh()

    #         for article in articles:
    #             if article:
    #                 article_soup = ArticleSoup(str(article))
    #                 extracted.append(article_soup.extract())

    #                 partial_url = article_soup.url.strip('/').rpartition('/')[-1]
    #                 article_soup.save_source(f"{partial_url}", filepath=EXPORT_DIR)
    #                 extract_p_bar.update(1)


if __name__ == '__main__':
    import sys

    _, EXPORT_DIR, URL, *FILES = sys.argv

    EXPORT_DIR = Path(EXPORT_DIR)

    if FILES:
        extract_from_file(FILES)
    else:
        main()