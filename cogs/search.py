import datetime as dt

from nextcord import slash_command, SlashOption, Embed, utils, ui, ButtonStyle
from nextcord.ext import commands

import main
from cogs.play import Play
from utils.song_info import search_yt


class Selector(ui.View):
	def __init__(self):
		super().__init__()
		self.value = None

	@ui.button(label="1", style=ButtonStyle.grey)
	async def first(self, button: ui.Button, ctx):
		self.value = 1
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		self.stop()

	@ui.button(label="2", style=ButtonStyle.grey)
	async def second(self, button: ui.Button, ctx):
		self.value = 2
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		self.stop()

	@ui.button(label="3", style=ButtonStyle.grey)
	async def third(self, button: ui.Button, ctx):
		self.value = 3
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		self.stop()

	@ui.button(label="4", style=ButtonStyle.grey)
	async def fourth(self, button: ui.Button, ctx):
		self.value = 4
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		self.stop()

	@ui.button(label="5", style=ButtonStyle.grey)
	async def fifth(self, button: ui.Button, ctx):
		self.value = 5
		button.style = ButtonStyle.green
		await ctx.response.edit_message(view=self)
		self.stop()


class Search(commands.Cog):
	def __int__(self, bot):
		self.bot = bot

	@slash_command(name="search",
				   description="Search for a song on youtube.",
				   guild_ids=main.bot.guild_ids)
	async def search_(self, ctx, q: str = SlashOption(name="title",
													  description="The video to be found.",
													  required=True)):
		await ctx.response.defer()
		songs = search_yt(q, True)
		if songs:
			view = Selector()
			embed = Embed(title=f"Search results for {q}", color=0x152875)
			embed.set_author(name="Worpal", icon_url=main.icon)
			cropped = [{'source': song['formats'][0]['url'], 'title': song['title'], 'thumbnail': song['thumbnail'],
						'duration': song['duration']} for song in songs]
			a = ""
			i = 0
			for i, entry in enumerate(cropped, i):
				a += f"{i + 1}. {entry['title']}\n\n"
			embed.add_field(name="Results:", value=a)
			await ctx.followup.send(embed=embed, view=view)
			await view.wait()
			if ctx.user.voice:
				voice_channel = ctx.user.voice.channel
				if view.value is not None:
					main.bot.music_queue[ctx.guild.id].append([cropped[view.value-1], voice_channel])
					embed = Embed(title="Song added from search", color=0x152875)
					embed.set_thumbnail(url=main.bot.music_queue[ctx.guild.id][-1][0]['thumbnail'])
					embed.add_field(name=main.bot.music_queue[ctx.guild.id][-1][0]['title'],
									value=str(dt.timedelta(
										seconds=int(main.bot.music_queue[ctx.guild.id][-1][0]['duration']))),
									inline=True)
					embed.set_footer(text="Song requested by: " + ctx.user.name)
					await ctx.send(embed=embed)
					await Play(commands.Cog).play_music(ctx)

			else:
				await ctx.send(content="Connect to a voice channel!", ephemeral=True)

		else:
			await ctx.followup.send(content="Error in getting the videos!")


def setup(bot):
	bot.add_cog(Search(bot))
