"""
Module to parse and write as JSON objects. May serve as a backup to a relational ORM.
"""

__author__ = "Johanan Tai"

import json
from datetime import datetime
from dateutil.parser import parse as datetimeparse
from pathlib import Path


class JSONObject:
    def __init__(self, data: dict | list, as_root: bool = True):
        self.__as_root = as_root
        self._data = data

    @property
    def _data(self):
        return self.__data

    @property
    def name(self):
        return self.__class__.__name__

    @_data.setter
    def _data(self, data):
        if (isinstance(data, dict) and self.__as_root) or isinstance(data, list):
            self.__data = data
        elif isinstance(data, dict) and not self.__as_root:
            self.__data = {self.name: data}
        else:
            raise TypeError("Data has to either be a dictionary or list")

    def get(self, key_or_index):
        if isinstance(self.__data, dict):
            return self.__data.get(key_or_index)
        elif isinstance(self.__data, list):
            try:
                return self.__data[key_or_index]
            except KeyError:
                return None

    def save(self, export_path: Path, filename=None):

        export_path.mkdir(exist_ok=True)
        timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M%S-%f")

        with open(
            export_path / f"{filename if filename else ''}{self.name}_{timestamp}.json",
            "w",
        ) as f:
            f.write(str(self))

    def __len__(self):
        return len(self._data)

    def __str__(self) -> str:
        if self.__as_root:
            return json.dumps(self.__data, indent=4)
        else:
            return json.dumps({self.name: self.__data}, indent=4)

    def __repr__(self) -> str:
        return str(self)


class Article(JSONObject):
    def __init__(self, data: dict):
        super().__init__(data)

    @property
    def title(self):
        return self.get("title")

    @property
    def url(self):
        return self.get("source_url")

    @property
    def timestamp(self):
        return self.get("publish_time")

    @property
    def publish_location(self):
        return self.get("publish_location")

    @property
    def text(self):
        return self.get("raw_text")

    @property
    def type(self):
        return self.get("article_type")

    @property
    def tags(self):
        return self.get("article_tags")

    @property
    def web_id(self):
        return self.get("web_candidate_id")


class Articles(JSONObject):
    def __init__(self, data: list):
        super().__init__(data)

    @property
    def all(self) -> list[Article]:
        return [Article(article) for article in self._data]

    def select(self, limit) -> list[Article]:
        return [Article(article) for article in self._data[:limit]]

    @property
    def latest(self):
        datetimes = set()

        for article in self.all:
            if article.timestamp:
                datetimes.add(datetimeparse(article.timestamp))

        return max(datetimes)

    @property
    def urls(self):
        urls = set()

        for article in self.all:
            urls.add(article.url)

        return urls


# ===============
#   TRANSFORM
# ===============
class TransformedArticle(Article):
    def __init__(self, data: dict):
        super().__init__(data)

    @property
    def nlp_extracts(self):
        return NLPExtracts(self.get("statements"))


class TransformedArticles(JSONObject):
    def __init__(self, data: dict | list):
        super().__init__(data)

    @property
    def all(self) -> list[TransformedArticle]:
        return [TransformedArticle(article) for article in self._data]


class NLPExtract(JSONObject):
    def __init__(self, data: dict):
        super().__init__(data)

    @property
    def attributed(self):
        return self.get("attributed")

    @property
    def text(self):
        return self.get("text")

    @property
    def text_type(self):
        return self.get("text_type")

    @property
    def classification(self):
        return self.get("classification")


class NLPExtracts(JSONObject):
    def __init__(self, data: list):
        super().__init__(data)

    @property
    def all(self) -> list[NLPExtract]:
        return [NLPExtract(extract) for extract in self._data]

    @property
    def all_attributed(self):
        return {extract.attributed for extract in self.all if extract.attributed}


#   ###


# ===============
#      LOAD
# ===============
class HarvestArticle(JSONObject):
    def __init__(self, data: dict):
        super().__init__(data)

    @property
    def candidate_ids(self):
        return self.get("candidate_ids")

    @property
    def speechtype_id(self):
        return self.get("speechtype_id")

    @property
    def title(self):
        return self.get("title")

    @property
    def speechdate(self):
        return self.get("speechdate")

    @property
    def location(self):
        return self.get("location")

    @property
    def url(self):
        return self.get("url")

    @property
    def speechtext(self):
        return self.get("speechtext")

    @property
    def review(self) -> bool:
        return self.get("review")

    @property
    def review_message(self) -> str:
        return self.get("review_msg")


class HarvestArticles(JSONObject):
    def __init__(self, data: dict | list):
        super().__init__(data)

    @property
    def all(self) -> list[HarvestArticle]:
        return [HarvestArticle(harvest) for harvest in self._data]


#   ###
