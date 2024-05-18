"""Module music options"""

import re
import json
import datetime
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import discord
from discord.ext import commands
from youtube_dl import YoutubeDL


class Music(commands.Cog):
    """Class representing play music"""

    def __init__(self, bot):
        self.bot = bot

        self.is_playing = {}
        self.is_paused = {}
        self.music_queue = {}
        self.queue_index = {}

        self.YTDL_OPTIONS = {"format": "bestaudio", "nonplaylist": "True"}
        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }

        self.embed_color = 0x290000

        self.vc = {}

    # FUNCTIONS
    @commands.Cog.listener()
    async def on_ready(self):
        """Initializes starting parameters"""
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.music_queue[id] = []
            self.queue_index[id] = 0
            self.vc[id] = None
            self.is_paused[id] = self.is_playing[id] = False
            print(f"Бот 8™ АКТИВИРОВАН !!! на: {guild}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Bot leave if all leave"""
        id = int(member.guild.id)
        if (
            member.id != self.bot.user.id
            and before.channel is not None
            and after.channel != before.channel
        ):
            remaining_channel_members = before.channel.members
            if (
                len(remaining_channel_members) == 1
                and remaining_channel_members[0].id == self.bot.user.id
            ):
                self.is_playing[id] = self.is_paused[id] = False
                self.music_queue[id] = []
                self.queue_index[id] = 0
                self.vc[id] = discord.utils.get(
                    self.bot.voice_clients, guild=member.guild
                )
                await self.vc[id].disconnect()
                self.vc[id] = None

    def now_playing_embed(self, ctx, song):
        """Now playing"""
        TITLE = song["title"]
        LINK = song["link"]
        THUMBNAIL = song["thumbnail"]
        DURATION = str(datetime.timedelta(seconds=song["duration"]))
        AUTHOR = ctx.author
        AVATAR = AUTHOR.avatar

        embed = discord.Embed(
            title="▶️ Сейчас играет:",
            description=f"[{TITLE}]({LINK})\nДлительность {DURATION}",
            colour=self.embed_color,
        )
        embed.set_thumbnail(url=THUMBNAIL)
        embed.set_footer(text=f"Добавил: {str(AUTHOR)}", icon_url=AVATAR)
        return embed

    def now_playing_repeat_embed(self, ctx, song):
        """Now playing for repeat"""
        TITLE = song["title"]
        LINK = song["link"]
        THUMBNAIL = song["thumbnail"]
        DURATION = str(datetime.timedelta(seconds=song["duration"]))
        AUTHOR = ctx.author
        AVATAR = AUTHOR.avatar

        embed = discord.Embed(
            title="▶️Сейчас играет на 🔁РЕПИТЕ ! ! !",
            description=f"[{TITLE}]({LINK})\nДлительность {DURATION}",
            colour=self.embed_color,
        )
        embed.set_thumbnail(url=THUMBNAIL)
        embed.set_footer(text=f"Добавил: {str(AUTHOR)}", icon_url=AVATAR)
        return embed

    def added_song_embed(self, ctx, song):
        """Added song in queue"""
        TITLE = song["title"]
        LINK = song["link"]
        THUMBNAIL = song["thumbnail"]
        AUTHOR = ctx.author
        AVATAR = AUTHOR.avatar

        embed = discord.Embed(
            title="Добавлено в очередь:",
            description=f"[{TITLE}]({LINK})",
            colour=self.embed_color,
        )
        embed.set_thumbnail(url=THUMBNAIL)
        embed.set_footer(text=f"Добавил: {str(AUTHOR)}", icon_url=AVATAR)
        return embed

    def removed_song_embed(self, ctx, song):
        """Remove song in queue"""
        TITLE = song["title"]
        LINK = song["link"]
        THUMBNAIL = song["thumbnail"]
        AUTHOR = ctx.author
        AVATAR = AUTHOR.avatar

        embed = discord.Embed(
            title="Удалена из очереди:",
            description=f"[{TITLE}]({LINK})",
            colour=self.embed_color,
        )
        embed.set_thumbnail(url=THUMBNAIL)
        embed.set_footer(text=f"Песню удалил: {str(AUTHOR )}", icon_url=AVATAR)
        return embed

    async def join_vc(self, ctx, channel):
        """Join bot to channel"""
        id = int(ctx.guild.id)
        if self.vc[id] is None or not self.vc[id].is_connected():
            self.vc[id] = await channel.connect()
            if self.vc[id] is None:
                await ctx.send("НЕ удалось подключится к голосовому каналу!")
                return
        else:
            await self.vc[id].move_to(channel)

    def get_yt_title(self, video_id):
        """Extract title"""
        params = {
            "format": "json",
            "url": "https://www.youtube.com/watch?v=%s" % video_id,
        }
        url = "https://www.youtube.com/oemed"
        query_string = parse.urlencode(params)
        url = url + "?" + query_string
        with request.urlopen(url) as response:
            response_text = response.read()
            data = json.loads(response_text.decode())
            return data["title"]

    def search_yt(self, search):
        """Search in Youtube"""
        query_string = parse.urlencode({"search_query": search})
        with request.urlopen(
            "https://www.youtube.com/results?" + query_string
        ) as htm_content:
            search_results = re.findall(
                r"/watch\?v=(.{11})", htm_content.read().decode()
            )
            return search_results[0:10]

    def extract_yt(self, url):
        """Extract info"""
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except:
                return False
        return {
            "link": "https://www.youtube.com/watch?v=" + url,
            "thumbnail": "https://i.ytimg.com/vi/"
            + url
            + "/hqdefault.jpg?sqp=-oaymwEcCOADEI4CSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLD5uL4xKN-IUfez6KIW_j5y70mlig",
            "source": info["formats"][0]["url"],
            "title": info["title"],
            "duration": info["duration"],
        }

    def play_next(self, ctx):
        """Play next song"""
        id = int(ctx.guild.id)
        if not self.is_playing[id]:
            return
        if self.queue_index[id] + 1 < len(self.music_queue[id]):
            self.is_playing[id] = True
            self.queue_index[id] += 1

            song = self.music_queue[id][self.queue_index[id]][0]
            message = self.now_playing_embed(ctx, song)
            coroutine = ctx.send(embed=message)
            fut = run_coroutine_threadsafe(coroutine, self.bot.loop)
            try:
                fut.result()
            except:
                pass

            self.vc[id].play(
                discord.FFmpegPCMAudio(song["source"], **self.FFMPEG_OPTIONS),
                after=lambda e: self.play_next(ctx),
            )
        else:
            coroutine = ctx.send("🏁 Вы достигли конца очереди!")
            fut = run_coroutine_threadsafe(coroutine, self.bot.loop)
            try:
                fut.result()
            except:
                pass
            self.queue_index[id] += 1
            self.is_playing[id] = False

    def play_next_repeat(self, ctx):
        """Play next repeat song"""
        id = int(ctx.guild.id)
        if not self.is_playing[id]:
            return
        if len(self.music_queue[id]) == 1:
            self.is_playing[id] = True
            song = self.music_queue[id][self.queue_index[id]][0]
            self.vc[id].play(
                discord.FFmpegPCMAudio(song["source"], **self.FFMPEG_OPTIONS),
                after=lambda e: self.play_next_repeat(ctx),
            )

        elif len(self.music_queue[id]) > 1 and self.queue_index[id] + 1 < len(
            self.music_queue[id]
        ):
            self.is_playing[id] = True
            self.queue_index[id] += 1

            song = self.music_queue[id][self.queue_index[id]][0]

            self.vc[id].play(
                discord.FFmpegPCMAudio(song["source"], **self.FFMPEG_OPTIONS),
                after=lambda e: self.play_next_repeat(ctx),
            )

        elif (
            len(self.music_queue[id]) > 1
            and self.queue_index[id] == len(self.music_queue[id]) - 1
        ):
            self.is_playing[id] = True
            self.queue_index[id] = 0

            song = self.music_queue[id][self.queue_index[id]][0]

            self.vc[id].play(
                discord.FFmpegPCMAudio(song["source"], **self.FFMPEG_OPTIONS),
                after=lambda e: self.play_next_repeat(ctx),
            )

    async def play_music(self, ctx):
        """Play music"""
        id = int(ctx.guild.id)
        if self.queue_index[id] < len(self.music_queue[id]):
            self.is_playing[id] = True
            self.is_paused[id] = False
            self.vc[id] = await self.join_vc(
                ctx, self.music_queue[id][self.queue_index[id]][1]
            )
            song = self.music_queue[id][self.queue_index[id]][0]
            message = self.now_playing_embed(ctx, song)
            await ctx.send(embed=message)

            self.vc[id] = ctx.guild.voice_client

            self.vc[id].play(
                discord.FFmpegPCMAudio(song["source"], **self.FFMPEG_OPTIONS),
                after=lambda e: self.play_next(ctx),
            )

        else:
            await ctx.send("В очереди на воспроизведение нет песен!")
            self.queue_index[id] += 1
            self.is_playing[id] = False

    async def play_music_repeat(self, ctx):
        """Play music repeat"""
        id = int(ctx.guild.id)
        if self.queue_index[id] < len(self.music_queue[id]):
            self.is_playing[id] = True
            self.is_paused[id] = False
            self.vc[id] = await self.join_vc(
                ctx, self.music_queue[id][self.queue_index[id]][1]
            )
            song = self.music_queue[id][self.queue_index[id]][0]
            message = self.now_playing_repeat_embed(ctx, song)
            await ctx.send(embed=message)

            self.vc[id] = ctx.guild.voice_client

            self.vc[id].play(
                discord.FFmpegPCMAudio(song["source"], **self.FFMPEG_OPTIONS),
                after=lambda e: self.play_next_repeat(ctx),
            )

        else:
            await ctx.send("В очереди на воспроизведение нет песен!")
            self.queue_index[id] += 1
            self.is_playing[id] = False

    # COMMANDS
    @commands.command(
        name="play", aliases=["pl"], help="▶️Воспроизводит (или возобновляет) песню."
    )
    async def play(self, ctx, *args):
        """Play/resume command"""
        search = " ".join(args)
        id = int(ctx.guild.id)
        try:
            user_channel = ctx.author.voice.channel
        except:
            await ctx.send("Вам нужно находиться в голосовом канале!")
            return
        if not args:
            if len(self.music_queue[id]) == 0:
                await ctx.send("В очереди на воспроизведение нет песен!")
                return
            if not self.is_playing[id] and not self.is_paused[id]:
                if self.music_queue[id] is None or self.vc[id] is None:
                    await self.play_music(ctx)
                else:
                    self.is_paused[id] = False
                    self.is_playing[id] = True
                    await self.play_music(ctx)
            elif not self.is_playing[id] and self.is_paused[id]:
                self.is_playing[id] = True
                self.is_paused[id] = False
                self.vc[id].resume()
                await ctx.send("▶️ Возобновлено")
            else:
                return
        else:
            song = self.extract_yt(self.search_yt(search)[0])
            if isinstance(song, bool):
                await ctx.send("НЕ нашел! Попробуйте другую фразу для поиска.")
            else:
                self.music_queue[id].append([song, user_channel])
                if not self.is_playing[id]:
                    await self.play_music(ctx)
                else:
                    message = self.added_song_embed(ctx, song)
                    await ctx.send(embed=message)

    @commands.command(
        name="add", aliases=["a"], help="Добавляет первый результат поиска в очередь."
    )
    async def add(self, ctx, *args):
        """Add song command"""
        search = " ".join(args)
        try:
            user_channel = ctx.author.voice.channel
        except:
            await ctx.send("Вы должны находиться в голосовом канале")
            return
        if not args:
            await ctx.send("Укажите песню, которую нужно добавить в очередь")
        else:
            song = self.extract_yt(self.search_yt(search)[0])
            if isinstance(song, bool):
                await ctx.send("НЕ нашел! Попробуйте другую фразу для поиска.")
                return
            else:
                self.music_queue[ctx.guild.id].append([song, user_channel])
                message = self.added_song_embed(ctx, song)
                await ctx.send(embed=message)

    @commands.command(
        name="remove", aliases=["rm"], help="Удаляет последнюю песню в очереди."
    )
    async def remove(self, ctx):
        """Remove song to queue command"""
        id = int(ctx.guild.id)
        if self.music_queue[id] != []:
            song = self.music_queue[id][-1][0]
            remove_song_embed = self.removed_song_embed(ctx, song)
            await ctx.send(embed=remove_song_embed)
        else:
            await ctx.send("В очереди на воспроизведение нет песен!")
        self.music_queue[id] = self.music_queue[id][:-1]
        if self.music_queue[id] == []:
            if self.vc[id] is not None and self.is_playing[id]:
                self.is_playing[id] = self.is_paused[id] = False
                await self.vc[id].disconnect()
                self.vc[id] = None
            self.queue_index[id] = 0
        elif (
            self.queue_index[id] == len(self.music_queue[id])
            and self.vc[id] is not None
            and self.vc[id]
        ):
            self.vc[id].pause()
            self.queue_index[id] -= 1
            await self.play_music(ctx)

    # =========================================================================================
    # @commands.command(
    #     name="search",
    #     aliases=["find", "sr"],
    #     help="Предоставляет список результатов поиска YouTube.",
    # )
    # async def search(self, ctx, *args):
    #     """Search song command"""
    #     search = "".join(args)
    #     songNames = []
    #     selectionOptions = []
    #     embedText = ""
    #     if not args:
    #         await ctx.send("Укажите условия поиска")
    #         return
    #     try:
    #         user_channel = ctx.author.voice.channel
    #     except:
    #         await ctx.send("Вы должны находиться в голосовом канале")
    #         return
    #     await ctx.send("Получение результатов поиска . . .")
    #     songTokens = self.search_yt(search)
    #     for i, token in enumerate(songTokens):
    #         url = "https://www.youtube.com/watch?v=" + token
    #         name = self.get_yt_title(token)
    #         songNames.append(name)
    #         embedText += f"{i+1} - [{name}]({url})\n"
    #     for i, title in enumerate(songNames):
    #         selectionOptions.append(
    #             SelectOption(label=f"{i+1} - {title[:95]}", value=i)
    #         )
    #     search_results = discord.Embed(
    #         title="Результаты поиска",
    #         description=embedText,
    #         colour=self.embed_color,
    #     )
    #     selectionComponents = [
    #         Select(placeholder="Опции выбора", options=selectionOptions),
    #         Button(label="Отменить", custom_id="Отменить", style=4),
    #     ]
    #     message = await ctx.send(embed=search_results, components=selectionComponents)
    #     try:
    #         tasks = [
    #             asyncio.create_task(
    #                 self.bot.wait_for("button_click", timeout=60.0, check=None),
    #                 name="button",
    #             ),
    #             asyncio.create_task(
    #                 self.bot.wait_for("select_option", timeout=60.0, check=None),
    #                 name="select",
    #             ),
    #         ]
    #         done, pending = await asyncio.wait(
    #             tasks, return_when=asyncio.FIRST_COMPLETED
    #         )
    #         finished = list(done)[0]
    #         for task in pending:
    #             try:
    #                 task.cancel()
    #             except asyncio.CancelledError:
    #                 pass
    #         if finished is None:
    #             search_results.title = "НЕ найдено"
    #             search_results.description = ""
    #             await message.delete()
    #             await ctx.send(embed=search_results)
    #             return
    #         action = finished.get_name()
    #         if action == "button":
    #             search_results.title = "НЕ найдено"
    #             search_results.description = ""
    #             await message.delete()
    #             await ctx.send(embed=search_results)
    #         elif action == "select":
    #             result = finished.result()
    #             chosenIndex = int(result.values[0])
    #             songRef = self.extract_yt(songTokens[chosenIndex])
    #             if isinstance(songRef, bool):
    #                 await ctx.send(
    #                     "НЕверный формат! Попробуйте другую фразу для поиска."
    #                 )
    #                 return
    #             embed_response = discord.Embed(
    #                 title=f"Опция #{chosenIndex + 1} выбрана",
    #                 description=f"[{songRef['title']}]({songRef['link']}) добавлены вочередь!",
    #                 colour=self.embed_color,
    #             )
    #             s.set_thumbnail(url=songRef["thumbnail"])
    #             await message.delete()
    #             await ctx.send(embed=s)
    #             self.music_queue[ctx.guild.id].append([songRef, user_channel])
    #     except:
    #         search_results.title = "НЕ найдено"
    #         search_results.description = ""
    #         await message.delete()
    #         await ctx.send(embed=search_results)
    # =========================================================================================
    @commands.command(
        name="resume", aliases=["re"], help="⏯️Возобновляет приостановленную песню."
    )
    async def resume(self, ctx):
        """Resume song command"""
        id = int(ctx.guild.id)
        if not self.vc[id]:
            await ctx.send("Нет музыки на паузе")
        elif self.is_paused[id]:
            self.is_playing[id] = True
            self.is_paused[id] = False
            self.vc[id].resume()
            await ctx.send("⏯️Воспроизведение продолжено.")

    @commands.command(
        name="repeat",
        aliases=["rpt", "rp"],
        help="▶️🔁Включает репит мод на всю очередь.",
    )
    async def repeat(self, ctx, *args):
        """Repeat mod command"""
        search = " ".join(args)
        id = int(ctx.guild.id)
        try:
            user_channel = ctx.author.voice.channel
        except:
            await ctx.send("Вам нужно находиться в голосовом канале!")
            return
        if not args:
            if len(self.music_queue[id]) == 0:
                await ctx.send("В очереди на воспроизведение нет песен!")
                return
            elif not self.is_playing[id] and not self.is_paused[id]:
                if self.music_queue[id] is None or self.vc[id] is None:
                    await self.play_music_repeat(ctx)
                else:
                    self.is_paused[id] = False
                    self.is_playing[id] = True
                    await self.play_music_repeat(ctx)
            # elif not self.is_playing[id] and self.is_paused[id]:
            #     self.is_playing[id] = True
            #     self.is_paused[id] = False
            #     self.vc[id].resume()
            #     await ctx.send("▶️ Возобновлено")
            else:
                return
        else:
            song = self.extract_yt(self.search_yt(search)[0])
            if isinstance(song, bool):
                await ctx.send("НЕ нашел! Попробуйте другую фразу для поиска.")
            else:
                self.music_queue[id].append([song, user_channel])
                if not self.is_playing[id]:
                    await self.play_music_repeat(ctx)

    @commands.command(
        name="pause", aliases=["stop", "pa"], help="⏸️Приостанавливает воспроизведение."
    )
    async def pause(self, ctx):
        """Pause song command"""
        id = int(ctx.guild.id)
        if not self.vc[id]:
            await ctx.send("Я не в канале!")
        else:
            if not self.is_playing[id]:
                await ctx.send("Нечего паузить!")
            elif self.is_playing[id]:
                self.is_playing[id] = False
                self.is_paused[id] = True
                self.vc[id].pause()
                await ctx.send("⏸️Воспроизведение приостановлено.")

    @commands.command(
        name="previous", aliases=["pre", "pr"], help="⏮️Воспроизводит предыдущую песню."
    )
    async def previous(self, ctx):
        """Previous song command"""
        id = int(ctx.guild.id)
        self.vc[id] = ctx.guild.voice_client
        if self.vc[id] is None:
            await ctx.send("Вам нужно находиться в голосовом канале!")
        elif self.queue_index[id] <= 0:
            await ctx.send("В очереди нет предыдущей песни!")
            self.vc[id].pause()
            await self.play_music(ctx)
        elif self.vc[id] is not None and self.vc[id]:
            self.vc[id].pause()
            self.queue_index[id] -= 1
            await self.play_music(ctx)

    @commands.command(
        name="skip", aliases=["sk"], help="⏭️Воспроизводит следующую песню."
    )
    async def skip(self, ctx):
        """Skip song command"""
        id = int(ctx.guild.id)
        self.vc[id] = ctx.guild.voice_client
        if self.vc[id] is None:
            await ctx.send("Вам нужно находиться в голосовом канале!")
        elif self.queue_index[id] >= len(self.music_queue[id]) - 1:
            await ctx.send("В очереди нет следующей песни!")
            self.vc[id].pause()
            await self.play_music(ctx)
        elif self.vc[id] is not None and self.vc[id]:
            self.vc[id].pause()
            self.queue_index[id] += 1
            await self.play_music(ctx)

    @commands.command(
        name="queue",
        aliases=["list", "q"],
        help="Показывает несколько песен в очереди.",
    )
    async def queue(self, ctx):
        """Show queue command"""
        id = int(ctx.guild.id)
        return_value = ""
        if self.music_queue[id] == []:
            await ctx.send("В очереди на воспроизведение нет песен!")
            return

        if len(self.music_queue[id]) <= self.queue_index[id]:
            await ctx.send("🏁 Вы достигли конца очереди!")
            return

        for i in range(self.queue_index[id], len(self.music_queue[id])):
            up_next_songs = len(self.music_queue[id]) - self.queue_index[id]
            if i > 5 + up_next_songs:
                break
            return_index = i - self.queue_index[id]
            if return_index == 0:
                return_index = "▶️ Сейчас играет"
            elif return_index == 1:
                return_index = "⏭️ Следующая"
            return_value += f"{return_index} - [{self.music_queue[id][i][0]['title']}]({self.music_queue[id][i][0]['link']})\n"

            if return_value == "":
                await ctx.send("В очереди на воспроизведение нет песен!")
                return
        queue = discord.Embed(
            title="Песни в очереди", description=return_value, colour=self.embed_color
        )
        await ctx.send(embed=queue)

    @commands.command(
        name="clear", aliases=["cl"], help="Удаляет ВСЕ песни из очереди."
    )
    async def clear(self, ctx):
        """Clear queue command"""
        id = int(ctx.guild.id)
        if self.vc[id] is not None and self.is_playing[id]:
            self.is_playing[id] = self.is_paused[id] = False
            self.vc[id].stop()
        if self.music_queue[id] != []:
            await ctx.send("Список воспроизведения ОЧИЩЕН")
            self.music_queue[id] = []
        self.queue_index[id] = 0

    @commands.command(name="join", aliases=["j"], help="Подключает Бота в канал.")
    async def join(self, ctx):
        """Join Bot to channel command"""
        if ctx.author.voice:
            user_channel = ctx.author.voice.channel
            await self.join_vc(ctx, user_channel)
            await ctx.send(f"8™_Бот вошел в канал: {user_channel}")
        else:
            await ctx.send("Вам нужно находиться в голосовом канале!")

    @commands.command(
        name="leave", aliases=["l"], help="Отключает Бота от канала и очищает очередь."
    )
    async def leave(self, ctx):
        """Leave Bot to channel command"""
        id = int(ctx.guild.id)
        self.is_playing[id] = self.is_paused[id] = False
        self.music_queue[id] = []
        self.queue_index[id] = 0
        self.vc[id] = ctx.guild.voice_client
        if self.vc[id] is not None:
            await self.vc[id].disconnect()
            await ctx.send("8™_Бот покинул голосовой канал!")
            self.vc[id] = None
