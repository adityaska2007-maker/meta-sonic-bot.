import discord
from discord.ext import commands
import re
import asyncio

invite_regex = re.compile(r"(https?:\/\/)?(www\.)?(discord\.gg|discord\.com\/invite)\/[a-zA-Z0-9]+")

class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Check AntiLink status from config
        if not self.bot.config.get("anti_invite", True):
            return

        if invite_regex.search(message.content) or "http" in message.content:
            try:
                await message.delete()
            except discord.Forbidden:
                return

            warn_msg = await message.channel.send(
                f"🚫 {message.author.mention}, links are not allowed!"
            )
            await warn_msg.delete(delay=5)

            log_channel_id = self.bot.config.get("log_channel_id")
            if log_channel_id:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    await log_channel.send(
                        f"🚨 **AntiLink triggered**: {message.author.mention} tried posting `{message.content}`"
                    )

    @commands.command(name="antilink")
    @commands.has_permissions(administrator=True)
    async def toggle_antilink(self, ctx, mode: str = None):
        """
        Enable/disable AntiLink
        Usage: >antilink on / off
        """
        if mode not in ["on", "off"]:
            return await ctx.send("Usage: `antilink on` or `antilink off`")

        self.bot.config["anti_invite"] = (mode == "on")
        await self.bot.save_config()  # persist change
        await ctx.send(f"✅ AntiLink is now **{mode.upper()}**")

async def setup(bot):
    # Attach config + save_config from main.py if not already
    if not hasattr(bot, "config"):
        from main import config, save_config
        bot.config = config
        bot.save_config = save_config
    await bot.add_cog(AntiLink(bot))
