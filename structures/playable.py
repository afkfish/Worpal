from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from datetime import timedelta
from typing import override

from discord import VoiceChannel, Embed, User


@dataclass
class Playable:
    user: User
    id: str = ""
    title: str = ""
    image: str = None
    spotify: bool = False
    valid: bool = True

    def __bool__(self):
        return self.valid

    def get_embed(self) -> Embed:
        pass

    def get_first_track(self) -> Track:
        pass


@dataclass
class Track(Playable):
    query: str = ""
    artists: list[str] = field(default_factory=list)
    source: str = None
    duration: int = 0
    channel: VoiceChannel = None
    start: dt.datetime = dt.datetime.now()

    def __init__(self, query: str, user: User):
        self.query = query
        self.user = user

    @override
    def __bool__(self):
        return self.is_valid()

    @classmethod
    def from_playable(cls, playable: Playable, query: str):
        tmp = cls(query, playable.user)
        tmp.id = playable.id
        tmp.image = playable.image
        tmp.title = playable.title
        tmp.spotify = playable.spotify
        tmp.artists = []
        return tmp

    @override
    def get_embed(self) -> Embed:
        embed = Embed(color=0x152875, title=self.title)
        embed.set_thumbnail(url=self.image)
        if len(self.artists) > 0:
            embed.add_field(name="Artists", value=", ".join(self.artists))
        embed.set_footer(text=f"Requested by: {self.user.name}")

        return embed

    @override
    def get_first_track(self) -> Track:
        return self

    def is_valid(self) -> bool:
        return bool(self.title and self.source and self.valid)

    def get_position(self) -> timedelta:
        return dt.datetime.now() - self.start

    def get_progress(self) -> float:
        return self.get_position().seconds/self.get_duration().seconds

    def get_duration(self) -> timedelta:
        return dt.timedelta(seconds=self.duration)

    def progress_bar(self) -> str:
        bar = ""
        for i in range(11):
            if i == math.floor(self.get_progress()*12):
                bar += "⭕"
            else:
                bar += "▬"

        return bar

    def format_progress(self) -> str:
        seconds = math.floor(self.get_duration().seconds*self.get_progress())
        progress = dt.timedelta(seconds=seconds)

        return str(progress)


@dataclass
class Playlist(Playable):
    id: str
    user: User
    owner: str = None
    tracks: list[Track] = field(default_factory=list)

    @classmethod
    def from_playable(cls, playable: Playable):
        tmp = cls(playable.user, playable.id)
        tmp.image = playable.image
        tmp.title = playable.title
        tmp.spotify = playable.spotify
        return tmp

    @override
    def get_embed(self) -> Embed:
        embed = Embed(color=0x152875, title="Playlist added from spotify")
        embed.set_thumbnail(url=self.image)
        embed.add_field(name=self.title, value=self.owner, inline=False)

        return embed

    @override
    def get_first_track(self) -> Track:
        return self.tracks[0]
