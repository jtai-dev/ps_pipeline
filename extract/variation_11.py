
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
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup
from tqdm import tqdm

## Internal library packages and modules
from scrapi import ArticleSoup


def get_page_source(url):

    chrome_service = Service('chromedriver')
    chrome_options = Options()
    chrome_options.add_argument('incognito')
    chrome_options.add_argument('headless')
    chrome_options.add_argument('disable-gpu')
    chrome_driver = webdriver.Chrome(service=chrome_service, options=chrome_options) 

    chrome_driver.get(url)
    page_source = chrome_driver.page_source

    chrome_driver.quit()
    
    return page_source

def get_article_urls(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    article_titles = soup.find_all('h2', {'class': 'preview-title'})
    return [urlparse(urljoin(URL, h2.parent['href'])) for h2 in article_titles if h2.parent]

@ArticleSoup.register('title')
def article_title(soup):
    title = soup.find('h1', {'class': 'post-title'})
    return title.get_text(strip=True, separator=' ') if title else None

@ArticleSoup.register('timestamp')
def publish_date(soup):
    publish_time = soup.find('meta', {'property': 'article:published_time'})
    return publish_time['content'] if publish_time else None

@ArticleSoup.register('type')
def article_type(soup):
    category = soup.find('span', {'class':'post-category'})
    return category.get_text(strip=True, separator=' ') if category else None

@ArticleSoup.register('text')
def article_text(soup):
    main_content = soup.find('main', {'class':'main-content'})
    wrapper = main_content.find('div', {'class':'row'}) if main_content else None
    final_wrap = wrapper.find('div') if wrapper else None

    texts = []
    if final_wrap:
        for el in final_wrap.contents:
            if (el.name and el.attrs not in({'class':['videoWrapper']},
                                            {'class':['tag-container']},
                                            {'class':['post-social']})):
                texts.append(el.get_text(strip=True))
        
    return '\n'.join(texts)

@ArticleSoup.register('tags')
def article_tags(soup):
    tag_container = soup.find('div', {'class': 'tag-container'})
    tags = tag_container.find_all('a')
    return [a.get_text(strip=True, separator=' ') for a in tags]

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
    save_extract({'records': extracted}, 'variation-11_extract')

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
    chrome_driver_2 = webdriver.Chrome(service=chrome_service, options=chrome_options)

    chrome_driver.get(URL)

    articles = []
    pages_with_errors = defaultdict(list)

    listing_p_bar = tqdm(total=1, desc='Article listing iterated...')
    articles_p_bar = tqdm(total=0, desc='Articles gathered...')

    while True:

        next_button, button_inactive = chrome_driver.execute_script(
        """
            buttons = document.getElementsByClassName('pagination-link');
            nextButton = buttons[buttons.length-1];
            return [nextButton, nextButton.disabled];
        """)

        try:
            WebDriverWait(chrome_driver, 10).until(
                EC.visibility_of_all_elements_located((By.XPATH,
                    "//div[@class='posts']//div[@class='post-preview']"))
            )
        except TimeoutException:
            print('Timeout...')

        article_urls = get_article_urls(chrome_driver.page_source)
        articles_p_bar.total = int((articles_p_bar.n + len(article_urls))/listing_p_bar.n  * listing_p_bar.total)
        articles_p_bar.refresh()

        for a_link in article_urls:
            try:
                chrome_driver_2.get(a_link.geturl())
                article = ArticleSoup(chrome_driver_2.page_source)
                partial_url = article.url.strip('/').rpartition('/')[-1] if article.url else "article_title"
                articles.append(article)
                article.save_source(partial_url, filepath=EXPORT_DIR)

                articles_p_bar.update(1)

            except WebDriverException:
                pages_with_errors[chrome_driver.current_url].append(a_link.geturl())
                continue

        listing_p_bar.update(1)

        if button_inactive:
            break
        else:
            listing_p_bar.total += 1
            listing_p_bar.refresh()
            next_button.click()

    extracted = extract_articles(articles)
    save_extract({'records': extracted}, 'variation-11_extract')


    ## ASYCHRONOUS PROCESS (will get IP banned quicker - use proxy or VPN)
    # extract_p_bar = tqdm(total=0, desc='Extracting Articles...')

    # with futures.ThreadPoolExecutor(max_workers=5) as e1:
    #     articles_futures = []

    #     while True:

    #         active_page, next_button, button_inactive = chrome_driver.execute_script(
    #         """
    #             activePage = document.getElementsByClassName('is-active')[0].textContent;
    #             buttons = document.getElementsByClassName('pagination-link');
    #             nextButton = buttons[buttons.length-1];
    #             return [activePage, nextButton, nextButton.disabled];
    #         """)

    #         try:
    #             WebDriverWait(chrome_driver, 10).until(
    #                 EC.visibility_of_all_elements_located((By.XPATH,
    #                     "//div[@class='posts']//div[@class='post-preview']"))
    #             )
    #         except TimeoutException:
    #             print(f'Timeout on page {active_page}')
                
    #         article_urls = get_article_urls(chrome_driver.page_source)

    #         for url in article_urls:
    #             articles_futures.append(e1.submit(get_page_source, url.geturl()))

    #         extract_p_bar.total += len(article_urls)
    #         extract_p_bar.refresh()

    #         done, _ = futures.wait(articles_futures, return_when=futures.FIRST_COMPLETED)

    #         for aft in done:
    #             articles_futures.pop(articles_futures.index(aft))
    #             article = ArticleSoup(aft.result())
    #             extracted.append(article.extract())

    #             partial_url = article.url.strip('/').rpartition('/')[-1]
    #             article.save_source(partial_url, filepath=EXPORT_DIR)
    #             extract_p_bar.update(1)

    #         if button_inactive:
    #             break
    #         else:
    #             next_button.click()
        
    #     for aft in futures.as_completed(articles_futures):
    #         article = ArticleSoup(aft.result())
    #         extracted.append(article.extract())

    #         partial_url = article.url.strip('/').rpartition('/')[-1]
    #         article.save_source(partial_url, filepath=EXPORT_DIR)
    #         extract_p_bar.update(1)


if __name__ == '__main__':
    import sys

    _, EXPORT_DIR, URL, *FILES = sys.argv

    EXPORT_DIR = Path(EXPORT_DIR)

    if FILES:
        extract_from_file(FILES)
    else:
        main()