
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

    paginator = soup.find('select', {'title':'Select Page'})
    options = paginator.find_all('option') if paginator else []

    return [urlparse(urljoin(URL, f"?pagenum_rs={option['value']}")) for option in options]

def get_article_urls(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    article_titles = soup.find_all('h2', {'class': 'title'})
    return [urlparse(URL, h2.find('a')['href']) for h2 in article_titles if h2.find('a')]


@ArticleSoup.register('title')
def article_title(soup):
    title = soup.find(attrs={'class':'main_page_title'}) 
    return title.get_text(strip=True, separator=' ') if title else None

@ArticleSoup.register('timestamp')
def publish_date(soup):
    date = soup.find('span', {'class': 'date'})
    return date.get_text(strip=True, separator=' ') if date and date.text else None

@ArticleSoup.register('text')
def article_text(soup):
    press_content = soup.find('div', {'id':['press', 'pressrelease']})
    texts = []
    if press_content:
        for el in press_content.contents:
            if (el.name and el.attrs not in ({'class': ['date', 'black']},
                                             {'class': ['main_page_title']})):
                texts.append(el.get_text(strip=True, separator='\n'))

    # subtitle = '\n'.join([s.get_text(strip=True, separator='\n') for s in content.find_all(attrs={'class':'subtitle'})])
    # paragraphs = '\n'.join([p..get_text(strip=True, separator='\n') for p in content.find_all('p')])
    # ul = '\n'.join([u.text.strip() for u in content.find_all('ul') if u.text])

    return '\n'.join(texts)

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
    save_extract({'records': extracted}, 'variation-3_extract')

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
            listing_p_bar.update(1)

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
    save_extract({'records': extracted}, 'variation-3_extract')


    # with futures.ThreadPoolExecutor(max_workers=5) as e2:
    #     with futures.ThreadPoolExecutor(max_workers=5) as e1:
    #         page_futures = [e1.submit(get_page_source, url.geturl()) for url in page_urls]
    #         articles_futures = []

    #         for pft in futures.as_completed(page_futures):

    #             result_pft, url, success = pft.result()

    #             if success:
    #                 article_urls = get_article_urls(result_pft)

    #                 for url in article_urls:
    #                     articles_futures.append(e2.submit(get_page_source, url.geturl()))

    #                 gather_p_bar.update(1)

    #                 extract_p_bar.total += len(article_urls)
    #                 extract_p_bar.refresh()

    #                 done, _ = futures.wait(articles_futures, return_when=futures.FIRST_COMPLETED)

    #                 for aft in done:
    #                     articles_futures.pop(articles_futures.index(aft))
    #                     article = ArticleSoup(aft.result())
    #                     extracted.append(article.extract())

    #                     partial_url = article.url.strip('/').rpartition('/')[-1] if article.url else "article_title"
    #                     article.save_source(partial_url, filepath=EXPORT_DIR)
    #                     extract_p_bar.update(1)
    #             else:
    #                 page_futures.append(e1.submit(get_page_source, url))

    #         for aft in futures.as_completed(articles_futures):
    #             article = ArticleSoup(aft.result())
    #             extracted.append(article.extract())

    #             partial_url = article.url.strip('/').rpartition('/')[-1] if article.url else "article_title"
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