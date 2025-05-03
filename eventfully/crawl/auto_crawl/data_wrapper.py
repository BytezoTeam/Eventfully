from typing import Self
from abc import abstractmethod
from json import loads, dumps
import io
import csv

from jsonpath_ng import parse, DatumInContext
from parsel import Selector


class AbstractDataWrapper:
    def __init__(self, data: str):
        self._data = data

    @abstractmethod
    def get_objects(self, query: str) -> list[Self]:
        pass

    @abstractmethod
    def get_value(self, query: str) -> str | None:
        pass

    @abstractmethod
    def get_values(self, query: str) -> list[str]:
        pass

    def __repr__(self) -> str:
        return self._data


class HTMLDataWrapper(AbstractDataWrapper):
    def __init__(self, data: str):
        super().__init__(data)

    def get_objects(self, query: str) -> list["HTMLDataWrapper"]:
        selector = Selector(text=self._data)
        new_objects = selector.xpath(query)
        return [HTMLDataWrapper(data=new_object.get()) for new_object in new_objects]

    def get_value(self, query: str) -> str | None:
        selector = Selector(text=self._data)
        return selector.xpath(query).get()

    def get_values(self, query: str) -> list[str]:
        selector = Selector(text=self._data)
        return selector.xpath(query).getall()


class JSONDataWrapper(AbstractDataWrapper):
    def __init__(self, data: str):
        super().__init__(data)

    def get_objects(self, query: str) -> list["JSONDataWrapper"]:
        dict_data = loads(self._data)
        results: list[DatumInContext] = parse(query).find(dict_data)
        return [JSONDataWrapper(data=dumps(new.value)) for new in results]

    def get_value(self, query: str) -> str | None:
        dict_data = loads(self._data)
        return parse(query).find(dict_data)[0].value

    def get_values(self, query: str) -> list[str]:
        dict_data = loads(self._data)
        results: list[DatumInContext] = parse(query).find(dict_data)
        return [result.value for result in results]


class CSVDataWrapper(AbstractDataWrapper):
    def __init__(self, data: str):
        super().__init__(data)

    def get_objects(self, query: str) -> list["CSVDataWrapper"]:
        lines = self._data.splitlines()
        events = lines[1:]
        return [CSVDataWrapper(lines[0] + "\n" + event) for event in events]

    def get_value(self, query: str) -> str | None:
        text_buffer = io.StringIO(self._data)
        reader = csv.DictReader(text_buffer)
        result = list(reader)[0]
        if query not in result:
            return None
        return result[query]

    def get_values(self, query: str) -> list[str]:
        raise NotImplementedError("CSV data type does not support get_values")
