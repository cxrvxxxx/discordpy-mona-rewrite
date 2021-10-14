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
        guild = member.guild
        config = self.config[guild.id]

        default_greet_message = f"Welcome to **{guild.name}**, {member.mention}!"
        use_custom_message = config.getboolean(__name__, 'use_custom_message')
        custom_message = config.get(__name__, 'custom_message')
        welcome_channel_id = config.getint(__name__, 'welcome_channel')
        channel = self.client.get_channel(welcome_channel_id)

        if use_custom_message and custom_message and channel:
            await channel.send(default_greet_message + custom_message)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
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
    @commands.has_permissions(manage_channels=True)
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

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setgreetchannel(self, ctx):
        config = self.config[ctx.guild.id]

        config.set(__name__, 'welcome_channel', ctx.channel.id)

        await ctx.send(
            embed = discord.Embed(
                description = "This channel will now be used for welcome messages.",
                colour = colors.blue
            )
        )

def setup(client):
    client.add_cog(Greeter(client))