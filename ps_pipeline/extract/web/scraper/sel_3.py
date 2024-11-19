"""
Web Driver module open a browser object and executes a parser.
"""

__author__ = "Johanan Tai"

from pathlib import Path
from collections import defaultdict
from dateutil.parser import parse as datetimeparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
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
    chrome_driver_2 = webdriver.Chrome(service=chrome_service, options=chrome_options)

    chrome_driver.get(main_url)

    listing_p_bar = tqdm(total=1, desc="Article listing iterated...")
    articles_p_bar = tqdm(total=0, desc="Articles gathered...")

    articles = []
    pages_with_errors = defaultdict(list)

    while True:

        next_button, button_inactive = chrome_driver.execute_script(
            """
            buttons = document.getElementsByClassName('pagination-link');
            nextButton = buttons[buttons.length-1];
            return [nextButton, nextButton.disabled];
        """
        )

        try:
            WebDriverWait(chrome_driver, 10).until(
                EC.visibility_of_all_elements_located(
                    (By.XPATH, "//div[@class='posts']//div[@class='post-preview']")
                )
            )
        except TimeoutException:
            print("Timeout...")

        article_urls = web_parser.get_article_urls(chrome_driver.page_source, main_url)
        articles_p_bar.total = int(
            (articles_p_bar.n + len(article_urls))
            / (listing_p_bar.n if listing_p_bar.n else 1)
            * listing_p_bar.total
        )
        articles_p_bar.refresh()

        for a_link in article_urls:
            try:
                chrome_driver_2.get(a_link.geturl())

                ### ARTICLE EXTRACTION STARTS ###
                article_soup = web_parser.ArticleSoup(chrome_driver_2.page_source)

                # Stop collecting if the current article datetime is older or equal to
                # the last collected datetime
                if last_collected and article_soup.timestamp:
                    if datetimeparse(article_soup.timestamp) <= datetimeparse(
                        last_collected
                    ):
                        button_inactive = True
                        break

                partial_url = (
                    article_soup.url.strip("/").rpartition("/")[-1]
                    if article_soup.url
                    else "article_title"
                )

                article_soup.save_to_file(
                    html_path / "HTML_FILES",
                    partial_url,
                )
                articles.append(article_soup)

                ### ARTICLE EXTRACTION ENDS ###
                articles_p_bar.update(1)

            except WebDriverException:
                pages_with_errors[chrome_driver.current_url].append(a_link.geturl())
                continue
        else:
            listing_p_bar.update(1)
            continue

        if button_inactive:
            break
        else:
            listing_p_bar.total += 1
            listing_p_bar.refresh()
            next_button.click()

    return [a.extract() for a in articles]
