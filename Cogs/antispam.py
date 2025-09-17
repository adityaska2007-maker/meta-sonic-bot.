import discord
from discord.ext import commands
import asyncio
import time
from collections import defaultdict

class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.msg_history = defaultdict(list)  # {user_id: [timestamps]}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if not self.bot.config.get("antispam", True):
            return

        cfg = self.bot.config.get("spam", {"window": 7, "max_messages": 5})
        window = cfg.get("window", 7)       # seconds
        max_msgs = cfg.get("max_messages", 5)

        user_id = message.author.id
        now = time.time()

        # Clean old timestamps
        self.msg_history[user_id] = [t for t in self.msg_history[user_id] if now - t <= window]
        self.msg_history[user_id].append(now)

        if len(self.msg_history[user_id]) > max_msgs:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            try:
                warn_msg = await message.channel.send(
                    f"⚠️ {message.author.mention}, please slow down! (AntiSpam protection)"
                )
                await warn_msg.delete(delay=3)
            except discord.Forbidden:
                pass

            log_channel_id = self.bot.config.get("log_channel_id")
            if log_channel_id and (log_channel := self.bot.get_channel(int(log_channel_id))):
                await log_channel.send(
                    f"🚨 **AntiSpam triggered**: {message.author.mention} exceeded {max_msgs} messages in {window}s."
                )

    @commands.command(name="antispam")
    @commands.has_permissions(administrator=True)
    async def toggle_antispam(self, ctx, mode: str = None):
        """
        Enable/disable AntiSpam per guild
        Usage: >antispam on / off
        """
        if mode not in ["on", "off"]:
            return await ctx.send("Usage: `antispam on` or `antispam off`")

        self.bot.config["antispam"] = (mode == "on")
        await self.bot.save_config()  # persist config
        await ctx.send(f"✅ AntiSpam is now **{mode.upper()}**")

async def setup(bot):
    # Ensure config + save_config are attached
    if not hasattr(bot, "config"):
        from main import config, save_config
        bot.config = config
        bot.save_config = save_config
    await bot.add_cog(AntiSpam(bot))
