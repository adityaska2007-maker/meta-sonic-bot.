import discord
from discord.ext import commands
import asyncio
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

YTDL_OPTS = {"format": "bestaudio/best", "noplaylist": True, "quiet": True}
FFMPEG_OPTS = {"options": "-vn"}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if "entries" in data:
            data = data["entries"][0]
        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTS), data=data)

class Music(commands.Cog):
    """Music with Spotify + YouTube support."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
        ))

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
            await ctx.send(f"✅ Joined {ctx.author.voice.channel}")
        else:
            await ctx.reply("❌ You must be in a voice channel.", mention_author=False)

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Disconnected.")
        else:
            await ctx.reply("❌ I'm not connected.", mention_author=False)

    @commands.command()
    async def play(self, ctx, *, query: str):
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                return await ctx.reply("❌ Join a voice channel first.", mention_author=False)

        if "open.spotify.com" in query:
            if "track" in query:
                track = self.sp.track(query)
                query = f"{track['name']} {track['artists'][0]['name']}"
            elif "playlist" in query:
                playlist = self.sp.playlist(query)
                first = playlist["tracks"]["items"][0]["track"]
                query = f"{first['name']} {first['artists'][0]['name']}"
                await ctx.send(f"🎵 Playlist detected — playing first track: {first['name']}")
            elif "album" in query:
                album = self.sp.album(query)
                first = album["tracks"]["items"][0]
                query = f"{first['name']} {first['artists'][0]['name']}"
                await ctx.send(f"🎵 Album detected — playing first track: {first['name']}")

        async with ctx.typing():
            player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
            ctx.voice_client.stop()
            ctx.voice_client.play(player, after=lambda e: print(f"Player error: {e}") if e else None)
        await ctx.send(f"🎶 Now playing: **{player.title}**")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.send("⏹️ Stopped.")
        else:
            await ctx.reply("❌ Nothing is playing.", mention_author=False)

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused.")
        else:
            await ctx.reply("❌ Nothing is playing.", mention_author=False)

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed.")
        else:
            await ctx.reply("❌ Nothing is paused.", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
