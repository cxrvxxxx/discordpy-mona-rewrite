import discord
import os
import cogs

from discord.ext import commands
from dotenv import load_dotenv

# load and read token from .env
load_dotenv()
token = os.getenv('TOKEN')

# set intents
intents = discord.Intents().all()
intents.typing = False
intents.presences = False

# define client
client = commands.AutoShardedBot(command_prefix='$', help_command=None, intents=intents)

# startup on initialization
@client.event
async def on_ready():
    print(f"Connected to discord as {client.user}.")
    # set activity status
    await client.change_presence(
        activity = discord.Activity(
            type = discord.ActivityType.watching,
            name = "the stars ($info)."
        )
    )

# run bot
client.run(token)