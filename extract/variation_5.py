

## Built-ins
import re
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
    paginator = soup.find('nav', {'class':'elementor-pagination'})

    prev_el = paginator.find(attrs={'class':'page-numbers prev'})
    next_el = paginator.find(attrs={'class':'page-numbers next'})

    first_page_el = prev_el.find_next(attrs={'class':'page-numbers'})
    last_page_el = next_el.find_previous(attrs={'class':'page-numbers'})

    first_page = re.search(r'\d+', first_page_el.text).group()
    last_page = re.search(r'\d+', last_page_el.text).group()

    return [urlparse(urljoin(URL, f"page/{i}")) for i in range(int(first_page), int(last_page)+1)]

def get_article_urls(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    articles_container = soup.find_all('article', {'class': 'elementor-post'})
    return [urlparse(urljoin(URL, a.find('a')['href'])) for a in articles_container if a.find('a')]

@ArticleSoup.register('title')
def article_title(soup):
    title = soup.find('div', {'class':'elementor-page-title'})
    return title.get_text(strip=True, separator=' ') if title else None

@ArticleSoup.register('timestamp')
def publish_date(soup):
    date_1 = soup.find('meta', {'property':'article:published_time'})
    date_2 = soup.find('span', {'class': 'elementor-post-info__item--type-date'})
    
    date_1_text = date_1['content'] if date_1 else None
    date_2_text = date_2.get_text(strip=True, separator=' ') if date_2 else None

    return date_1_text or date_2_text

@ArticleSoup.register('text')
def article_text(soup):
    content = soup.find('div', {'data-widget_type':'theme-post-content.default'})
    return content.get_text(strip=True, separator='\n') if content else None

@ArticleSoup.register('url')
def article_url(soup):
    url = soup.find('meta', {'property':'og:url'})
    return url['content'] if url else None

def extract_articles(articles:list):
    return [article.extract() for article in tqdm(articles, desc='Extracting...')]

def extract_from_file(files:list):
    articles = []

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            article = ArticleSoup(f.read())
            articles.append(article)

    extracted = extract_articles(articles)
    save_extract({'records': extracted}, 'variation-5_extract')

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

            article_urls = get_article_urls(chrome_driver.page_source)
            articles_p_bar.total = int((articles_p_bar.n + len(article_urls))/listing_p_bar.n  * listing_p_bar.total)
            articles_p_bar.refresh()

            for a_link in article_urls:
                try:
                    if a_link:
                        chrome_driver.get(a_link.geturl())
                        article = ArticleSoup(chrome_driver.page_source)
                        partial_url = article.url.strip('/').rpartition('/')[-1] if article.url else "article_title"
                        articles.append(article)
                        article.save_source(partial_url, filepath=EXPORT_DIR)

                        articles_p_bar.update(1)

                except WebDriverException:
                    pages_with_errors[p_link.geturl()].append(a_link.geturl())
                    continue
                
            listing_p_bar.update(1)

        except WebDriverException:
            pages_with_errors[p_link.geturl()]
            continue

    extracted = extract_articles(articles)
    save_extract({'records': extracted}, 'variation-5_extract')


    ## ASYCHRONOUS PROCESS (will get IP banned quicker - use proxy or VPN)
    # page_urls = get_page_urls(get_page_source(URL))
    # extracted = []

    # with futures.ThreadPoolExecutor(max_workers=5) as e2:
    #     with futures.ThreadPoolExecutor(max_workers=5) as e1:
    #         page_futures = [e1.submit(lambda url: get_page_source(url.geturl()), url) for url in page_urls]
    #         articles_futures = []

    #         for pft in futures.as_completed(page_futures):
    #             article_urls = get_article_urls(pft.result())

    #             for url in article_urls:
    #                 articles_futures.append(e2.submit(lambda url: get_page_source(url.geturl()), url))

    #             gather_p_bar.update(1)

    #             extract_p_bar.total += len(article_urls)
    #             extract_p_bar.refresh()

    #             done, _ = futures.wait(articles_futures, return_when=futures.FIRST_COMPLETED)

    #             for aft in done:
    #                 articles_futures.pop(articles_futures.index(aft))
    #                 article = ArticleSoup(aft.result())
    #                 extracted.append(article.extract())

    #                 partial_url = article.url.strip('/').rpartition('/')[-1]
    #                 article.save_source(partial_url, filepath=EXPORT_DIR)
    #                 extract_p_bar.update(1)

    #         for aft in futures.as_completed(articles_futures):
    #             article = ArticleSoup(aft.result())
    #             extracted.append(article.extract())

    #             partial_url = article.url.strip('/').rpartition('/')[-1]
    #             article.save_source(partial_url, filepath=EXPORT_DIR)
    #             extract_p_bar.update(1)


if __name__ == '__main__':
    import sys

    _, EXPORT_DIR, URL, *FILES = sys.argv

    EXPORT_DIR = Path(EXPORT_DIR)

    if FILES:
        extract_from_file(FILES)
    else:
        main()