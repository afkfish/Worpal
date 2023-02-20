import dataclasses
import datetime as dt
import math
from datetime import timedelta

import discord
from discord import VoiceChannel, Embed


@dataclasses.dataclass
class Track:
    def __init__(
            self,
            query: str = None,
            title: str = None,
            source: str = None,
            thumbnail: str = None,
            duration: int = 0,
            user: discord.User = None,
            spotify: bool = False
    ):
        self.query = query
        self.id = None
        self.title = title
        self.source = source
        self.thumbnail = thumbnail
        self.duration = duration
        self.user = user
        self.spotify = spotify
        self.artists = []
        self.start: dt.datetime = dt.datetime.utcnow()
        self.channel: VoiceChannel

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
            if i == self.get_progress()*12:
                bar += "⭕"
            else:
                bar += "▬"

        return bar

    def format_time(self) -> str:
        seconds = math.floor(self.get_duration().seconds/1000.0)
        hours = (str(seconds/(60*60)) + ":" if seconds/(60*60) > 0 else "")
        seconds %= 60*60
        minutes = ("0" + str(seconds/60) if seconds/60 < 10 else seconds/60)
        seconds %= 60
        return hours + minutes + ":" + ("0" + str(seconds) if seconds < 10 else seconds)
