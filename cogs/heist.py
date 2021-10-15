import discord
import colors
import asyncio

from discord.ext import commands
from game import Game, User, GameExceptions
from logger import console_log

games = {}
settings = {}

class Heist(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def cog_command_error(self, ctx, error):
        await ctx.send(
            embed = discord.Embed(
                description = error,
                colour = colors.red
            )
        )
        
        console_log(f"Error occurred while executing command: '{ctx.command}' in {ctx.guild.name}/{ctx.channel.name}: {type(error)}: {error}")
        
        if not isinstance(error, commands.CommandOnCooldown):
            ctx.command.reset_cooldown(ctx)
            console_log(f"Command '{ctx.command}' for {ctx.guild.name} has been reset due to an error")

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
        game = games.get(ctx.guild.id)

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

        game = games.get(ctx.guild.id)
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
        game = games.get(ctx.guild.id)
        
        data = game.work(ctx.author.id)
        amount = data.get('amount')
        cash = data.get('cash')
        exp = data.get('exp')
        levelup = data.get('levelup')

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
        game = games.get(ctx.guild.id)
        name = member.nick if member.nick else member.name

        if member == ctx.author:
            await ctx.send(
                embed = discord.Embed(
                    description = "You cannot rob yourself.",
                    colour = colors.red
                )
            )
            return

        data = game.rob(ctx.author.id, member.id)
        failed = data.get('failed')
        amount = data.get('amount')
        cash = data.get('cash')
        exp = data.get('exp')
        levelup = data.get('levelup')

        if levelup:
            await self.levelup(ctx)

        if failed:
            await ctx.send(
                embed = discord.Embed(
                    description = f'Your plan to rob **{name}** has failed and you have been fined **${amount}**. Your new balance is **${cash}**.',
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

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def donate(self, ctx, member: discord.Member, amount):
        game = games.get(ctx.guild.id)
        name =  member.nick if member.nick else member.name

        amount = int(amount)

        data = game.donate(ctx.author.id, member.id, amount)
        exp = data.get('exp')
        levelup = data.get('levelup')

        if levelup:
            self.levelup(ctx)

        await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} just donated **${amount}** to **{name}** and earned **{exp}** exp.",
                colour = colors.gold
            )
        )

    @commands.command()
    async def charity(self, ctx, amount):
        game = games.get(ctx.guild.id)
        name = ctx.author.nick if ctx.author.nick else ctx.author.name

        data = game.charity(ctx.author.id, amount)
        exp = data.get('exp')

        levelup = data.get('levelup')
        if levelup:
            self.levelup(ctx)

        await ctx.send(
            embed = discord.Embed(
                description = f"**{name}** just donated **${amount}** to charity and earned **{exp}** exp.",
                colour = colors.blue
            )
        )

    @commands.command()
    async def gamble(self, ctx, amount):
        game = games.get(ctx.guild.id)

        embed = discord.Embed(
            description=f'{ctx.author.mention}, are you sure you want to gamble for **${amount}**?',
            colour = colors.red,
        )

        check_emoji = '✅'
        x_emoji = '❌'

        verify = await ctx.send(embed=embed)
        await verify.add_reaction(check_emoji)
        await verify.add_reaction(x_emoji)

        try:
            reaction, user = await self.client.wait_for(
                'reaction_add',
                timeout=10,
                check=lambda reaction, user: user == ctx.author
            )
            if str(reaction.emoji) == x_emoji:
                await verify.delete()
                embed = discord.Embed(
                    description = "Gamble cancelled.",
                    colour = colors.red
                )

                await ctx.send(embed=embed, delete_after=10)
                return

            if str(reaction.emoji) == check_emoji:
                await verify.delete()

                data = game.gamble(ctx.author.id, amount)
                win = data.get('win')
                amount = data.get('amount')

                if win:
                    end_msg = discord.Embed(
                        description=f'Congratulations, {ctx.author.mention}! You gambled and won **${amount}**.',
                        colour = colors.gold
                    )
                else:
                    end_msg = discord.Embed(
                        description=f'Yikes, {ctx.author.mention}! You gambled and lost **${amount}**.',
                        colour = colors.red
                    )

                end_msg.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
                await ctx.send(embed=end_msg)
        except asyncio.TimeoutError:
            await verify.delete()
            await ctx.send('Cancelling due to timeout.')

def setup(client):
    client.add_cog(Heist(client))