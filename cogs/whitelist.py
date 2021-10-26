import discord
import colors

from discord.ext import commands
from checks import is_whitelisted

class Whitelist(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.config = client.config

    @commands.command()
    async def wlhelp(self, ctx):
        commands = {
            "(w)hite(l)ist <@user> <level>": "Add user to the whitelist.",
            "(unw)hite(l)ist <@user>": "Remove user from the whitelist.",
            "myaccess": "Check your access level."
        }

        embed = discord.Embed(
            title = "Whitelist Commands",
            description = "".join([f"**${key}**\n{value}\n\n" for key, value in commands.items()]),
            colour = colors.blue
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=["wl"])
    @commands.check(is_whitelisted)
    async def whitelist(self, ctx, member: discord.Member, access=0):
        config = self.config[ctx.guild.id]
        name = member.nick if member.nick else member.name

        author_level = config.getint(__name__, ctx.author.id)
        access = int(access)

        if ctx.author == member:
            await ctx.send(
                embed = discord.Embed(
                    description = "You cannot modify your own access level.",
                    colour = colors.red
                )
            )
            return

        # return if access is greater than author's access
        if author_level <= access:
            await ctx.send(
                embed = discord.Embed(
                    description = "You cannot add users to the whitelist with greater or equal access than you.",
                    colour = colors.red
                )
            )
            return

        config.set(__name__, member.id, access)

        await ctx.send(
            embed = discord.Embed(
                description = f'Added **{name}** to the whitelist with access level **{access}**.',
                colour = colors.blue
            )
        )

    @commands.command(aliases=["unwl"])
    @commands.check(is_whitelisted)
    async def unwhitelist(self, ctx, member: discord.Member):
        config = self.config[ctx.guild.id]
        name = member.nick if member.nick else member.name

        author_level = config.getint(__name__, ctx.author.id)
        target_level = config.getint(__name__, member.id)

        if ctx.author == member:
            await ctx.send(
                embed = discord.Embed(
                    description = "You cannot modify your own access level.",
                    colour = colors.red
                )
            )
            return

        # return if access is greater than author's access
        if author_level <= target_level:
            await ctx.send(
                embed = discord.Embed(
                    description = "You cannot remove users from the whitelist with greater or equal access than you.",
                    colour = colors.red
                )
            )
            return

        config.delete(__name__, member.id)

        await ctx.send(
            embed = discord.Embed(
                description = f'Removed **{name}** from the whitelist.',
                colors = colors.blue
            )
        )
    
    @commands.command()
    async def myaccess(self, ctx):
        config = self.config[ctx.guild.id]

        access = config.get(__name__, ctx.author.id)

        await ctx.send(
            embed = discord.Embed(
                description = f'Your access level is **{access}**',
                colour = colors.blue
            )
        )

def setup(client):
    client.add_cog(Whitelist(client))