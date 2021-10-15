import discord
import colors

from discord.ext import commands
from game import Game, User
from logger import console_log

games = {}
settings = {}

class Heist(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def levelup(self, ctx):
        embed = discord.Embed(
            title='Yay!',
            description=f'{ctx.author.mention} has leveled up!',
            colour=colors.green
        )
        embed.set_thumbnail(
            url='https://chpic.su/_data/stickers/p/Paimon_Emoji_Set/Paimon_Emoji_Set_006.webp'
        )
        await ctx.send(embed=embed)

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

    @commands.command(aliases=["me", "stats"])
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

    @commands.command(aliases=["w"])
    @commands.cooldown(1, 300, commands.BucketType.member)
    async def work(self, ctx):
        game = games[ctx.guild.id]
        
        try:
            data = game.work(ctx.author.id)
            amount = data.get('amount')
            cash = data.get('cash')
            exp = data.get('exp')
            levelup = data.get('levelup')
        except Exception as e:
            console_log(e)
            return

        if levelup:
            await self.levelup(ctx)

        await ctx.send(
            embed = discord.Embed(
                description = f'You have earned **${amount}** and **{exp}** exp. Your new balance is **${cash}**.',
                colour = colors.gold
            )
        )
    
    @commands.command()
    @commands.cooldown(1, 90, commands.BucketType.member)
    async def rob(self, ctx, member: discord.Member):
        game = games[ctx.guild.id]
        name = member.nick if member.nick else member.name

        if member == ctx.author:
            await ctx.send(
                embed = discord.Embed(
                    description = "You cannot rob yourself.",
                    colour = colors.red
                )
            )
            return

        try:
            data = game.rob(ctx.author.id, member.id)
            failed = data.get('failed')
            amount = data.get('amount')
            cash = data.get('cash')
            exp = data.get('exp')
            levelup = data.get('levelup')
        except Exception as e:
            await ctx.send(
                embed = discord.Embed(
                    description = "You cannot rob this user.",
                    colour = colors.red
                )
            )
            console_log(e)
            return

        if levelup:
            await self.levelup(ctx)

        if failed:
            await ctx.send(
                embed = discord.Embed(
                    description = f'Your plan to rob **{name}** has failed and you have been fined **${amount}** for it. Your new balance is **${cash}**.',
                    colour = colors.red
                )
            )
        else:
            await ctx.send(
                embed = discord.Embed(
                    description = f'Your just robbed **{name}** for **${amount}** and earned **{exp}** exp. Your new balance is **${cash}**.',
                    colour = colors.gold
                )
            )

def setup(client):
    client.add_cog(Heist(client))