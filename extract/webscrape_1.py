
from importlib import import_module

from pathlib import Path
from collections import defaultdict
from dateutil.parser import parse as datetimeparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from tqdm import tqdm

# Internal library packages and modules
if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))


from json_model import Articles


def get_article_json(compare_file):
    import json

    with open(compare_file, 'r') as f:
        return Articles(json.load(f))


def main(main_url, module):

    extract_module = import_module(f'extract.extract.{module}')
    
    html_dir = Path(EXPORT_DIR) / 'HTML_FILES'
    extract_dir = Path(EXPORT_DIR) / 'EXTRACT_FILES'

    html_dir.mkdir(exist_ok=True)
    extract_dir.mkdir(exist_ok=True)

    past_article_json = get_article_json(
        COMPARE_FILE) if COMPARE_FILE else None
    latest_collected = past_article_json.latest if past_article_json else None
    past_urls = past_article_json.urls if past_article_json else None

    chrome_service = Service('chromedriver')
    chrome_options = Options()
    chrome_options.add_argument('incognito')
    # chrome_options.add_argument('headless')
    chrome_driver = webdriver.Chrome(
        service=chrome_service, options=chrome_options)

    chrome_driver.get(main_url)

    articles = []
    page_urls = extract_module.get_page_urls(
        chrome_driver.page_source, main_url)
    pages_with_errors = defaultdict(list)

    listing_p_bar = tqdm(total=len(page_urls),
                         desc='Article listing iterated...')
    articles_p_bar = tqdm(total=0, desc='Articles gathered...')

    for p_link in page_urls:

        try:
            chrome_driver.get(p_link.geturl())

            article_urls = extract_module.get_article_urls(
                chrome_driver.page_source, main_url)

            articles_p_bar.total = int((articles_p_bar.n + len(article_urls))/(
                1 if not listing_p_bar.n else listing_p_bar.n) * listing_p_bar.total)
            articles_p_bar.refresh()

            for a_link in article_urls:
                try:
                    if a_link:
                        chrome_driver.get(a_link.geturl())

                        article_soup = extract_module.ArticleSoup(
                            chrome_driver.page_source)

                        # Only collect if the timestamp is greater than the last collected timestamp
                        if past_article_json and article_soup.timestamp:
                            if (datetimeparse(article_soup.timestamp) <= latest_collected or article_soup.url in past_urls):
                                break

                        partial_url = article_soup.url.strip(
                            '/').rpartition('/')[-1] if article_soup.url else "article_title"

                        articles.append(article_soup)
                        article_soup.save(partial_url, filepath=html_dir)

                        articles_p_bar.update(1)

                except WebDriverException:
                    pages_with_errors[p_link.geturl()].append(a_link.geturl())
                    continue
            else:
                listing_p_bar.update(1)
                continue

            break

        except WebDriverException:
            pages_with_errors[p_link.geturl()]
            continue

    extracted = [article.extract() for article in articles]
    articles_json = Articles(extracted)
    articles_json.save(filename=module, filepath=extract_dir)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(prog='ps_automation_webscrape_1')
    parser.add_argument('module')
    parser.add_argument('url')
    parser.add_argument('exportdir')
    parser.add_argument('-cf', '--comparefile')

    args = parser.parse_args()
    EXPORT_DIR = Path(args.exportdir)
    COMPARE_FILE = Path(args.comparefile) if args.comparefile else None

    main(args.url, args.module)
