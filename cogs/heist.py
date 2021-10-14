import discord
import colors

from discord.ext import commands
from game import Game, User

games = {}

class Heist(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        # init game
        for guild in self.client.guilds:
            games[guild.id] = Game(guild.id)

    @commands.command()
    async def register(self, ctx):
        game = games[ctx.guild.id]

        user = game.register(ctx.author.id)

        if not user:
            embed = discord.Embed(
                colour=colors.red,
                title='Yikes!',
                description='It seems that you are already registered.'
            )
            embed.set_thumbnail(url='https://chpic.su/_data/stickers/p/Paimon_Emoji_Set/Paimon_Emoji_Set_012.webp')
        else:
            embed = discord.Embed(
                colour=colors.green,
                title='Nice!',
                description='You are now registered!'
            )
            embed.set_thumbnail(url='https://chpic.su/_data/stickers/p/Paimon_Emoji_Set/Paimon_Emoji_Set_005.webp')
        await ctx.send(embed=embed)

    @commands.command()
    async def profile(self, ctx, member: discord.Member = None):
        if member:
            ctx.author = member

        game = games[ctx.guild.id]
        user = User.get(game.conn, game.c, ctx.author.id)

        if user:
            embed = discord.Embed(title="User Profile", description=f"Showing information for: {ctx.author.mention}", colour=colors.blue, timestamp=ctx.message.created_at)
            embed.add_field(name='Experience', value=f'{user.exp}/{user.exp_to_levelup}', inline=True)
            embed.add_field(name='Level', value=user.level, inline=True)
            embed.add_field(name='Cash', value=f"${user.cash}", inline=True)
            embed.set_thumbnail(url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

def setup(client):
    client.add_cog(Heist(client))