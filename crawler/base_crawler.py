from abc import ABC, abstractmethod
from typing import List, Dict

class LibraryCrawler(ABC):
    @abstractmethod
    def get_book_status(self, book_title: str) -> List[Dict]:
        pass
