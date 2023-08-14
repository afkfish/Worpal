from dataclasses import dataclass, field
import datetime as dt
import math
from datetime import timedelta

import discord
from discord import VoiceChannel, Embed


@dataclass
class Track:
    query: str
    user: discord.User
    spotify: bool = False
    artists: [str] = field(default_factory=list)
    id: str = None
    title: str = None
    source: str = None
    thumbnail: str = None
    duration: int = 0
    channel: VoiceChannel = None
    start: dt.datetime = dt.datetime.utcnow()

    def get_embed(self) -> Embed:
        embed = Embed(color=0x152875, title=self.title)
        embed.set_thumbnail(url=self.thumbnail)
        if len(self.artists) > 0:
            embed.add_field(name="Artists", value=", ".join(self.artists))
        embed.set_footer(text=f"Requested by: {self.user.name}")

        return embed

    def is_valid(self) -> bool:
        return bool(self.title and self.source)

    def get_position(self) -> timedelta:
        return dt.datetime.utcnow() - self.start

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
