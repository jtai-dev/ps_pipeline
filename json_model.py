
import json
from datetime import datetime
from dateutil import parser as datetime_parser
from pathlib import Path


class JSONObject:

    def __init__(self, data: dict | list, name: str = 'root', as_root: bool = True):
        self.__as_root = as_root
        self.name = name
        self._data = data

    @property
    def _data(self): return self.__data

    @_data.setter
    def _data(self, data):
        if (isinstance(data, dict) and self.__as_root) or isinstance(data, list):
            self.__data = data
        elif isinstance(data, dict) and not self.__as_root:
            self.__data = {self.name: data}
        else:
            raise TypeError('Data has to either be a dictionary or list')

    def get(self, key_or_index):
        if isinstance(self.__data, dict):
            return self.__data.get(key_or_index)
        elif isinstance(self.__data, list):
            try:
                return self.__data[key_or_index]
            except KeyError:
                return None

    def save(self, filename, filepath):
        filepath = Path(filepath)
        filepath.mkdir(exist_ok=True)
        timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d-%H%M%S-%f')

        with open(filepath / f'{filename}_{self.__class__.__name__}_{timestamp}.json', 'w') as f:
            f.write(str(self))

    def __str__(self) -> str:
        if self.__as_root:
            return json.dumps(self.__data, indent=4)
        else:
            return json.dumps({self.name: self.__data}, indent=4)

    def __repr__(self) -> str: return str(self)


class Article(JSONObject):

    def __init__(self, data: dict, name='article', as_root=True):
        super().__init__(data, name, as_root)

    @property
    def title(self): return self.get('article_title')

    @property
    def timestamp(self): return self.get('article_timestamp')

    @property
    def text(self): return self.get('article_text')

    @property
    def type(self): return self.get('article_type')

    @property
    def tags(self): return self.get('article_tags')

    @property
    def url(self): return self.get('article_url')

    @property
    def publish_location(self): return self.get('publish_location')


class Articles(JSONObject):

    def __init__(self, data: list, name: str = 'articles'):
        super().__init__(data, name)

    @property
    def all(self) -> list[Article]:
        return [Article(article) for article in self._data]

    def select(self, limit) -> list[Article]: return [Article(article)
                                                      for article in self._data[:limit]]

    @property
    def latest(self):
        datetimes = set()

        for article in self.all:
            datetimes.add(datetime_parser.parse(article.timestamp))

        return max(datetimes)

    @property
    def urls(self):
        urls = set()

        for article in self.all:
            urls.add(article.url)

        return urls


# ===============#
### TRANSFORM ###
class TransformedArticle(Article):

    def __init__(self, data: dict, name='transformed_article'):
        super().__init__(data, name=name)

    @property
    def statements(self): return NLPExtracts(
        self.get('statements'), name='statements')

    @property
    def letters(self): return NLPExtracts(self.get('letters'), name='letters')
    @property
    def speech(self): return NLPExtracts(self.get('letters'), name='speech')

    @property
    def interviews(self): return NLPExtracts(
        self.get('letters'), name='interviews')


class TransformedArticles(JSONObject):
    def __init__(self, data: dict | list, name: str = 'root', as_root: bool = True):
        super().__init__(data, name, as_root)

    @property
    def all(self) -> list[TransformedArticle]:
        return [TransformedArticle(article) for article in self._data]


class NLPExtract(JSONObject):
    def __init__(self, data: dict, name: str = 'nlp_extract', as_root: bool = True):
        super().__init__(data, name, as_root)

    @property
    def attributed(self) -> list: return self.get('attributed')

    @property
    def contents(self): return TransformedContents(self.get('contents'))


class NLPExtracts(JSONObject):
    def __init__(self, data: list, name: str = 'nlp_extracts'):
        super().__init__(data, name)

    @property
    def all(self) -> list[NLPExtract]: return [NLPExtract(statement, name=self.name)
                                               for statement in self._data]


class SpanToReplace(JSONObject):
    def __init__(self, data: dict, name: str = 'root', as_root: bool = True):
        super().__init__(data, name, as_root)

    @property
    def start(self): return self.get('start')

    @property
    def end(self): return self.get('end')


class SpansToReplace(JSONObject):
    def __init__(self, data: list, name: str = 'root'):
        super().__init__(data, name)

    @property
    def all(self) -> list[SpanToReplace]: return [SpanToReplace(to_replace)
                                                  for to_replace in self._data]


class TransformedContent(JSONObject):
    def __init__(self, data: dict, name: str = 'content', as_root: bool = True):
        super().__init__(data, name, as_root)

    @property
    def start(self): return self.get('start')

    @property
    def end(self): return self.get('end')

    @property
    def text(self) -> str: return self.get('text')

    @property
    def to_replace(
        self) -> SpansToReplace: return SpansToReplace(self.get('to_replace'))


class TransformedContents(JSONObject):
    def __init__(self, data: list, name: str = 'contents'):
        super().__init__(data, name)

    @property
    def all(self) -> list[TransformedContent]: return [TransformedContent(content)
                                                       for content in self._data]


# ***************#


# ===============#
### LOAD ###
class HarvestExpanded(JSONObject):
    def __init__(self, data: dict | list, name: str = 'harvest', as_root: bool = True):
        super().__init__(data, name, as_root)

    @property
    def candidate_id(self): return self.get('candidate_id')

    @property
    def candidate_name(self): return self.get('candidate_name')

    @property
    def harvests(self): return self.get('harvests')


class Harvests(JSONObject):
    def __init__(self, data: list, name: str = 'harvests', as_root: bool = True):
        super().__init__(data, name, as_root)

    def all(self):
        return [Harvest(harvest) for harvest in self._data]


class Harvest(JSONObject):
    def __init__(self, data: dict, name: str = 'harvest', as_root: bool = True):
        super().__init__(data, name, as_root)


class CondensedHarvest(JSONObject):
    def __init__(self, data: dict, name: str = 'condensed_harvest', as_root: bool = True):
        super().__init__(data, name, as_root)

    @property
    def candidate_id(self): return self.get('candidate_id')
    @property
    def speechtype_id(self): return self.get('speechtype_id')
    @property
    def title(self): return self.get('title')
    @property
    def speechdate(self): return self.get('speechdate')
    @property
    def location(self): return self.get('location')
    @property
    def url(self): return self.get('url')
    @property
    def speechtext(self): return self.get('speechtext')
    @property
    def review(self) -> bool: return self.get('review')
    @property
    def review_message(self) -> str: return self.get('review_message')


class CondensedHarvests(JSONObject):
    def __init__(self, data: dict | list, name: str = 'condensed_harvests', as_root: bool = True):
        super().__init__(data, name, as_root)

    @property
    def all(self) -> list[CondensedHarvest]: return [CondensedHarvest(harvest) for harvest in self._data]
# **************#
