import discord
import colors

from discord.ext import commands

class Whitelist(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.config = client.config

    @commands.command()
    async def whitelist(self, ctx, member: discord.Member, access=0):
        config = self.config[ctx.guild.id]
        name = member.nick if member.nick else member.name

        author_level = config.getint(__name__, ctx.author.id)
        access = int(access)

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

    @commands.command()
    async def unwhitelist(self, ctx, member: discord.Member):
        config = self.config[ctx.guild.id]
        name = member.nick if member.nick else member.name

        author_level = config.getint(__name__, ctx.author.id)
        target_level = config.getint(__name__, member.id)

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