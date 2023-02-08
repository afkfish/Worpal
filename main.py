import json
import logging
import os

from nextcord import utils, Activity, ActivityType
from nextcord.ext import commands

from structures.worpal import Worpal


def main() -> None:
	logger = setup_logging()
	with open("secrets.json", "r") as file:
		secrets = json.load(file)
	worp = Worpal({}, {}, {}, {}, secrets)
	bot = setup_bot(logger)
	bot.worp = worp

	@bot.event
	async def on_ready():
		logger.info(f"Logged in as {bot.user}!")
		with open('./settings/settings.json', 'r') as f:
			data = json.load(f)
		for guild in bot.guilds:
			if str(guild.id) not in data:
				data.update({str(guild.id): {'announce': False, 'shuffle': False, 'loop': False}})
			worp.music_queue[guild.id] = []
			worp.query[guild.id] = []
			worp.playing[guild.id] = ''
		with open('./settings/settings.json', 'w') as f:
			json.dump(data, f, indent=4)

	@bot.event
	async def on_guid_join(guild):
		with open('./settings/settings.json', 'r') as f:
			data = json.load(f)
		data.update({str(guild.id): {'announce': False, 'shuffle': False, 'loop': False}})
		worp.music_queue[guild.id] = []
		worp.query[guild.id] = []
		worp.playing[guild.id] = ''
		with open('./settings/settings.json', 'w') as f:
			json.dump(data, f, indent=4)

	@bot.event
	async def on_voice_state_update(member, before, after):
		voice = utils.get(bot.voice_clients, guild=member.guild)
		if voice is not None and before.channel is not None:
			if before.channel.id == voice.channel.id:
				if len(voice.channel.members) == 1:
					bot.music_queue[member.guild.id] = []
					voice.stop()
					await voice.disconnect(force=True)

	@bot.slash_command(description="Latency test", guild_ids=[940575531567546369])
	async def ping(ctx):
		await ctx.followup.send(f"Pong! {round(bot.latency * 1000)}ms")

	bot.run(os.getenv('BOT_TOKEN'))


def setup_logging() -> logging.Logger:
	logger = logging.getLogger('Worpal')
	logger.setLevel(logging.INFO)
	logging.basicConfig(
		level=logging.INFO,
		format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S'
	)

	return logger


def setup_bot(logger: logging.Logger) -> commands.Bot:
	bot = commands.Bot(activity=Activity(name="/play", type=ActivityType.listening))
	bot.remove_command('help')

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
			bot.load_extension(f"cogs.{cog}")
		except Exception as e:
			logger.error(f"Failed to load cog {cog}: {type(e).__name__}, {e}")

	return bot


def bot_shuffle(guildid):
	with open('./settings/settings.json', 'r') as f:
		data = json.load(f)
	return bool(data[str(guildid)]['shuffle'])


def bot_announce(guildid):
	with open('./settings/settings.json', 'r') as f:
		data = json.load(f)
	return bool(data[str(guildid)]['announce'])


def bot_loop(guildid):
	with open('./settings/settings.json', 'r') as f:
		data = json.load(f)
	return bool(data[str(guildid)]['loop'])


if __name__ == '__main__':
	main()
