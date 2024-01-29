from discord import Embed


class Player:
    def __init__(self, data: any, _uuid: str, avatar: str):
        self.username: str = data['username']
        self.uuid = _uuid
        self.avatar: str = avatar
        self.rankColor: int = int(str(data['legacyRankColour']['main']).replace("#", "0x"), base=16)
        self.rankIcon: str = f"https://cdn.wynncraft.com/{data['rankBadge']}"
        self.rank: str = str(data['supportRank']).replace("plus", "+").upper()
        self.firstJoin: str = data['firstJoin'][:10]
        self.lastJoin: str = data['lastJoin'][:10]
        self.online: bool = bool(data['online'])
        self.server: str | None = data['server']
        # self.activeCharacter = data['activeCharacter']
        self.playtime: float = float(data['playtime'])

    def get_embed(self) -> Embed:
        embed = Embed(
            title=f"{f"[{self.rank}]" if self.rank else ""} {self.username}'s info",
            color=self.rankColor
        )

        # embed.set_image(url=data['rank_icon']) discord doesn't support svg preview
        embed.set_thumbnail(url=self.avatar)
        embed.add_field(name="First joined", value=self.firstJoin, inline=True)
        embed.add_field(name="Last joined", value=self.lastJoin, inline=True)
        embed.add_field(name="Current status",
                        value=f"Online on {self.server}" if self.online else "Offline", inline=False)
        embed.add_field(name="Hours played", value=f"{self.playtime}", inline=False)

        return embed
