import discord
from discord.ext import commands

# Define your modules
MODULES = {
    "Main": ["AntiNuke", "Auto Moderation", "Music", "Moderation", "Giveaway", "Ticket", "Utility", "Welcomer"],
    "Extra": ["Auto Responder", "Custom Roles", "Logging", "Media", "VCRoles", "Fun", "Bot"]
}

class HelpMenu(discord.ui.View):
    def __init__(self, embed_author):
        super().__init__(timeout=None)
        self.embed_author = embed_author

        # Buttons
        self.add_item(discord.ui.Button(label="Main Module", style=discord.ButtonStyle.primary, custom_id="main_module"))
        self.add_item(discord.ui.Button(label="Extra Module", style=discord.ButtonStyle.primary, custom_id="extra_module"))
        self.add_item(discord.ui.Button(label="Search Command", style=discord.ButtonStyle.secondary, custom_id="search_command"))

    @discord.ui.button(label="Main Module", style=discord.ButtonStyle.primary, custom_id="main_module")
    async def main_module(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="📦 Main Modules", color=discord.Color.blurple())
        embed.set_author(name=self.embed_author.name, icon_url=self.embed_author.display_avatar.url)
        embed.description = "\n".join([f"• {m}" for m in MODULES["Main"]])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Extra Module", style=discord.ButtonStyle.primary, custom_id="extra_module")
    async def extra_module(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="📦 Extra Modules", color=discord.Color.blurple())
        embed.set_author(name=self.embed_author.name, icon_url=self.embed_author.display_avatar.url)
        embed.description = "\n".join([f"• {m}" for m in MODULES["Extra"]])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Search Command", style=discord.ButtonStyle.secondary, custom_id="search_command")
    async def search_command(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔎 Type the command name to search for help.", ephemeral=True)


class Help(commands.Cog):
    """Interactive help command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = discord.Embed(title="MetaSonic Help", description=f"Prefix is `{self.bot.command_prefix(ctx.bot, ctx.message)}`\nUse `?help <command>` for details.", color=discord.Color.blue())
        embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.display_avatar.url)
        embed.add_field(name="Main Modules", value="📦 Click the buttons below", inline=False)
        view = HelpMenu(embed_author=ctx.author)
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
