#!/usr/bin/env python3
# main.py — MetaSonic entrypoint (Python 3.12)

import os
import json
import asyncio
import logging
import traceback
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

# --- logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# --- env & config ---
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_PATH = Path("my_config.json")
COGS_DIR = Path("./cogs")

DEFAULT_CONFIG = {
    "owner_id": 123456789012345678,
    "default_prefix": ">",
    "guild_prefixes": {},
    "log_channel_id": None,
    "trusted_roles": [],
    "trusted_users": []
}

if not CONFIG_PATH.exists():
    CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=4))

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

_save_lock = asyncio.Lock()


async def save_config():
    async with _save_lock:
        tmp = CONFIG_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(config, indent=4), encoding="utf-8")
        tmp.replace(CONFIG_PATH)
        logging.info("Config saved")


def get_prefix(bot, message):
    if not message.guild:
        return config.get("default_prefix", ">")
    return config.get("guild_prefixes", {}).get(str(message.guild.id), config.get("default_prefix", ">"))


intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix=lambda bot, msg: commands.when_mentioned_or(get_prefix(bot, msg))(bot, msg),
    intents=intents,
    help_command=commands.DefaultHelpCommand()
)

# attach config and save to bot
bot.config = config
bot.save_config = save_config

# --- events ---
@bot.event
async def on_ready():
    logging.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    logging.info(f"Guild count: {len(bot.guilds)}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You don't have permission.", mention_author=False)
        return
    if isinstance(error, commands.CommandNotFound):
        return
    logging.error("Unhandled error:\n" + "".join(traceback.format_exception(type(error), error, error.__traceback__)))
    try:
        await ctx.reply("An internal error occurred.", mention_author=False)
    except Exception:
        pass

# --- basic commands ---
@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, new_prefix: str):
    config.setdefault("guild_prefixes", {})[str(ctx.guild.id)] = new_prefix
    await save_config()
    await ctx.reply(f"✅ Prefix set to `{new_prefix}`.", mention_author=False)

@bot.command(name="resetprefix")
@commands.has_permissions(administrator=True)
async def reset_prefix(ctx):
    guild_id = str(ctx.guild.id)
    if guild_id in config.get("guild_prefixes", {}):
        del config["guild_prefixes"][guild_id]
        await save_config()
        await ctx.reply(f"✅ Prefix reset to default `{config.get('default_prefix', '>')}`.", mention_author=False)
    else:
        await ctx.reply("Nothing to reset — using default prefix.", mention_author=False)

@bot.command(name="clear", aliases=["purge"])
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 10):
    if amount < 1:
        await ctx.reply("Enter a valid number.", mention_author=False)
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted {len(deleted)-1} messages.", delete_after=5)


# --- load cogs ---
async def load_all_cogs():
    failed = []
    if not COGS_DIR.exists():
        logging.warning("No cogs/ folder found.")
        return failed

    for file in sorted(COGS_DIR.glob("*.py")):
        if file.name.startswith("_"):
            continue
        ext_name = f"cogs.{file.stem}"
        try:
            await bot.load_extension(ext_name)
            logging.info(f"✅ Loaded {ext_name}")
        except Exception as exc:
            logging.error(f"❌ Failed to load {ext_name}: {exc}")
            failed.append({"ext": ext_name, "error": str(exc)})
    return failed


# --- main ---
async def main():
    if not TOKEN:
        logging.critical("DISCORD_TOKEN missing!")
        return
    async with bot:
        failed = await load_all_cogs()
        if failed:
            logging.error("Some cogs failed: %s", failed)
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
