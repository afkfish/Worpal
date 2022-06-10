import json
from nextcord.ext import commands

bot = commands.Bot()
bot.remove_command('help')

with open("secrets.json", "r") as file:
    application_key = json.load(file)["discord"]["app_key"]

modules = [
    'play',
    'navigation',
    'seek',
    'settings',
    'help'
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
        if guild.id not in data:
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


@bot.slash_command(description="Load cogs",
                   guild_ids=[940575531567546369])
async def load(ctx, cog_):
    await ctx.send('Bot is thinking!')
    try:
        bot.load_extension(f'cogs.{cog_}')
        await ctx.edit_original_message(content="Succefully loaded {}".format(cog_))
    except Exception as ex:
        print(f'Failed to load mod {cog_}\n{type(ex).__name__}: {ex}')
        await ctx.edit_original_message(content=f"Loading {cog_} was unsuccesful"
                                                f"\nError: {cog_}\n{type(ex).__name__}: {ex}")


@bot.slash_command(description="Unload cogs",
                   guild_ids=[940575531567546369])
async def unload(ctx, cog_):
    await ctx.send('Bot is thinking!')
    try:
        bot.unload_extension(f'cogs.{cog_}')
        await ctx.edit_original_message(content=f"Succefully unloaded {cog_}")
    except Exception as ex:
        print(f'Failed to unload mod {cog_}\n{type(ex).__name__}: {ex}')
        await ctx.edit_original_message(content=f"Unloading {cog_} was unsuccesful"
                                                f"\nError: {cog_}\n{type(ex).__name__}: {ex}")


@bot.slash_command(description="Reload cogs",
                   guild_ids=[940575531567546369])
async def reload(ctx, cog_):
    await ctx.send('Bot is thinking!')
    try:
        bot.unload_extension(f'cogs.{cog_}')
        bot.load_extension(f'cogs.{cog_}')
        await ctx.edit_original_message(content=f"Succefully reloaded {cog_}")
    except Exception as ex:
        print(f'Failed to reload mod {cog_}\n{type(ex).__name__}: {ex}')
        await ctx.edit_original_message(content=f"Reloading {cog_} was unsuccesful"
                                                f"\nError: {cog_}\n{type(ex).__name__}: {ex}")


@bot.slash_command(description="Latency test", guild_ids=[940575531567546369])
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")


for cog in modules:
    try:
        bot.load_extension(f"cogs.{cog}")
    except Exception as e:
        print(f"Failed to load cog {cog}: {type(e).__name__}, {e}")

bot.run(application_key)
