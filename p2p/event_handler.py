from dataclasses import dataclass, field
from typing import Dict, Callable, Any, List

from .exceptions import HandlerMissingException


@dataclass
class EventHandler():
    """Super class instanciate elements that can call event handlers (such as Peer and Connection)."""

    handlers: Dict[str, Callable[[Any], Any]]
    handler_list: List[str] = field(default_factory=list)

    def handle(self, handler_type: str, *args) -> Any:
        """Calls a handler if existing, passing arguments.

        Args:
            handler_type (str): the handler type to call.

        Returns:
            Any: whatever the handler, if existing, returns
        """
        handler = self.handlers.get(handler_type, None)

        if handler is not None:
            return handler(*args)
        elif handler_type in self.handler_list:
            raise HandlerMissingException(f"{self.__name__} must have the following handlers: {self.handler_list}")
