"""main program module"""

import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
from music_cog import Music
from help_cog import Help

bot = commands.Bot(command_prefix="+", intents=discord.Intents.all())

# with open("token.txt", "r", encoding="utf-8") as file:
#     TOKEN = file.readlines()[0]
load_dotenv(find_dotenv())


async def main():
    """Delete help command, add cogs and launch bot"""
    async with bot:
        bot.remove_command("help")
        await bot.add_cog(Music(bot))
        await bot.add_cog(Help(bot))
        await bot.start(os.getenv("TOKEN"))


asyncio.run(main())
