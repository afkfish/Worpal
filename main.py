import asyncio
import json
import logging
import os
import uuid

import discord
from discord import Guild, VoiceClient, Member, VoiceState, VoiceProtocol
from discord.ext import commands
from dotenv_vault import load_dotenv

from structures.playable import Track


class Worpal(commands.Bot):
    color = 0x0b9ebc
    icon = "https://i.imgur.com/Rygy2KWs.jpg"

    def __init__(self, initial_extensions: [str], testing_guild_id) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, command_prefix="§")
        self.initial_extensions = initial_extensions
        self.testing_guild_id = testing_guild_id
        self.remove_command('help')
        self.logger = logging.getLogger('Worpal')
        self.logger.setLevel(logging.INFO)
        self.music_queue: dict[int, list[Track]] = {}
        self.playing: dict[int, Track | None] = {}
        self.minecraft_uuid_cache: dict[str, uuid.UUID] = {}
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
            self.playing[guild.id] = None

    async def on_guid_join(self, guild: Guild):
        self.settings.update({str(guild.id): {'announce': False, 'shuffle': False, 'loop': False}})
        self.music_queue[guild.id] = []
        self.playing[guild.id] = None

    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if before.channel:
            voice: VoiceClient | VoiceProtocol = before.channel.guild.voice_client
            if voice and not after.channel:
                if before.channel.id == voice.channel.id:
                    if len(voice.channel.members) == 1:
                        self.music_queue[member.guild.id] = []
                        voice.stop()
                        await voice.disconnect(force=True)

    def shuffle(self, guild_id: int) -> bool:
        return self.settings[str(guild_id)]["shuffle"]

    def announce(self, guild_id: int) -> bool:
        return self.settings[str(guild_id)]['announce']

    def looping(self, guild_id: int) -> bool:
        return self.settings[str(guild_id)]['loop']

    def __del__(self):
        self.logger.info("Writing settings to file...")
        with open('./settings/settings.json', 'w', encoding="UTF-8") as file:
            json.dump(self.settings, file, indent=2)


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# def wc_schedule(bot: Worpal):
#     anon_embed = Wynncraft(bot).player_embed("Anon08")
#     anon_embed = anon_embed if anon_embed else Embed(title="oh no")
#     origin_embed = Wynncraft(bot).player_embed("Origin_VXS")
#     near_embed = Wynncraft(bot).player_embed("Near_End")
#     schedule.every().day.at("19:00").do(lambda: {
#         bot.loop.create_task(
#             bot.get_channel(940575531567546372)
#             .send(embeds=[anon_embed, origin_embed, near_embed])
#         )
#     })
#
#     while True:
#         schedule.run_pending()
#         time.sleep(1)


async def main() -> None:
    load_dotenv()

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(CustomFormatter())
    logging.basicConfig(
        format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO,
        handlers=[ch]
    )

    exts = [
        'play',
        'navigation',
        'image',
        'settings',
        'help',
        # 'search', TODO: fix search with api
        'wynncraft',
        'utils'
    ]
    bot = Worpal(exts, 940575531567546369)

    # scheduled_thread = Thread(target=wc_schedule, args=(bot,))
    # scheduled_thread.start()

    await bot.start(os.getenv('BOT_TOKEN'))


if __name__ == '__main__':
    asyncio.run(main())
