import dataclasses
import datetime as dt

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
        self.start = None
        self.channel: VoiceChannel

    def get_embed(self) -> Embed:
        embed = Embed(color=0x152875, title="Track added to queue")
        embed.set_thumbnail(url=self.thumbnail)
        embed.add_field(name=self.title, value=str(dt.timedelta(seconds=self.duration)), inline=False)
        if len(self.artists) > 0:
            embed.add_field(name="Artists", value=", ".join(self.artists), inline=False)
        # embed.set_image(self.thumbnail)
        embed.set_footer(text=f"Requested by: {self.user.name}")

        return embed

    def is_valid(self) -> bool:
        return bool(self.title and self.source)
