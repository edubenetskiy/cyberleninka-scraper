import logging
import os
import re
import urllib.parse

import bs4
import requests
from selenium import webdriver as selenium_webdriver

logger = logging.getLogger(__name__)


class Article:
    slug: str
    url: str
    title: str
    abstract_description: str = None
    full_text_body: str = None
    download_url: str = None


def search_articles(query_keywords: str, max_search_pages=10):
    logger.info(f"Searching articles for query [{query_keywords}]")
    for search_page_number in range(1, max_search_pages + 1):
        search_page_url_parameters = urllib.parse.urlencode(query={'q': query_keywords, 'page': search_page_number},
                                                            quote_via=urllib.parse.quote)
        search_page_url = f"https://cyberleninka.ru/search?{search_page_url_parameters}"
        logger.debug(f"Loading search page {search_page_number}: {search_page_url}")
        search_page_html = download_page_html(search_page_url)
        search_page_soup = bs4.BeautifulSoup(search_page_html, features='lxml')
        search_result_elements: bs4.ResultSet = search_page_soup.find(id='search-results').find_all('li')
        search_result_element: bs4.Tag
        for search_result_element in search_result_elements:
            article = Article()

            article.title = search_result_element.select_one('.title').get_text()
            relative_url = search_result_element.select_one('.title').select_one('a')['href']
            article.url = "https://cyberleninka.ru" + relative_url
            article.slug = re.match(r"^/article/n/(?P<slug>.+)$", relative_url).group('slug')

            article_html = download_page_html(article.url)
            article_soup = bs4.BeautifulSoup(article_html, features='lxml')

            abstract_description_element = article_soup.select_one('.abstract')
            if abstract_description_element is not None:
                article.abstract_description = abstract_description_element.select_one('p').get_text()

            full_text_element = article_soup.select_one('.ocr')
            if full_text_element is not None:
                article.full_text_body = full_text_element.get_text()

            download_url = article.url + '/pdf'
            if requests.head(download_url).ok:
                article.download_url = download_url

            logger.info(f"Found article “{article.title}” <{article.url}>")
            yield article


def download_page_html(url):
    logger.debug("Creating Selenium WebDriver...")
    driver = create_web_driver()
    logger.debug("Created Selenium WebDriver")
    try:
        logger.debug("Downloading page: " + url)
        driver.get(url)
        logger.debug("Page downloaded")
        return driver.page_source
    finally:
        logger.debug("Closing connection to Selenium WebDriver")
        driver.quit()


def create_web_driver(max_attempts=3):
    selenium_grid_url = os.environ.get("SELENIUM_GRID_URL", default='http://127.0.0.1:4444/wd/hub')
    try:
        return selenium_webdriver.Remote(command_executor=selenium_grid_url)
    except Exception as e:
        if max_attempts > 0:
            create_web_driver(max_attempts=max_attempts - 1)
        raise Exception(f'Cannot create Selenium WebDriver using remote server <{selenium_grid_url}>. '
                        f'Is Selenium Grid running?') from e
