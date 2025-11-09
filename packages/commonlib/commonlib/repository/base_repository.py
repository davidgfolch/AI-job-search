from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar('T')

class BaseRepository(ABC):
    """Base repository interface following Repository pattern"""
    
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    def find_all(self, filters: Dict[str, Any] = None) -> List[T]:
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        pass
    
    @abstractmethod
    def count(self, filters: Dict[str, Any] = None) -> int:
        pass