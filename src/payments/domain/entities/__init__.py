from typing import TypeVar



class BaseEntitiy:
    """
    Base class for domain entities.
    """
    __slots__ = ()


T_Domain_Entity = TypeVar("T_Domain_Entity", bound=BaseEntitiy)
