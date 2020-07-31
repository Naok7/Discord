from typing import Any, Optional, Union, List, Tuple, Iterator, Callable, TypeVar, Coroutine, Generic
from .core import Command
from .context import Context

_CT = TypeVar('_CT', bound=Context)
_L = TypeVar('_L', bound=Callable[..., Coroutine[Any, Any, Any]])

class CogMeta(type):
    @classmethod
    def qualified_name(cls) -> str: ...

class Cog(Generic[_CT], metaclass=CogMeta):
    __cog_commands__: Any = ...

    def get_commands(self) -> List[Command[_CT]]: ...
    @property
    def qualified_name(self) -> str: ...
    @property
    def description(self) -> str: ...
    def walk_commands(self) -> Iterator[Command[_CT]]: ...
    def get_listeners(self) -> List[Tuple[str, Callable[..., Any]]]: ...
    @classmethod
    def listener(cls, name: Optional[str] = ...) -> Callable[[_L], _L]: ...
    def cog_unload(self) -> None: ...
    def bot_check_once(self, ctx: _CT) -> Union[bool, Coroutine[Any, Any, bool]]: ...
    def bot_check(self, ctx: _CT) -> Union[bool, Coroutine[Any, Any, bool]]: ...
    def cog_check(self, ctx: _CT) -> Union[bool, Coroutine[Any, Any, bool]]: ...
    async def cog_command_error(self, ctx: _CT, error: Any) -> None: ...
    async def cog_before_invoke(self, ctx: _CT) -> None: ...
    async def cog_after_invoke(self, ctx: _CT) -> None: ...
