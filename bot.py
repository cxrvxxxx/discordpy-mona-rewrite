import discord
import os

from glob import glob
from discord.ext import commands
from dotenv import load_dotenv
from logger import console_log
from config import Config

# load and read token from .env
load_dotenv()
token = os.getenv('TOKEN')

# init dirs
dirs = [
    'config',
    'playlists'
]
for dir in dirs:
    if not os.path.exists(dir):
        os.mkdir(dir)

# list files in /cogs
cog_names = glob("./cogs/*.py")
for index, name in enumerate(cog_names):
    cog_names[index] = name[7:-3]

# set intents
intents = discord.Intents().all()
intents.typing = False
intents.presences = False

# define client
client = commands.AutoShardedBot(command_prefix='$', help_command=None, intents=intents)

# client.property
client.config = {}

# load cogs from /cogs
for name in cog_names:
    client.load_extension(f'cogs.{name}')
    console_log(f"Loaded '{name}' cog")

# startup on initialization
@client.event
async def on_ready():
    console_log(f"Connected to discord as {client.user}.")
    # set activity status
    await client.change_presence(
        activity = discord.Activity(
            type = discord.ActivityType.watching,
            name = "the stars ($info)."
        )
    )

    # init per guild config
    for guild in client.guilds:
        config_path = f'./config/{guild.id}.ini'
        client.config[guild.id] = Config(config_path)

# run bot
client.run(token)