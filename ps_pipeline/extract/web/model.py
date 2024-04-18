import html
import functools
from pathlib import Path
from datetime import datetime

# External Packages
from bs4 import BeautifulSoup


class HTMLSoup:

    _attrs = {}

    def __init__(self, page_source) -> None:
        self.__soup = BeautifulSoup(page_source, "html.parser")

    @classmethod
    def register(cls, assign_to):
        def _registered(func):
            cls._attrs[assign_to] = func

            @functools.wraps(func)
            def deco(*args, **kwargs):
                result = func(*args, **kwargs)
                return result

            return deco

        return _registered

    @classmethod
    def deregister(cls, assign_to=None):
        if assign_to is None:
            cls._attrs.clear()
        else:
            cls._attrs.pop(assign_to)

    def __getattr__(self, _attr: str):
        if _attr in self._attrs:
            f = self._attrs.get(_attr)
            return f(soup=self.__soup)

    def __str__(self) -> str:
        return str(self.__soup)

    def __repr__(self) -> str:
        return self.__soup.prettify()

    def save_to_file(self, filepath: Path, filename):

        filepath.mkdir(exist_ok=True)
        timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M%S-%f")

        # Replaces any slashes that might confused it to be a filepath
        filename = filename.replace("/", "", len(filename)).replace(
            "\x07", "", len(filename)
        )

        with open(filepath / f"{filename[:225]}_{timestamp}.html", "w") as f:
            f.write(str(self))


class ArticleSoup(HTMLSoup):

    _attrs = {}

    def __init__(self, page_source):
        super().__init__(html.unescape(page_source))

    def extract(self):
        return {
            "article_title": self.title,
            "article_timestamp": self.timestamp,
            "article_text": self.text,
            "article_type": self.type,
            "article_tags": self.tags,
            "article_url": self.url,
            "publish_location": self.location,
        }


def remove_formatting(soup):
    anchor = soup.find_all("a")
    emphasis = soup.find_all("em")
    italic = soup.find_all("i")
    strong = soup.find_all("strong")
    bold = soup.find_all("b")
    marked = soup.find_all("mark")
    small = soup.find_all("small")
    inserted = soup.find_all("ins")
    superscripted = soup.find_all("sup")
    subscripted = soup.find_all("sub")

    all_instances = (
        anchor
        + emphasis
        + italic
        + strong
        + bold
        + marked
        + small
        + inserted
        + subscripted
        + superscripted
    )

    for tag in all_instances:
        tag.unwrap()

    soup.smooth()
