import websockets  # type: ignore
import asyncio
import threading
from .client import Client, VoiceClient
from .activity import _ActivityTag
from .enums import Status

from typing import Any, Optional, Union, Iterable, NamedTuple, Callable, Dict, ClassVar, TypeVar, Type
from mypy_extensions import TypedDict

class KeepAlivePayloadDict(TypedDict):
    op: int
    d: int

class ResumeWebSocket(Exception):
    shard_id: int

    def __init__(self, shard_id: int) -> None: ...


class EventListener(NamedTuple):
    predicate: Callable[[Any], bool]
    event: str
    result: Optional[Callable[[Any], Any]]
    future: asyncio.Future[Any]


class KeepAliveHandler(threading.Thread):
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def run(self) -> None: ...

    def get_payload(self) -> KeepAlivePayloadDict: ...

    def stop(self) -> None: ...

    def ack(self) -> None: ...


class VoiceKeepAliveHandler(KeepAliveHandler):
    ...


_T = TypeVar('_T', bound='DiscordWebSocket')

class DiscordWebSocket(websockets.client.WebSocketClientProtocol):
    DISPATCH: ClassVar[int]
    HEARTBEAT: ClassVar[int]
    IDENTIFY: ClassVar[int]
    PRESENCE: ClassVar[int]
    VOICE_STATE: ClassVar[int]
    VOICE_PING: ClassVar[int]
    RESUME: ClassVar[int]
    RECONNECT: ClassVar[int]
    REQUEST_MEMBERS: ClassVar[int]
    INVALIDATE_SESSION: ClassVar[int]
    HELLO: ClassVar[int]
    HEARTBEAT_ACK: ClassVar[int]
    GUILD_SYNC: ClassVar[int]

    session_id: Optional[int]
    sequence: Optional[int]

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    @classmethod
    async def from_client(cls: Type[_T], client: Client, *, shard_id: Optional[int] = ..., session: Optional[int] = ...,
                          sequence: Optional[int] = ..., resume: bool = ...) -> _T: ...

    def wait_for(self, event: str, predicate: Callable[[Any], bool],
                 result: Optional[Callable[[Any], Any]] = ...) -> asyncio.Future[Any]: ...

    async def identify(self) -> None: ...

    async def resume(self) -> None: ...

    async def received_message(self, msg: Union[str, bytes]) -> None: ...

    @property
    def latency(self) -> float: ...

    async def poll_event(self) -> None: ...

    async def send(self, data: Union[str, bytes]) -> None: ...

    async def send_as_json(self, data: Any) -> None: ...

    async def change_presence(self, *, activity: Optional[_ActivityTag] = ..., status: Optional[str] = ..., afk: bool = ..., since: float = ...) -> None: ...

    async def request_sync(self, guild_ids: Iterable[int]) -> None: ...

    async def voice_state(self, guild_id: int, channel_id: Optional[int], self_mute: bool = False, self_deaf: bool = False) -> None: ...

    async def close_connection(self, *args: Any, **kwargs: Any) -> None: ...

_VT = TypeVar('_VT', bound='DiscordVoiceWebSocket')

class DiscordVoiceWebSocket(websockets.client.WebSocketClientProtocol):
    IDENTIFY: ClassVar[int]
    SELECT_PROTOCOL: ClassVar[int]
    READY: ClassVar[int]
    HEARTBEAT: ClassVar[int]
    SESSION_DESCRIPTION: ClassVar[int]
    SPEAKING: ClassVar[int]
    HEARTBEAT_ACK: ClassVar[int]
    RESUME: ClassVar[int]
    HELLO: ClassVar[int]
    INVALIDATE_SESSION: ClassVar[int]

    async def send_as_json(self, data: Any) -> None: ...

    async def resume(self) -> None: ...

    async def identify(self) -> None: ...

    @classmethod
    async def from_client(cls: Type[_VT], client: VoiceClient, *, resume: bool = False) -> _VT: ...

    async def select_protocol(self, ip: str, port: str) -> None: ...

    async def speak(self, is_speaking: bool = ...) -> None: ...

    async def received_message(self, msg: Dict[str, Any]) -> None: ...

    async def initial_connection(self, data: Dict[str, Any]) -> None: ...

    async def load_secret_key(self, data: Dict[str, Any]) -> None: ...

    async def poll_event(self) -> None: ...

    async def close_connection(self, *args: Any, **kwargs: Any) -> None: ...
