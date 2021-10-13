import discord
import colors

from discord.ext import commands

settings = {
    "use_custom_message": "False"
}

class Greeter(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.config = client.config

    @commands.Cog.listener()
    async def on_ready(self):
        # init config data for this cog
        for guild in self.client.guilds:
            for key, value in settings.items():
                if not self.config[guild.id].get(__name__, key):
                    self.config[guild.id].set(__name__, key, value)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        config = self.config[guild_id]

        pass

    @commands.command()
    async def setgreeting(self, ctx, *, message):
        config = self.config[ctx.guild.id]

        # removes tick/double tick from message
        # ticks may cause formatting errors in config files
        if message.startswith('"') or message.startswith("'"):
            message = message[1:]
        if message.endswith('"') or message.endswith("'"):
            message = message[:-1]

        config.set(__name__, "custom_message", message)

        await ctx.send(
            embed = discord.Embed(
                description = f"Custom greet message adjusted to:\n\n[{message}]",
                colour = colors.blue
            )
        )

    @commands.command()
    async def setgreetmode(self, ctx):
        config = self.config[ctx.guild.id]
        value = config.getboolean(__name__, 'use_custom_message')
        
        value = False if value else True
        config.set(__name__, 'use_custom_message', str(value))

        await ctx.send(
            embed = discord.Embed(
                description = f'Setting: [**use_custom_message**] changed to [**{value}**].',
                colour = colors.blue
            )
        )

def setup(client):
    client.add_cog(Greeter(client))