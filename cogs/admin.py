import discord
import colors

from discord.ext import commands
from checks import is_whitelisted, whitelist_level
from logger import console_log
from bot import cog_names

class InsufficientAccess(commands.CommandError):
    """The access level is insufficient."""
    pass

class InvalidModule(commands.CommandError):
    """Module does not exist"""
    pass

class Admin(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.config = client.config

    async def cog_command_error(self, ctx, error):
        await ctx.send(
            embed = discord.Embed(
                description = error,
                colour = colors.red
            )
        )
        
        console_log(f"Error occurred while executing command: '{ctx.command}' in {ctx.guild.name}/{ctx.channel.name}: {type(error)}: {error}")

    @commands.command()
    @commands.check(is_whitelisted)
    async def cogs(self, ctx):
        required_access = 3

        if not whitelist_level(ctx, required_access):
            raise InsufficientAccess("You do not have access to this command.")

        embed = discord.Embed(
            title = "Modules",
            description = "".join(
                [f"{index}: **{name[0].upper() + name[1:]}**\n" for index, name in enumerate(cog_names, start=1)]
            ),
            colour = colors.blue
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(is_whitelisted)
    async def reloadcog(self, ctx, name):
        required_access = 3

        if not whitelist_level(ctx, required_access):
            raise InsufficientAccess("You do not have access to this command.")

        if name in cog_names:
            self.client.reload_extension(f'cogs.{name}')
            await ctx.send(
                embed = discord.Embed(
                    description = f"**cogs.{name}** reloaded.",
                    colour = colors.blue
                )
            )
        else:
            raise InvalidModule(f"There is no module named **{name}**.")

    @commands.command(aliases=["r"])
    @commands.check(is_whitelisted)
    async def restart(self, ctx):
        required_access = 5

        if not whitelist_level(ctx, required_access):
            raise InsufficientAccess("You do not have access to this command.")

        name = ctx.author.nick if ctx.author.nick else ctx.author.name
        await ctx.send(
            embed = discord.Embed(
                description = f"The **restart** command has been issued by **{name}**. I'll be back shortly.",
                colour = colors.red
            )
        )
        await self.client.close()

def setup(client):
    client.add_cog(Admin(client))