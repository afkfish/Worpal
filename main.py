import json

from nextcord import utils
from nextcord.ext import commands

bot = commands.Bot()
bot.remove_command('help')
icon = "https://i.imgur.com/Rygy2KWs.jpg"

with open("secrets.json", "r") as file:
    application_key = json.load(file)["discord"]["app_key"]

modules = [
    'play',
    'navigation',
    'seek',
    'settings',
    'help',
    'search'
]


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


bot.playing = {}
bot.music_queue = {}
bot.query = {}
bot.guild_ids = []


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    with open('./settings/settings.json', 'r') as f:
        data = json.load(f)
    for guild in bot.guilds:
        if str(guild.id) not in data:
            data.update({str(guild.id): {'announce': False, 'shuffle': False, 'loop': False}})
        bot.guild_ids.append(guild.id)
        bot.music_queue[guild.id] = []
        bot.query[guild.id] = []
        bot.playing[guild.id] = ''
    with open('./settings/settings.json', 'w') as f:
        json.dump(data, f, indent=4)


@bot.event
async def on_guid_join(guild):
    with open('./settings/settings.json', 'r') as f:
        data = json.load(f)
    data.update({str(guild.id): {'announce': False, 'shuffle': False, 'loop': False}})
    bot.guild_ids.append(guild.id)
    bot.music_queue[guild.id] = []
    bot.query[guild.id] = []
    bot.playing[guild.id] = ''
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
                await voice.disconnect()


@bot.slash_command(description="Load cogs",
                   guild_ids=[940575531567546369])
async def load(ctx, cog_):
    await ctx.response.defer()
    try:
        bot.load_extension(f'cogs.{cog_}')
        await ctx.followup.send(content="Succefully loaded {}".format(cog_))
    except Exception as ex:
        print(f'Failed to load cog {cog_}\n{type(ex).__name__}: {ex}')
        await ctx.followup.send(content=f"Loading {cog_} was unsuccesful"
                                                f"\nError: {cog_}\n{type(ex).__name__}: {ex}")


@bot.slash_command(description="Unload cogs",
                   guild_ids=[940575531567546369])
async def unload(ctx, cog_):
    await ctx.response.defer()
    try:
        bot.unload_extension(f'cogs.{cog_}')
        await ctx.followup.send(content=f"Succefully unloaded {cog_}")
    except Exception as ex:
        print(f'Failed to unload cog {cog_}\n{type(ex).__name__}: {ex}')
        await ctx.followup.send(content=f"Unloading {cog_} was unsuccesful"
                                                f"\nError: {cog_}\n{type(ex).__name__}: {ex}")


@bot.slash_command(description="Reload cogs",
                   guild_ids=[940575531567546369])
async def reload(ctx, cog_):
    await ctx.response.defer()
    try:
        bot.unload_extension(f'cogs.{cog_}')
        bot.load_extension(f'cogs.{cog_}')
        await ctx.followup.send(content=f"Succefully reloaded {cog_}")
    except Exception as ex:
        print(f'Failed to reload cog {cog_}\n{type(ex).__name__}: {ex}')
        await ctx.followup.send(content=f"Reloading {cog_} was unsuccesful"
                                                f"\nError: {cog_}\n{type(ex).__name__}: {ex}")


@bot.slash_command(description="Latency test", guild_ids=[940575531567546369])
async def ping(ctx):
    await ctx.followup.send(f"Pong! {round(bot.latency * 1000)}ms")


for cog in modules:
    try:
        bot.load_extension(f"cogs.{cog}")
    except Exception as e:
        print(f"Failed to load cog {cog}: {type(e).__name__}, {e}")

bot.run(application_key)
