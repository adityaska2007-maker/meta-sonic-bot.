#!/usr/bin/env python3
# main.py — entrypoint for MetaSonic (designed for Python 3.12)

import os
import json
import asyncio
import logging
import traceback
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

# --- basic logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# --- env & config paths ---
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_PATH = Path("my_config.json")
COGS_DIR = Path("./cogs")

# --- default config (will be written if missing) ---
DEFAULT_CONFIG = {
    "owner_id": 123456789012345678,
    "default_prefix": ">",
    "guild_prefixes": {},
    "log_channel_id": None,
    "trusted_roles": [],
    "trusted_users": []
}

# Ensure config exists
if not CONFIG_PATH.exists():
    logging.info("my_config.json missing — creating default")
    CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=4))

# Load config
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# Async lock to protect writes
_save_lock = asyncio.Lock()


async def save_config():
    """Safely write config to disk."""
    async with _save_lock:
        tmp = CONFIG_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(config, indent=4), encoding="utf-8")
        tmp.replace(CONFIG_PATH)
        logging.info("Config saved")


# Prefix resolver (per-guild prefix support)
def get_prefix(bot, message):
    # DM fallback -> default prefix
    if not message.guild:
        return config.get("default_prefix", ">")
    guild_id = str(message.guild.id)
    return config.get("guild_prefixes", {}).get(guild_id, config.get("default_prefix", ">"))


# Full intents as requested
intents = discord.Intents.all()

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=commands.DefaultHelpCommand())

# --- Basic events & error handling ---
@bot.event
async def on_ready():
    logging.info(f"✅ Logged in as: {bot.user} (ID: {bot.user.id})")
    logging.info(f"Guild count: {len(bot.guilds)}")


@bot.event
async def on_command_error(ctx, error):
    # Handle common errors gracefully
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You don't have permission to run this command.", mention_author=False)
        return
    if isinstance(error, commands.CommandNotFound):
        return
    # Unhandled: log and reply
    logging.error("Unhandled command error:\n" + "".join(traceback.format_exception(type(error), error, error.__traceback__)))
    try:
        await ctx.reply("An internal error occurred. The owner has been notified.", mention_author=False)
    except Exception:
        pass


# --- Admin prefix commands (per-guild) ---
@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, new_prefix: str):
    guild_id = str(ctx.guild.id)
    config.setdefault("guild_prefixes", {})[guild_id] = new_prefix
    await save_config()
    await ctx.reply(f"✅ Prefix set to `{new_prefix}` for this server.", mention_author=False)


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


# --- Extension (cog) loader ---
async def load_all_cogs():
    failed = []
    if not COGS_DIR.exists():
        logging.warning("No cogs/ directory found.")
        return failed

    for file in sorted(COGS_DIR.iterdir()):
        if file.suffix != ".py":
            continue
        if file.name.startswith("_"):
            # skip private/internal files
            continue
        ext_name = f"cogs.{file.stem}"
        try:
            logging.info(f"Loading extension {ext_name} ...")
            # use await so async setup() in cogs is supported
            await bot.load_extension(ext_name)
            logging.info(f"Loaded {ext_name}")
        except Exception as exc:
            logging.exception(f"Failed to load {ext_name}: {exc}")
            failed.append({"ext": ext_name, "error": str(exc)})
    return failed


# --- Startup / main ---
async def main():
    if not TOKEN:
        logging.critical("DISCORD_TOKEN missing in environment (.env). Exiting.")
        return

    async with bot:
        failed = await load_all_cogs()
        if failed:
            logging.error("Some cogs failed to load: %s", failed)
        try:
            await bot.start(TOKEN)
        except Exception:
            logging.exception("Error while running bot")
            raise


if __name__ == "__main__":
    asyncio.run(main())
