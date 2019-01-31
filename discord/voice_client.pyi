import asyncio

from .abc import Connectable
from .guild import Guild
from .user import ClientUser
from .channel import VoiceChannel
from .player import AudioSource

from typing import Optional, Callable, ClassVar, Tuple

class VoiceClient:
    warn_nacl: ClassVar[bool]
    supported_modes: ClassVar[Tuple[str, ...]]

    session_id: str
    token: str
    endpoint: str
    channel: Connectable
    loop: asyncio.AbstractEventLoop
    source: Optional[AudioSource]

    @property
    def guild(self) -> Optional[Guild]: ...

    @property
    def user(self) -> ClientUser: ...

    async def start_handshake(self) -> None: ...

    async def terminate_handshake(self, *, remove: bool = ...) -> None: ...

    async def connect(self, *, reconnect: bool = ..., _tries: int = ..., do_handshake: bool = ...) -> None: ...

    async def poll_voice_ws(self, reconnect: bool) -> None: ...

    async def disconnect(self, *, force: bool = ...) -> None: ...

    async def move_to(self, channel: VoiceChannel) -> None: ...

    def is_connected(self) -> bool: ...

    def play(self, source: AudioSource, *, after: Optional[Callable[[Optional[Exception]], None]] = ...) -> None: ...

    def is_playing(self) -> bool: ...

    def is_paused(self) -> bool: ...

    def stop(self) -> None: ...

    def pause(self) -> None: ...

    def resume(self) -> None: ...

    def send_audio_packet(self, data: bytes, *, encode: bool = ...) -> None: ...
