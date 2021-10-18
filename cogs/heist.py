import discord
import colors
import asyncio

from discord.ext import commands
from game import Game, User, Perk, GameExceptions, Bank
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

        
        embed = discord.Embed(
            description = f'You have earned **${amount}** and **{exp}** exp. Your new balance is **${cash}**.',
            colour = colors.gold
        )

        if data.get("perk"):
            embed.set_footer(text="Perk consumed and reward icnreased.")

        await ctx.send(embed=embed)
    
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
            embed = discord.Embed(
                description = f'Your plan to rob **{name}** has failed and you have been fined **${amount}**. Your new balance is **${cash}**.',
                colour = colors.red
            )
        else:
            
            embed = discord.Embed(
                description = f'You just robbed **{name}** for **${amount}** and earned **{exp}** exp. Your new balance is **${cash}**.',
                colour = colors.gold
            )

        if data.get('perk'):
            embed.set_footer(
                text = "A perk was used and the chances of failing was reduced for this attempt."
            )

        await ctx.send(embed=embed)

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

    @commands.command(aliases=["perk"])
    async def myperks(self, ctx):
        game = games.get(ctx.guild.id)
        user = User.get(game.conn, game.c, ctx.author.id)
        user.perks = Perk.get(game.conn, game.c, ctx.author.id)

        embed = discord.Embed(
				title="Perk Information",
				description=f"User: {ctx.author.mention}",
				colour=colors.blue,
				timestamp=ctx.message.created_at
			)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(
            name=f"Tactical Robbery `x{user.perks.rob}`",
            value="Get caught less in **`$rob`**",
            inline=False
        )
        embed.add_field(
            name=f"Energy Drink `x{user.perks.work}`",
            value="Earn more cash in **`$work`**",
            inline=False
        )

        await ctx.send(embed=embed)
    
    @commands.command(aliases=["buy"])
    async def buyperk(self, ctx, item, amount):
        game = games.get(ctx.guild.id)
        name = ctx.author.nick if ctx.author.nick else ctx.author.name

        if item.lower() == 'rob':
            item_name = 'Tactical Robbery'
            data = game.buy_rob(ctx.author.id, amount)
        if item.lower() == 'work':
            item_name = 'Energy Drink'
            data = game.buy_work(ctx.author.id, amount)

        await ctx.send(
            embed = discord.Embed(
                description = f"**{name}** has purchased **{data.get('amount')}x** **{item_name}** for **${data.get('cost')}**.",
                colour = colors.gold
            )
        )

    @commands.command()
    async def shop(self, ctx):
        game = games.get(ctx.guild.id)
        user = User.get(game.conn, game.c, ctx.author.id)

        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")

        shop_items = {
            'work': {'price': '10', 'code': 'work', 'name': 'Energy Drink', 'desc': 'Increases cash and exp gained from `$work`.'},
            'rob': {'price': '50', 'code': 'rob', 'name': 'Tactical Robbery', 'desc': 'Reduces the chance of failing in `$rob`.'}
        }

        embed = discord.Embed(
            title = 'Perk Shop',
            description = "".join(
                [f"Code: `{item.get('code')}` | **{item.get('name')}** `${item.get('price')}`\n{item.get('desc')}\n\n" for key, item in shop_items.items()]
            ),
            colour = colors.blue
        )

        embed.set_footer(
            text="Use [$buy <code> <qty>] to buy perks."
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def bank(self, ctx):
        game = games.get(ctx.guild.id)
        bank = Bank.get(game.conn, game.c, ctx.author.id)

        await ctx.send(
            embed = discord.Embed(
                description = f"Current bank balance: **${bank.balance}**.",
                colour = colors.gold
            )
        )

    @commands.command()
    async def deposit(self, ctx, amount):
        game = games.get(ctx.guild.id)
        amount = game.deposit(ctx.author.id, amount)

        await ctx.send(
            embed = discord.Embed(
                description = f"You have deposited **${amount}**.",
                colour = colors.gold
            )
        )
    
    @commands.command()
    async def withdraw(self, ctx, amount):
        game = games.get(ctx.guild.id)
        amount = game.withdraw(ctx.author.id, amount)

        await ctx.send(
            embed = discord.Embed(
                description = f"You have withdrawn **${amount}**.",
                colour = colors.gold
            )
        )

    @commands.command()
    async def transfer(self, ctx, member: discord.Member, amount):
        game = games.get(ctx.guild.id)

        sender_name = ctx.author.nick if ctx.author.nick else ctx.author.name
        receiver_name = member.nick if member.nick else member.name

        amount = game.transfer(ctx.author.id, member.id, amount)

        await ctx.send(
            embed = discord.Embed(
                description = f"{sender_name} has transferred **${amount}** to {receiver_name}.",
                colour = colors.gold
            )
        )
        
def setup(client):
    client.add_cog(Heist(client))