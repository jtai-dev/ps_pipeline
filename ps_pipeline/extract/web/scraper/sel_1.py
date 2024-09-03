from pathlib import Path
from collections import defaultdict
from dateutil.parser import parse as datetimeparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from tqdm import tqdm


def scrape(
    main_url,
    web_parser,
    html_path: Path,
    last_collected=None,
):

    chrome_service = Service()
    chrome_options = Options()
    chrome_options.add_argument("incognito")
    chrome_options.add_argument("headless")
    chrome_driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    chrome_driver.get(main_url)

    page_urls = web_parser.get_page_urls(chrome_driver.page_source, main_url)

    listing_p_bar = tqdm(total=len(page_urls), desc="Article listing iterated...")
    articles_p_bar = tqdm(total=0, desc="Articles gathered...")

    articles = []
    pages_with_errors = defaultdict(list)

    for p_link in page_urls:

        try:
            chrome_driver.get(p_link.geturl())

            article_urls = web_parser.get_article_urls(
                chrome_driver.page_source, main_url
            )

            articles_p_bar.total = int(
                (articles_p_bar.n + len(article_urls))
                / (1 if not listing_p_bar.n else listing_p_bar.n)
                * listing_p_bar.total
            )
            articles_p_bar.refresh()

            for a_link in article_urls:
                try:
                    if a_link:
                        chrome_driver.get(a_link.geturl())

                        ### ARTICLE EXTRACTION STARTS ###
                        article_soup = web_parser.ArticleSoup(chrome_driver.page_source)

                        # Stop collecting if the current article datetime is older or equal to
                        # the last collected datetime
                        if last_collected and article_soup.timestamp:
                            if datetimeparse(article_soup.timestamp) <= last_collected:
                                break

                        partial_url = (
                            article_soup.url.strip("/").rpartition("/")[-1]
                            if article_soup.url
                            else "article_title"
                        )

                        article_soup.save_to_file(
                            html_path,
                            partial_url,
                        )
                        articles.append(article_soup)
                        ### ARTICLE EXTRACTION ENDS ###

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

    return [a.extract() for a in articles]
