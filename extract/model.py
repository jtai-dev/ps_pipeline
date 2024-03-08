
# Built-ins
import html
import functools

from pathlib import Path
from datetime import datetime

# External Packages
from bs4 import BeautifulSoup


class HTMLSoup:

    _func_list = {}

    def __init__(self, page_source) -> None:
        self.__soup = BeautifulSoup(page_source, 'html.parser')

    @classmethod
    def register(cls, assign_to):

        def _registered(func):
            cls._func_list[assign_to] = func

            @functools.wraps(func)
            def deco(*args, **kwargs):
                result = func(*args, **kwargs)
                return result

            return deco

        return _registered

    def save_to_file(self, filename, filepath):

        filepath = Path(filepath)
        timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d-%H%M%S-%f')

        # Replaces any slashes that might confused it to be a filepath
        filename = filename.replace(
            '/', '', len(filename)).replace('\x07', '', len(filename))

        if len(filename) > 225:
            filename = filename[:225]

        with open(filepath / f"{filename}_{timestamp}.html", 'w') as f:
            f.write(str(self))

    def __getattr__(self, __name: str):
        if __name in self._func_list:
            return self._func_list[__name](soup=self.__soup)

    def __str__(self) -> str:
        return str(self.__soup)

    def __repr__(self) -> str:
        return self.__soup.prettify()


class ArticleSoup(HTMLSoup):

    def __init__(self, page_source):
        super().__init__(html.unescape(page_source))

    def extract(self): 
        return {
            'article_title': self.title,
            'article_timestamp': self.timestamp,
            'article_text': self.text,
            'article_type': self.type,
            'article_tags': self.tags,
            'article_url': self.url,
            'publish_location': self.location,
        }


def remove_formatting(soup):
    anchor = soup.find_all('a')
    emphasis = soup.find_all('em')
    italic = soup.find_all('i')
    strong = soup.find_all('strong')
    bold = soup.find_all('b')
    marked = soup.find_all('mark')
    small = soup.find_all('small')
    inserted = soup.find_all('ins')
    superscripted = soup.find_all('sup')
    subscripted = soup.find_all('sub')

    all_instances = anchor + emphasis + italic + strong + bold + \
        marked + small + inserted + subscripted +\
        superscripted

    for tag in all_instances:
        tag.unwrap()

    soup.smooth()
