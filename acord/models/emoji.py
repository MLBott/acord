from __future__ import annotations
from os import path
from re import L

from typing import Any, List, Optional
import pydantic
import datetime

from acord.core.helpers import Route, isInt
from acord.bases import Hashable
from acord.models import User


class Emoji(pydantic.BaseModel, Hashable):
    conn: Any                               # Connection Object - for internal use

    id: int                                 # ID of emoji
    name: str                               # Name of emoji
    roles: Optional[List[Any]]              # List of roles TODO: Role object
    user: Optional[User]                    # User who created the emoji
    require_colons: Optional[bool]          # Whether this emoji must be wrapped in colons
    managed: Optional[bool]                 # Whether this emoji is managed
    animated: Optional[bool]                # Emoji is animated or not
    available: Optional[bool]               # Can be used or not - Lost due to server boosts

    """ Not provided by discord API """

    is_unicode: Optional[bool]              # Is the emoji unicode
    guild_id: Optional[int]                 # Guild were emoji belongs to
    deleted: Optional[bool] = False         # Whether the emoji has been deleted internally

    # This has to be worked out manually
    created_at: Optional[datetime.datetime] # When the emoji was created

    @pydantic.validator('is_unicode')
    def _validate_unicode(cls, **kwargs) -> bool:
        if kwargs['values']['name'].isascii():
            return False
        return True

    @pydantic.validator('created_at')
    def _validate_createdat(cls, _, **kwargs) -> datetime.datetime:
        if _:
            raise ValueError('Time provided, not able to parse')

        toS = format(kwargs['values']['id'], 'b')
        # Discord timestamp number of bits
        deT = toS[:42]

        timestamp = int(deT, 2)
        timestamp += 1420070400000

        return datetime.datetime.fromtimestamp(timestamp)

    def discord_string(self):
        """ Returns the emoji as a string that discord identifies as an emoji """
        if self.is_unicode:
            return self.name

        if self.animated:
            return f'<a:{self.name}:{self.animated}>'
        return f'<:{self.name}:{self.id}>'
    
    async def delete(self, *, reason: Optional[str] = None, guild_id: Optional[int]) -> None:
        if guild_id and guild_id != self.guild_id:
            raise ValueError(f'Mismatching guild_id provided, expected {self.guild_id} got {guild_id}')
        guild_id = self.guild_id or guild_id

        if not guild_id:
            raise ValueError('Cannot delete emoji as no guild provided')

        await self.conn.request(
            Route("DELETE", path=f"/guilds/{self.guild_id}/emojis/{self.id}"),
            headers={"X-Audit-Log-Reason": reason}
        )

    async def edit(self, *, name: Optional[str] = None, 
                            roles: Optional[List[Any]] = None, 
                            reason: Optional[str] = None
    ) -> Emoji:
        if not (name or roles):
            raise ValueError('No parameters provided to edit')
        if all(i for i in roles if isInt(i)):
            roles = roles
        # TODO: role object
        # elif all(i for i in roles if isinstance(i, Role)):
        #     roles = list(map(lambda role: role.id, roles))
        else:
            raise ValueError('Incorrect roles provided')

        name = name or self.name
        roles = roles or list(map(lambda role: role.id, self.roles))

        await self.conn.request(
            Route("PATCH", path=f'/guilds/{self.guild_id}/emojis/{self.id}'),
            data={
                "name": name,
                "roles": roles
            },
            headers={'X-Audit-Log-Reason': reason}
        )
