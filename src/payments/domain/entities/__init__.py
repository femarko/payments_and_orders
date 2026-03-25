from typing import TypeVar



class BaseEntitiy: ...
"""
Base class for domain entities.
"""


T_Domain_Entity = TypeVar("T_Domain_Entity", bound=BaseEntitiy)
