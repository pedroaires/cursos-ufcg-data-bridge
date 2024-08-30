import logging

from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TableBuilder(ABC):
    def build(self, previous_task_result=None):
        logger.info(msg=f"Building table {self.__class__.__name__}")
        result = self._build_impl(previous_task_result)
        return result

    @abstractmethod
    def _build_impl(self, previoues_task_result=None):
        raise NotImplementedError("Subclasses must implement this method")