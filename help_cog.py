"""Module help options"""

import discord
from discord.ext import commands


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.embed_color = 0x290000

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     """Ready status"""
    #     send_to_channels = []
    #     for guild in self.bot.guilds:
    #         channel = guild.text_channels[0]
    #         send_to_channels.append(channel)
    #     hello_embed = discord.Embed(
    #         title = "Здарова бандиты!",
    #         description = f"""Я 8™_Бот, для проигрывания музыки с Youtube!
    #                         Мой префикс **`+`**, для использования команд.
    #                         Используйте **`+help`**, для получения списка команд.""",
    #         colour = self.embed_color
    #     )
    #     for channel in send_to_channels:
    #         await channel.send(embed = hello_embed)

    # help command +
    @commands.command(
        name="help",
        aliases=["h"],
        help="📜Предоставляет описание всех указанных команд.",
    )
    async def help(self, ctx):
        """Command create help"""
        help_cog = self.bot.get_cog("Help")
        music_cog = self.bot.get_cog("Music")
        commands_all = help_cog.get_commands() + music_cog.get_commands()
        command_description = ""

        for c in commands_all:
            command_description += f"**`+{c.name} или {c.aliases}`** - {c.help}\n"
        commands_embed = discord.Embed(
            title="Список команд для Бота",
            description=command_description,
            colour=self.embed_color,
        )
        await ctx.send(embed=commands_embed)
