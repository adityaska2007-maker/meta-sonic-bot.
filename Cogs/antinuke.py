import discord
from discord.ext import commands

class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_trusted(self, user_id: int):
        return str(user_id) in self.bot.config.get("trusted_users", [])

    async def punish(self, guild, user, action: str):
        log_channel_id = self.bot.config.get("log_channel_id")
        member = guild.get_member(user.id)

        if log_channel_id:
            log_channel = self.bot.get_channel(int(log_channel_id))
            if log_channel:
                await log_channel.send(f"🚨 **AntiNuke triggered**: {user.mention} attempted {action}!")

        if member and not self.is_trusted(user.id):
            try:
                await member.kick(reason=f"AntiNuke: unauthorized {action}")
                if log_channel_id and (log_channel := self.bot.get_channel(int(log_channel_id))):
                    await log_channel.send(f"🦵 {member.mention} kicked for **{action}**")
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not self.bot.config.get("antinuke", True):
            return
        guild = channel.guild
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                await self.punish(guild, entry.user, "channel delete")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if not self.bot.config.get("antinuke", True):
            return
        guild = role.guild
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                await self.punish(guild, entry.user, "role delete")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if not self.bot.config.get("antinuke", True):
            return
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                await self.punish(guild, entry.user, "ban")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not self.bot.config.get("antinuke", True):
            return
        guild = member.guild
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                await self.punish(guild, entry.user, "kick")
        except discord.Forbidden:
            pass

    @commands.command(name="antinuke")
    @commands.has_permissions(administrator=True)
    async def toggle_antinuke(self, ctx, mode: str = None):
        """
        Enable/disable AntiNuke
        Usage: >antinuke on / off
        """
        if mode not in ["on", "off"]:
            return await ctx.send("Usage: `antinuke on` or `antinuke off`")

        self.bot.config["antinuke"] = (mode == "on")
        await self.bot.save_config()  # persist change
        await ctx.send(f"✅ AntiNuke is now **{mode.upper()}**")

async def setup(bot):
    # Ensure config + save_config are attached
    if not hasattr(bot, "config"):
        from main import config, save_config
        bot.config = config
        bot.save_config = save_config
    await bot.add_cog(AntiNuke(bot))
