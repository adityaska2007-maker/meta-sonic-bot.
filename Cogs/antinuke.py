import discord
from discord.ext import commands


class AntiNuke(commands.Cog):
    """Anti-nuke protection with whitelist support."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def whitelist(self, ctx):
        users = self.bot.config.get("trusted_users", [])
        roles = self.bot.config.get("trusted_roles", [])
        msg = []
        if users:
            msg.append("👤 Users: " + ", ".join([f"<@{u}>" for u in users]))
        if roles:
            msg.append("📌 Roles: " + ", ".join([f"<@&{r}>" for r in roles]))
        if not msg:
            msg = ["⚠️ Whitelist is empty."]
        await ctx.send("\n".join(msg))

    @whitelist.command()
    @commands.has_permissions(administrator=True)
    async def adduser(self, ctx, user: discord.User):
        wl = self.bot.config.setdefault("trusted_users", [])
        if user.id not in wl:
            wl.append(user.id)
            await self.bot.save_config()
            await ctx.send(f"✅ Added {user.mention} to whitelist.")
        else:
            await ctx.send(f"⚠️ {user.mention} already whitelisted.")

    @whitelist.command()
    @commands.has_permissions(administrator=True)
    async def removeuser(self, ctx, user: discord.User):
        wl = self.bot.config.setdefault("trusted_users", [])
        if user.id in wl:
            wl.remove(user.id)
            await self.bot.save_config()
            await ctx.send(f"❌ Removed {user.mention} from whitelist.")
        else:
            await ctx.send(f"⚠️ {user.mention} not in whitelist.")

    @whitelist.command()
    @commands.has_permissions(administrator=True)
    async def addrole(self, ctx, role: discord.Role):
        wl = self.bot.config.setdefault("trusted_roles", [])
        if role.id not in wl:
            wl.append(role.id)
            await self.bot.save_config()
            await ctx.send(f"✅ Added role {role.mention} to whitelist.")
        else:
            await ctx.send(f"⚠️ {role.mention} already whitelisted.")

    @whitelist.command()
    @commands.has_permissions(administrator=True)
    async def removerole(self, ctx, role: discord.Role):
        wl = self.bot.config.setdefault("trusted_roles", [])
        if role.id in wl:
            wl.remove(role.id)
            await self.bot.save_config()
            await ctx.send(f"❌ Removed role {role.mention} from whitelist.")
        else:
            await ctx.send(f"⚠️ {role.mention} not in whitelist.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiNuke(bot))
