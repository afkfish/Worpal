import asyncio
import json
import logging
import os

import discord
from discord import Guild, VoiceClient, Member, VoiceState
from discord.ext import commands

from structures.track import Track


class Worpal(commands.Bot):
    def __init__(self, initial_extensions: [str], testing_guild_id) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, command_prefix="§")
        self.initial_extensions = initial_extensions
        self.testing_guild_id = testing_guild_id
        self.remove_command('help')
        self.logger = logging.getLogger('Worpal')
        self.logger.setLevel(logging.INFO)
        self.music_queue: {int: [Track]} = {}
        self.playing: {int: Track} = {}
        self.mc_uuids = {}
        self.color = 0x0b9ebc
        self.icon = "https://i.imgur.com/Rygy2KWs.jpg"
        self.settings = {}
        with open('./settings/settings.json', 'r', encoding='UTF-8') as file:
            self.settings = json.load(file)

    async def setup_hook(self) -> None:

        # here, we are loading extensions prior to sync to ensure we are syncing interactions defined in those
        # extensions.

        for extension in self.initial_extensions:
            await self.load_extension(f"cogs.{extension}")

        # In overriding setup hook,
        # we can do things that require a bot prior to starting to process events from the websocket.
        # In this case, we are using this to ensure that once we are connected, we sync for the testing guild.
        # You should not do this for every guild or for global sync, those should only be synced when changes happen.
        if self.testing_guild_id:
            guild = discord.Object(self.testing_guild_id)
            # We'll copy in the global commands to test with:
            self.tree.copy_global_to(guild=guild)
            # followed by syncing to the testing guild.
            await self.tree.sync(guild=guild)

    async def on_ready(self):
        self.logger.info("Logged in as %s!", self.user)
        await self.tree.sync()

        for guild in self.guilds:
            if str(guild.id) not in self.settings:
                self.settings.update({
                    str(guild.id): {
                        'announce': False,
                        'shuffle': False,
                        'loop': False
                    }
                })
            self.music_queue[guild.id] = []
            self.playing[guild.id] = ''

    async def on_guid_join(self, guild: Guild):
        self.settings.update({str(guild.id): {'announce': False, 'shuffle': False, 'loop': False}})
        self.music_queue[guild.id] = []
        self.playing[guild.id] = ''

    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if before.channel:
            voice: VoiceClient = before.channel.guild.voice_client
            if voice and not after.channel:
                if before.channel.id == voice.channel.id:
                    if len(voice.channel.members) == 1:
                        self.music_queue[member.guild.id] = []
                        voice.stop()
                        await voice.disconnect(force=True)

    def shuffle(self, guildid) -> bool:
        return self.settings[str(guildid)]["shuffle"]

    def announce(self, guildid) -> bool:
        return self.settings[str(guildid)]['announce']

    def looping(self, guildid) -> bool:
        return self.settings[str(guildid)]['loop']

    def __del__(self):
        self.logger.info("Writing settings to file...")
        with open('./settings/settings.json', 'w', encoding="UTF-8") as file:
            json.dump(self.settings, file, indent=4)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    exts = [
        'play',
        'navigation',
        'settings',
        # 'help', too many redundant commands
        # 'search', TODO: fix search with api
        'wynncraft',
        'utils'
    ]

    await Worpal(exts, 940575531567546369).start(os.getenv('BOT_TOKEN'))


if __name__ == '__main__':
    asyncio.run(main())
