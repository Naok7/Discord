"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations


from typing import (
    Dict,
    Optional,
    List,
    TYPE_CHECKING,
    Union,
    AsyncIterator,
    NamedTuple
)

import datetime

from .enums import PollLayoutType, try_enum
from . import utils
from .emoji import PartialEmoji, Emoji
from .user import User

if TYPE_CHECKING:
    from typing_extensions import Self

    from .message import Message, PartialMessage
    from .abc import Snowflake
    from .state import ConnectionState
    from .member import Member

    from .types.poll import (
        Poll as PollPayload,
        PollMedia as PollMediaPayload,
        PollAnswerCount as PollAnswerCountPayload,
        PollWithExpiry as PollWithExpiryPayload,
        FullPoll as FullPollPayload,
        PollAnswerWithID as PollAnswerWithIDPayload,
    )

    PollMessage = Union[PartialMessage, Message]


__all__ = (
    'Poll',
    'PollAnswer',
    'PollAnswerCount',
    'PollMedia',
)

MISSING = utils.MISSING
PollMediaEmoji = Union[PartialEmoji, Emoji, str]


class PollMedia(NamedTuple):
    """Represents the poll media for a poll item.

    Attributes
    ----------
    text: :class:`str`
        The displayed text
    emoji: Optional[Union[:class:`PartialEmoji`, :class:`Emoji`, :class:`str`]]
        The attached emoji for this media. This will always be ignored for a poll
        question media.
    """

    text: str
    emoji: Optional[PollMediaEmoji] = None

    def to_dict(self) -> PollMediaPayload:
        """Returns an API valid payload for this tuple."""

        payload = {'text': self.text}

        if self.emoji:
            if isinstance(self.emoji, Emoji):
                payload['emoji'] = {'name': self.emoji.name, 'id': self.emoji.id}  # type: ignore

            elif isinstance(self.emoji, PartialEmoji):
                payload['emoji'] = self.emoji.to_dict()  # type: ignore

            else:
                payload['emoji'] = {'name': str(self.emoji)}  # type: ignore

        return payload  # type: ignore

    @classmethod
    def from_dict(cls, *, data: PollMediaPayload) -> PollMedia:
        """Returns a new instance of this class from a payload."""

        return cls(text=data['text'], emoji=PartialEmoji.from_dict(data.get('emoji', {})))  # type: ignore


class PollAnswerBase:

    if TYPE_CHECKING:
        id: int
        _message: Optional[Message]
        _state: Optional[ConnectionState]

    async def users(self, *, after: Snowflake = MISSING, limit: int = 25) -> AsyncIterator[Union[User, Member]]:
        r"""|coro|

        Retrieves all the voters of this answer.

        .. warning::

            This can only be called when the poll is accessed via :attr:`Message.poll`.

        Parameters
        ----------
        after: :class:`Snowflake`
            Fetches users after this ID.
        limit: :class:`int`
            The max number of users to return. Can be up to 100.

        Raises
        ------
        HTTPException
            Retrieving the users failed.

        Yields
        ------
        Union[:class:`User`, :class:`Member`]
            The users that voted for this poll answer. This can be a :class:`Member` object if the poll
            is in a guild-message context, for other contexts it will always return a :class:`User`, or when
            the member left the guild.
        """

        # As this is the same implementation for both PollAnswer objects
        # we should just recycle this.

        if not self._message or not self._state:  # Make type checker happy
            raise RuntimeError('You cannot fetch users in a non-message-attached poll')

        data = await self._state.http.get_poll_answer_voters(
            self._message.channel.id,
            self._message.id,
            self.id,
            after.id if after is not MISSING else MISSING,
            limit
        )

        if not self._message.guild:
            for user in data.get('users'):
                yield User(state=self._state, data=user)

        else:
            guild = self._message.guild

            for user in data.get('users'):
                member = guild.get_member(int(user['id']))

                yield member or User(state=self._state, data=user)


class PollAnswerCount(PollAnswerBase):
    """Represents a poll answer count.

    This is not meant to be user-constructed but instead obtained by the results in
    :attr:`Poll.answer_counts`

    Attributes
    ----------
    id: :class:`int`
        The answer ID.
    self_voted: :class:`bool`
        Whether the current client has voted for this answer or not.
    count: :class:`int`
        The number of votes for this answer.
    """

    __slots__ = (
        '_state',
        '_message',
        'id',
        'self_voted',
        'count',
    )

    def __init__(self, *, state: ConnectionState, message: PollMessage, data: PollAnswerCountPayload) -> None:
        self._state: ConnectionState = state
        self._message: PollMessage = message

        self.id: int = int(data.get('id'))
        self.self_voted: bool = data.get('me_voted')
        self.count: int = data.get('count')

    def __repr__(self) -> str:
        return f'<PollAnswerCount id={self.id} resolved={self.resolved!r}> self_voted={self.self_voted}'

    @property
    def original_message(self) -> PollMessage:
        """Union[:class:`PartialMessage`, :class:`Message`]: Returns the original message the poll of this answer is in."""
        return self._message

    @property
    def resolved(self) -> PollAnswer:
        """:class:`PollAnswer`: Returns the resolved poll answer of this count."""
        return self.original_message.poll.get_answer(self.id)  # type: ignore # This will always be a value

    @property
    def poll(self) -> Poll:
        """:class:`Poll`: Returns the poll that this answer belongs to."""
        return self._message.poll  # type: ignore


class PollAnswer(PollAnswerBase):
    """Represents a poll's answer.

    .. container:: operations

        .. describe:: str(x)

            Returns this answer's text, if any.

    Attributes
    ----------
    id: :class:`int`
        The ID of this answer.
    media: :class:`PollMedia`
        A :class:`NamedTuple` containing the raw data of this answers media.
    """

    __slots__ = ('media', 'id', '_state', '_message')

    def __init__(
        self,
        *,
        message: Optional[PollMessage],
        poll: Optional[Poll] = None,  # Defaults to message poll
        data: PollAnswerWithIDPayload,
    ) -> None:
        self._state: Optional[ConnectionState] = message._state if message else None
        self._message: Optional[PollMessage] = message
        self._poll: Poll = message.poll if message else poll

        self.media: PollMedia = PollMedia.from_dict(data=data['poll_media'])
        # Moved all to 'media' NamedTuple so it is accessed via properties
        self.id: int = int(data['answer_id'])

    def __repr__(self) -> str:
        return f'<PollAnswer id={self.id} media={self.media}>'

    @classmethod
    def from_params(
        cls,
        id: int,
        text: str,
        emoji: Optional[PollMediaEmoji] = None,
        *,
        poll: Poll,
    ) -> Self:
        poll_media: PollMediaPayload = {'text': text}
        if emoji:
            if isinstance(emoji, Emoji):
                poll_media['emoji'] = {'name': emoji.name}  # type: ignore

                if emoji.id:
                    poll_media['emoji']['id'] = emoji.id
            elif isinstance(emoji, PartialEmoji):
                poll_media['emoji'] = emoji.to_dict()  # type: ignore
            else:
                poll_media['emoji'] = {'name': str(emoji)}

        payload: PollAnswerWithIDPayload = {'answer_id': id, 'poll_media': poll_media}

        return cls(data=payload, message=poll.message, poll=poll)

    @property
    def text(self) -> str:
        """:class:`str`: Returns this answer display text."""
        return self.media.text

    @property
    def emoji(self) -> Optional[Union[PartialEmoji, Emoji]]:
        """Optional[:class:`PartialEmoji`]: Returns this answer display emoji, is any."""
        if isinstance(self.media.emoji, str):
            return PartialEmoji.from_str(self.media.emoji)
        return self.media.emoji

    @utils.cached_property
    def poll(self) -> Optional[Poll]:
        """Optional[:class:`Poll`]: The parent poll of this answer."""

        return self._poll

    def get_count(self) -> Optional[PollAnswerCount]:
        """Returns this answer's count data, if available.

        .. warning::

            This will **always** return ``None`` if it was added to a user-constructed poll object via
            :meth:`Poll.add_answer`.

        Returns
        -------
        Optional[:class:`PollAnswerCount`]
            This poll's answer count, or ``None`` if not available.
        """

        if not self._message:
            return None
        return self._message.poll.get_answer_count(id=self.id)  # type: ignore # Message will ALWAYS be a value here

    def _to_dict(self) -> PollMediaPayload:
        data: Dict[str, Union[str, Dict[str, Union[str, int]]]] = dict()  # Type hinted to make type-checker happy
        data['text'] = self.text

        if self.emoji is not None:
            if isinstance(self.emoji, PartialEmoji):
                data['emoji'] = self.emoji.to_dict()  # type: ignore
            else:
                data['emoji'] = {'name': str(self.emoji)}

                if hasattr(self.emoji, 'id'):
                    data['emoji']['id'] = int(self.emoji.id)

        return data  # type: ignore # Type Checker complains that this dict's type ain't PollAnswerMediaPayload


class Poll:
    """Represents a message's Poll.

    .. container:: operations

        .. describe:: str(x)

            Returns the Poll's question

        .. describe:: len(x)

            Returns the Poll's answer amount.

    .. versionadded:: 2.4

    Parameters
    ----------
    question: Union[:class:`PollMedia`, :class:`str`]
        The poll's question media. Text can be up to 300 characters.

        .. warning::

            At the moment, this *does not* support emojis.

    duration: :class:`datetime.timedelta`
        The duration of the poll.
    multiselect: :class:`bool`
        Whether users are allowed to select more than
        one answer.
    layout_type: :class:`PollLayoutType`
        The layout type of the poll.
    """

    __slots__ = (
        'multiselect',
        '_answers',
        'duration',
        '_hours_duration',
        'layout_type',
        '_question_media',
        '_message',
        '_results',
        '_expiry',
        '_finalized',
        '_state',
        '_counts',
    )

    def __init__(
        self,
        question: Union[str, PollMedia],
        duration: datetime.timedelta,
        *,
        multiselect: bool = False,
        layout_type: PollLayoutType = PollLayoutType.default,
    ) -> None:
        if isinstance(question, str):
            self._question_media: PollMedia = PollMedia(text=question, emoji=None)
        else:
            self._question_media: PollMedia = question  # At the moment this only supports text, so no need to add emoji support
        self._answers: List[PollAnswer] = []
        self.duration: datetime.timedelta = duration
        self._hours_duration: float = duration.total_seconds() / 3600

        self.multiselect: bool = multiselect
        self.layout_type: PollLayoutType = layout_type

        # NOTE: These attributes are set manually when calling
        # _from_data, so it should be ``None`` now.
        self._message: Optional[PollMessage] = None
        self._state: Optional[ConnectionState] = None
        self._finalized: bool = False
        self._counts: Optional[List[PollAnswerCount]] = None
        self._expiry: Optional[datetime.datetime] = None  # Manually set when constructed via '_from_data'

    @classmethod
    def _from_data(cls, *, data: Union[PollWithExpiryPayload, FullPollPayload], message: Message, state: ConnectionState) -> Self:
        # In this case, `message` will always be a Message object, not a PartialMessage
        answers = [PollAnswer(data=answer, poll=message.poll, message=message) for answer in data.get('answers')]  # type: ignore # 'message' will always have the 'poll' attr
        multiselect = data.get('allow_multiselect', False)
        layout_type = try_enum(PollLayoutType, data.get('layout_type', 1))
        question_data = data.get('question')
        question = question_data.get('text')
        expiry = datetime.datetime.fromisoformat(data['expiry'])  # If obtained via API, then expiry is set.
        duration = expiry - message.created_at  # self.created_at = message.created_at|duration = self.created_at - expiry

        if (duration.total_seconds() / 3600) > 168:  # As the duration may exceed little milliseconds then we fix it
            duration = datetime.timedelta(days=7)

        self = cls(
            duration=duration,
            multiselect=multiselect,
            layout_type=layout_type,
            question=question,
        )
        self._answers = answers
        self._message = message
        self._state = state
        self._expiry = expiry

        results = data.get('results', None)
        if results:
            self._finalized = results.get('is_finalized')
            self._counts = [
                PollAnswerCount(state=state, message=message, data=count) for count in results.get('answer_counts')
            ]

        return self

    def _to_dict(self) -> PollPayload:
        data = dict()
        data['allow_multiselect'] = self.multiselect
        data['question'] = self._question_media.to_dict()
        data['duration'] = self._hours_duration
        data['layout_type'] = self.layout_type.value
        data['answers'] = [{'poll_media': answer._to_dict()} for answer in self.answers]

        return data  # type: ignore

    def __str__(self) -> str:
        return self.question

    def __repr__(self) -> str:
        return f"<Poll duration={self.duration} question=\"{self.question}\" answers={self.answers}>"

    def __len__(self) -> int:
        return len(self.answers)

    @property
    def question(self) -> str:
        """:class:`str`: Returns this poll answer question string."""
        return self._question_media.text

    @property
    def emoji(self) -> Optional[PartialEmoji]:
        """Optional[:class:`PartialEmoji`]: Returns the emoji for this poll's question."""

        return None  # As of now, polls questions don't support emojis

    @property
    def answers(self) -> List[PollAnswer]:
        """List[:class:`PollAnswer`]: Returns a read-only copy of the answers"""
        return self._answers.copy()

    @property
    def expiry(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: A datetime object representing the poll expiry, this is autocalculated using a UTC :class:`datetime.datetime` object
        and adding the poll duration.

        .. note::
    
            This will **always** return ``None`` if the poll is not part of a message.
        """
        return self._expiry

    @utils.cached_property
    def answer_counts(self) -> Optional[List[PollAnswerCount]]:
        """Optional[List[:class:`PollAnswerCount`]]: Returns a read-only copy of the
        answer counts, or ``None`` if this is user-constructed."""

        if self._counts:
            return self._counts.copy()
        return None

    @property
    def created_at(self) -> Optional[datetime.datetime]:
        """:class:`datetime.datetime`: Returns the poll's creation time, or ``None`` if user-created."""

        if not self._message:
            return
        return self._message.created_at

    @property
    def message(self) -> Optional[PollMessage]:
        """Union[:class:`PartialMessage`, :class:`Message`]: The message this poll is from."""
        return self._message

    def is_finalized(self) -> bool:
        """:class:`bool`: Returns whether the poll has finalized.

        It always returns ``False`` if the poll is not part of a
        fetched message. You should consider accessing this method
        via :attr:`Message.poll`
        """

        return self._finalized

    def add_answer(
        self,
        *,
        text: str,
        emoji: Optional[Union[PartialEmoji, Emoji, str]] = None,
    ) -> Self:
        """Appends a new answer to this poll.

        Parameters
        ----------
        text: :class:`str`
            The text label for this poll answer. Can be up to 55
            characters.
        emoji: Union[:class:`PartialEmoji`, :class:`Emoji`, :class:`str`]
            The emoji to display along the text.

        Returns
        -------
        :class:`Poll`
            This poll with the new answer appended.
        """

        answer = PollAnswer.from_params(id=len(self.answers) + 1, text=text, emoji=emoji, poll=self)

        self._answers.append(answer)
        return self

    def get_answer(
        self,
        /,
        id: int,
    ) -> Optional[PollAnswer]:
        """Returns the answer with the provided ID or ``None`` if not found.

        Note that the ID, as Discord says, it is the index / row where the answer
        is located in the poll.

        Parameters
        ----------
        id: :class:`int`
            The ID of the answer to get.

        Returns
        -------
        Optional[:class:`PollAnswer`]
            The answer.
        """

        return utils.get(self.answers, id=id)

    def get_answer_count(
        self,
        /,
        id: int,
    ) -> Optional[PollAnswerCount]:
        """Returns the answer count with the provided ID or ``None`` if not found.

        Note that the ID, as Discord says, is the index or row where the answer is
        located in the poll UI.

        .. warning::

            This will **always** return ``None`` for user-created poll objects.

        Parameters
        ----------
        id: :class:`int`
            The ID of the answer to get the count of.

        Returns
        -------
        Optional[:class:`PollAnswerCount`]
            The answer count.
        """

        if not self.answer_counts:
            return None
        return utils.get(self.answer_counts, id=id)

    async def end(self) -> Message:
        """|coro|

        Ends the poll.

        .. warning::

            This can only be called when the poll is accessed via :attr:`Message.poll`.

        Raises
        ------
        RuntimeError
            This poll has no attached message.
        HTTPException
            Ending the poll failed.

        Returns
        -------
        :class:`Message`
            The updated message with the poll ended and with accurate results.
        """

        if not self._message or not self._state:  # Make type checker happy
            raise RuntimeError(
                'This method can only be called when a message is present, try using this via Message.poll.end()'
            )

        data = await self._state.http.end_poll(self._message.channel.id, self._message.id)

        self._message = Message(state=self._state, channel=self._message.channel, data=data)

        return self._message
