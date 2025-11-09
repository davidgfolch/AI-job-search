from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

class DatabaseInterface(ABC):
    """Database interface for dependency inversion"""
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[Sequence] = None) -> List[tuple]:
        pass
    
    @abstractmethod
    def execute_single(self, query: str, params: Optional[Sequence] = None) -> Optional[tuple]:
        pass
    
    @abstractmethod
    def execute_count(self, query: str, params: Optional[Sequence] = None) -> int:
        pass
    
    @abstractmethod
    def execute_commit(self, query: str, params: Optional[Sequence] = None) -> int:
        pass