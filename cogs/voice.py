import discord
import DiscordUtils
import asyncio
import colors

from discord.ext import commands
from logger import console_log

settings = {
    'voice_auto_disconnect': 'True'
}

music = DiscordUtils.Music()
channels = {}

class VoiceExceptions:
    class AlreadyConnectedToVoice(commands.CommandError):
        """Already connected to voice"""
        pass
    
    class NotConnectedToVoice(commands.CommandError):
        """Not connected to voice"""
        pass

    class InvalidTitle(commands.CommandError):
        """Title cannot be played"""
        pass

    class IncorrectControlChannel(commands.CommandError):
        """Cannot be controlled from this channel"""
        pass

    class NoActivePlayer(commands.CommandError):
        """No player found"""
        pass

    class EmptyQueue(commands.CommandError):
        """Queue is empty"""
        pass

    class InvalidVolume(commands.CommandError):
        """Volume value out of range"""
        pass

class Voice(commands.Cog):
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

    @commands.Cog.listener()
    async def on_ready(self):
        # init config data for this cog
        for guild in self.client.guilds:
            for key, value in settings.items():
                if not self.config[guild.id].get(__name__, key):
                    self.config[guild.id].set(__name__, key, value)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        config = self.config[member.guild.id]
        channel = channels.get(member.guild.id)
        auto_disconnect = config.getboolean(__name__, 'voice_auto_disconnect')
        user_count = len(member.guild.voice_client.members)

        # do nothing if the update does not come from the bot
        if member != self.client.user:
            return

        if (user_count < 2 and auto_disconnect) and channel:
            await asyncio.sleep(180)

            if user_count < 2:
                embed = discord.Embed(
                    colour=colors.blue,
                    description=f"Disconnecting from **[{channel.name}]** since no one else is in the channel."
                )
                
                channels.remove(channel)
                await channel.send(embed=embed)                    
                await member.guild.voice_client.disconnect()

    @commands.command(aliases=['toggleadc'])
    async def toggleautodisconnect(self, ctx):
        config = self.config[ctx.guild.id]

        value = config.getboolean(__name__, 'voice_auto_disconnect')
        config.set(__name__, 'voice_auto_disconnect', False if value else True)

        embed = discord.Embed(
            colour=colors.blue,
            description=f"Automatic voice channel disconnection **{'disabled' if value else 'enabled'}**."
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=['musichelp'])
    async def music(self, ctx):
        embed = discord.Embed(colour=colors.blue, title="Music Player", description="Guide & Commands")
        embed.add_field(name="How to play?", value="Connect to a voice channel and use the commands below to interact with the player.", inline=False)
        embed.add_field(name="Commands", value="**$join** - Mona joins your voice channel.\n**$play <url/song title>** - Plays the specified youtube url or song.\n**$queue** - Displays the current queue.\n**$skip** - Play the next song in the queue.\n**$leave** - Mona stops playing and disconnects from the voice channel.\n**$volume <0-100>** - Set the volume for the currently playing track.\n**$pause** - Pause the current track.\n**$resume** - Resume playback.\n**$fave <optional: url>** - Adds the currently playing track to your favorites. If a link is provided, add that instead.\n**$favorites** - Show your favorite tracks.\n**$unfave <id>** - Removes the specified track from your favorites.", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def join(self, ctx, silent=False):
        if ctx.voice_client:
            raise VoiceExceptions.AlreadyConnectedToVoice(f"Already connected to voice channel **[{ctx.voice_client.channel.name}]**.")

        if not ctx.author.voice:
            raise VoiceExceptions.NotConnectedToVoice("You are not connected to a **voice channel**.")

        embed = discord.Embed(
            colour=colors.blue,
            description=f"Connected to **[{ctx.author.voice.channel.name}]** and bound to **[{ctx.channel.name}]**."
        )

        channels[ctx.guild.id] = ctx.channel
        await ctx.author.voice.channel.connect()

        # does not send response if silent is true
        if silent:
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, url = None):
        try:
            if not url:
                raise VoiceExceptions.InvalidTitle("Please provide a **song title** or **link**.")

            if url.startswith('https://open.spotify.com/'):
                raise VoiceExceptions.InvalidTitle("**Spotify** playlists are not currently supported.")

            if not ctx.voice_client:
                await ctx.invoke(self.client.get_command('join'))

            if ctx.channel != channels[ctx.guild.id]:
                raise VoiceExceptions.IncorrectControlChannel(f"The player can only be controlled from **[{channels[ctx.guild.id]}]**.")
            
            player = music.get_player(guild_id=ctx.guild.id)
            if not player:
                player = music.create_player(ctx, ffmpeg_error_betterfix=True)
            if not player.now_playing():
                await player.queue(url, search=True)
                song = await player.play()
                embed = discord.Embed(colour=colors.blue, title=f"🎶 {song.name}", description=f"Now playing on {ctx.author.voice.channel.name} | by {ctx.author.mention}.")
                embed.set_thumbnail(url=song.thumbnail)
                embed.set_footer(text="If you like this song, use '$fave' to add this to your favorites!")
            else:
                song = await player.queue(url, search=True)
                embed = discord.Embed(colour=colors.blue, title=f"🎶 {song.name}", description=f"Successfully added to queue by {ctx.author.mention}.")

            await ctx.send(embed=embed)
            await ctx.message.delete()
        except:
            console_log(f"MusicPlayer: An error occurred while controlling the player in {ctx.guild.name}")

            await ctx.invoke(self.client.get_command('resetplayer'), from_error=True)
            await asyncio.sleep(1)
            await ctx.invoke(self.client.get_command('join'), silent=True)

            embed = discord.Embed(
                colour=colors.blue,
                description="The player has been **reset**. Try playing the song again."
            )

            await ctx.send(embed=embed, delete_after=10)

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        player = music.get_player(guild_id=ctx.guild.id)
        if not player:
            raise VoiceExceptions.NoActivePlayer("There is no **active player**.")

        if ctx.channel != channels[ctx.guild.id]:
            raise VoiceExceptions.IncorrectControlChannel(f"The player can only be controlled from **[{channels[ctx.guild.id].name}]**.")

        queue = player.current_queue()

        if not queue:
            raise VoiceExceptions.EmptyQueue("The queue is **empty** because there is nothing being currently played.")

        embed = discord.Embed(
            colour=colors.blue,
            title=f"🎼 {queue[0].name}",
            description=f"Now playing in {ctx.author.voice.channel.name}"
        )

        embed.set_thumbnail(
            url=queue[0].thumbnail
        )

        songs = ""
        if len(queue) <= 1:
            songs = "There are no songs in the queue."
        else:
            for index, song in enumerate(queue):
                if index == 0:
                    pass
                else:
                    songs = songs + f"\n `{index}` {song.name}"

        embed.add_field(
            name="🎶 Up Next...",
            value=songs,
            inline=False
        )

        embed.set_footer(text="If you like this song, use '$fave' to add this to your favorites!")
        await ctx.send(embed=embed)

    @commands.command()
    async def resume(self, ctx):
        if ctx.channel != channels[ctx.guild.id]:
            raise VoiceExceptions.IncorrectControlChannel(f"The player can only be controlled from **[{channels[ctx.guild.id]}]**.")

        player = music.get_player(guild_id=ctx.guild.id)
        if not player:
            raise VoiceExceptions.NoActivePlayer("There is no **active player**.")

        song =  await player.resume()
        await ctx.send(f"Resuming {song.name}")

    @commands.command()
    async def volume(self, ctx, vol):
        if ctx.channel != channels[ctx.guild.id]:
            raise VoiceExceptions.IncorrectControlChannel(f"The player can only be controlled from **[{channels[ctx.guild.id]}]**.")

        vol = float(vol)
        if vol < 0 or vol > 100:
            raise VoiceExceptions.InvalidVolume("The volume must be between **0** to **100**.")

        if not ctx.author.voice.channel:
            raise VoiceExceptions.NotConnectedToVoice("You are not connected to a **voice channel**.")

        player = music.get_player(guild_id=ctx.guild.id)
        if not player:
            raise VoiceExceptions.NoActivePlayer("There is no **active player**.")

        song, volume = await player.change_volume(vol / 100)
        await ctx.send(f"Volume set to **{volume}** for **{song.name}**.")

    @commands.command()
    async def pause(self, ctx):
        if not ctx.author.voice.channel:
            raise VoiceExceptions.NotConnectedToVoice("You are not connected to a **voice channel**.")

        if ctx.channel != channels[ctx.guild.id]:
            raise VoiceExceptions.IncorrectControlChannel(f"The player can only be controlled from **[{channels[ctx.guild.id]}]**.")

        player = music.get_player(guild_id=ctx.guild.id)
        if not player:
            raise VoiceExceptions.NoActivePlayer("There is no **active player**.")

        song = await player.pause()
        await ctx.send(f"Paused {song.name}")

    @commands.command()
    async def skip(self, ctx):
        if not ctx.author.voice:
            raise VoiceExceptions.NotConnectedToVoice("You are not connected to a **voice channel**.")

        if ctx.channel != channels[ctx.guild.id]:
            raise VoiceExceptions.IncorrectControlChannel(f"The player can only be controlled from **[{channels[ctx.guild.id]}]**.")

        player = music.get_player(guild_id=ctx.guild.id)
        if not player:
            raise VoiceExceptions.NoActivePlayer("There is no **active player**.")

        data = await player.skip(force=True)
        await ctx.send(f"Skipping 🎶 **{data[0].name}**.")

    @commands.command()
    async def remove(self, ctx, index):
        player = music.get_player(guild_id=ctx.guild.id)
        if not player:
            raise VoiceExceptions.NoActivePlayer("There is no **active player**.")

        if ctx.channel != channels[ctx.guild.id]:
            raise VoiceExceptions.IncorrectControlChannel(f"The player can only be controlled from **[{channels[ctx.guild.id]}]**.")

        try:
            song = await player.remove_from_queue(int(index))
            await ctx.send(f"Removed 🎶 **{song.name}** from queue.")
        except:
            await ctx.send("Could not remove song from the queue, perhaps the queue is empty.")

    @commands.command(aliases=['disconnect', 'dc'])
    async def leave(self, ctx):
        if not ctx.voice_client:
            raise VoiceExceptions.NotConnectedToVoice("Not connected to a **voice channel**.")

        if ctx.channel != channels[ctx.guild.id]:
            raise VoiceExceptions.IncorrectControlChannel(f"The player can only be controlled from **[{channels[ctx.guild.id]}]**.")

        embed = discord.Embed(
            colour=colors.blue,
            description=f"Disconnected from **[{ctx.voice_client.channel.name}]** and unbound from **[{channels[ctx.guild.id].name}]**."
        )

        player = music.get_player(guild_id=ctx.guild.id)
        if player:
            await player.stop()

        await ctx.send(embed=embed)
        await ctx.voice_client.disconnect()

    @commands.command()
    async def resetplayer(self, ctx, from_error=False):
        des_text = [
            "**Resetting player...**\n\nIf you are having difficulty in trying to control the **music player**, this might resolve the issue.",
            "**Resetting player...**\n\nIt seems like an error has occurred in your command. Hold on while I try to fix it for you."
        ]

        player = music.get_player(guild_id=ctx.guild.id)
        if player:
            await player.stop()

        embed = discord.Embed(
            colour=colors.red,
            description=f"{des_text[0] if not from_error else des_text[1]}"
        )

        await ctx.send(embed=embed, delete_after=30)
        await ctx.voice_client.disconnect()

    @commands.command()
    async def fave(self, ctx, *, url=None):
        if url:
            embed = discord.Embed(title="Enter song title", description="Use alphanumber characters only.")
            request = await ctx.send(embed=embed)

            try:
                msg = await self.client.wait_for(
                    'message',
                    timeout=60,
                    check=lambda message: message.author == ctx.author and message.channel == ctx.channel
                )
                if msg:
                    with open(f"playlists/{ctx.author.id}.txt", 'a') as f:
                        f.write(f"{msg.content}<url>{url}\n")

                    await request.delete()
                    await msg.delete()
                    await ctx.send(f"Added **{msg.content}** to your favorites.")
                    return
            except asyncio.TimeoutError:
                await request.delete()
                await ctx.send("Cancelling due to timeout")
                return

        player = music.get_player(guild_id=ctx.guild.id)
        if not player:
            raise VoiceExceptions.NoActivePlayer("There is no **active player**.")

        song = player.now_playing()
        if not song:
            raise VoiceExceptions.EmptyQueue("There is no **song** currently playing.")

        with open(f"playlists/{ctx.author.id}.txt", 'a') as f:
            f.write(f"{song.name}<url>{song.url}\n")

        await ctx.send(f"Added **{song.name}** to your favorites.")

    @commands.command()
    async def unfave(self, ctx, i: int):
        i = i - 1
        with open(f"playlists/{ctx.author.id}.txt", 'r') as f:
            songs = f.read().splitlines()

        playlist = ""
        for x in range(len(songs)):
            title, url = songs[x].split("<url>")
            if x == i:
                await ctx.send(f"**{title}** has been removed from your favorites.")
            else:
                playlist = playlist + f"{title}<url>{url}\n"

        with open(f"playlists/{ctx.author.id}.txt", 'w') as a:
            a.write(playlist)
        songs.pop(i)

    @commands.command(aliases=['faves'])
    async def favorites(self, ctx):
        with open(f"playlists/{ctx.author.id}.txt", 'r') as f:
            songs = f.read().splitlines()

        playlist = ""
        for i in range(len(songs)):
            title, url = songs[i].split("<url>")
            playlist = playlist + f"`{i+1}` **{title}**\n"
            playlist = playlist + f"{url}\n"

        embed = discord.Embed(colour=colors.blue, title="❤️ Liked Songs", description=playlist)
        embed.set_footer(text="Use `$unfave <id>` to remove an item from your favorites.")
        await ctx.send(embed=embed)

    @commands.command(aliases=['playfaves', 'pl', 'pf'])
    async def playliked(self, ctx, number=None):
        if not ctx.author.voice:
            raise VoiceExceptions.NotConnectedToVoice("Please connect to a voice channel first.")

        if not ctx.voice_client:
            await ctx.invoke(self.client.get_command('join'))

        if ctx.channel != channels[ctx.guild.id]:
            raise VoiceExceptions.IncorrectControlChannel(f"The player can only be controlled from **[{channels[ctx.guild.id]}]**.")

        with open(f"playlists/{ctx.author.id}.txt", 'r') as f:
            songs = f.read().splitlines()

        if number:
            try:
                number = int(number) - 1
            except:
                raise VoiceExceptions.InvalidTitle("Invalid song ID.")

            title, url = songs[number].split("<url>")
            await ctx.invoke(self.client.get_command('play'), url=url)
            return

        player = music.get_player(guild_id=ctx.guild.id)

        titles = ""
        for index, song in enumerate(songs):
            title, url = song.split("<url>")
            titles = titles + f"`{index}` {title}\n"

            if not player:
                player = music.create_player(ctx, ffmpeg_error_betterfix=True)
            if not player.now_playing():
                await player.queue(url, search=True)
                song = await player.play()
            else:
                song = await player.queue(url, search=True)

        embed = discord.Embed(colour=colors.blue, title="❤️ Playing songs that you like", description=titles)
        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(Voice(client))