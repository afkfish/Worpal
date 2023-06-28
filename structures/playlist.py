from dataclasses import dataclass

from discord import Embed

from structures.track import Track


@dataclass
class PlayList:
    name: str
    image: str = None
    owner: str = None
    tracks: [Track] = None

    def get_embed(self) -> Embed:
        embed = Embed(color=0x152875, title="Playlist added from spotify")
        embed.set_thumbnail(url=self.image)
        embed.add_field(name=self.name, value=self.owner, inline=False)

        return embed
