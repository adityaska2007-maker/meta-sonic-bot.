import discord
from discord.ext import commands

class Logs(commands.Cog):
    """Logs join/leave and deleted messages."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_log_channel(self, guild: discord.Guild):
        channel_id = self.bot.config.get("log_channel_id")
        if channel_id:
            return guild.get_channel(channel_id)
        return None

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlog(self, ctx, channel: discord.TextChannel):
        self.bot.config["log_channel_id"] = channel.id
        await self.bot.save_config()
        await ctx.send(f"✅ Log channel set to {channel.mention}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.get_log_channel(member.guild)
        if channel:
            await channel.send(f"📥 {member.mention} joined.")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.get_log_channel(member.guild)
        if channel:
            await channel.send(f"📤 {member.mention} left.")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or message.guild is None:
            return
        channel = self.get_log_channel(message.guild)
        if channel:
            await channel.send(f"🗑️ Deleted message by {message.author.mention}: {message.content}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))
