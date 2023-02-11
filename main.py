import json
import logging
import os

from nextcord import utils, Activity, ActivityType, slash_command, VoiceClient
from nextcord.ext import commands


class Worpal(commands.Bot):
	def __init__(self) -> None:
		super().__init__(activity=Activity(name="/play", type=ActivityType.listening))
		self.remove_command('help')
		self.logger = logger = logging.getLogger('Worpal')
		logger.setLevel(logging.INFO)
		self.music_queue = {}
		self.query = {}
		self.playing = {}
		self.mc_uuids = {}
		self.color = 0x0b9ebc
		self.icon = "https://i.imgur.com/Rygy2KWs.jpg"

	async def on_ready(self):
		self.logger.info(f"Logged in as {self.user}!")

		modules = [
			'play',
			'navigation',
			'seek',
			'settings',
			'help',
			# 'search', TODO: fix search with api
			'wynncraft'
		]

		for cog in modules:
			try:
				self.load_extension(f"cogs.{cog}")
			except Exception as e:
				self.logger.error(f"Failed to load cog {cog}: {type(e).__name__}, {e}")

		with open('./settings/settings.json', 'r') as f:
			data = json.load(f)
		for guild in self.guilds:
			if str(guild.id) not in data:
				data.update({str(guild.id): {'announce': False, 'shuffle': False, 'loop': False}})
			self.music_queue[guild.id] = []
			self.query[guild.id] = []
			self.playing[guild.id] = ''
		with open('./settings/settings.json', 'w') as f:
			json.dump(data, f, indent=4)

	async def on_guid_join(self, guild):
		with open('./settings/settings.json', 'r') as f:
			data = json.load(f)
		data.update({str(guild.id): {'announce': False, 'shuffle': False, 'loop': False}})
		self.music_queue[guild.id] = []
		self.query[guild.id] = []
		self.playing[guild.id] = ''
		with open('./settings/settings.json', 'w') as f:
			json.dump(data, f, indent=4)

	async def on_voice_state_update(self, member, before, after):
		voice: VoiceClient = utils.get(self.voice_clients, guild=member.guild)
		if voice is not None and before.channel is not None:
			if before.channel.id == voice.channel.id:
				if len(voice.channel.members) == 1:
					self.music_queue[member.guild.id] = []
					voice.stop()
					await voice.disconnect(force=True)

	@staticmethod
	def shuffle(guildid):
		with open('./settings/settings.json', 'r') as f:
			data = json.load(f)
		return bool(data[str(guildid)]['shuffle'])

	@staticmethod
	def announce(guildid):
		with open('./settings/settings.json', 'r') as f:
			data = json.load(f)
		return bool(data[str(guildid)]['announce'])

	@staticmethod
	def looping(guildid):
		with open('./settings/settings.json', 'r') as f:
			data = json.load(f)
		return bool(data[str(guildid)]['loop'])

	@slash_command(description="Latency test", guild_ids=[940575531567546369])
	async def ping(self, ctx):
		await ctx.followup.send(f"Pong! {round(self.latency * 1000)}ms")


def main() -> None:
	logging.basicConfig(
		level=logging.INFO,
		format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S'
	)
	worpal = Worpal()
	worpal.run(os.getenv('BOT_TOKEN'))


if __name__ == '__main__':
	main()
