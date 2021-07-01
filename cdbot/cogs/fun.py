"""
Set of bot commands designed for general leisure.
"""
import asyncio
import textwrap
from io import BytesIO
from math import ceil
from random import choice, randint
import re
from random import randint
from string import ascii_lowercase
from typing import List
from urllib.parse import urlencode

import asyncpg
from PIL import Image, ImageDraw, ImageFont
from aiohttp import ClientSession
from discord import (
    Colour,
    Embed,
    File,
    HTTPException,
    Message,
    NotFound,
    RawReactionActionEvent,
    embeds,
)
from discord.ext.commands import (
    Bot,
    BucketType,
    Cog,
    Context,
    UserConverter,
    command,
    cooldown,
)
from discord.utils import get

from cdbot.constants import (
    CYBERDISC_ICON_URL,
    EMOJI_LETTERS,
    FAKE_ROLE_ID,
    LOCAL_DEBUGGING,
    LOGGING_CHANNEL_ID,
    NEGATIVE_EMOJI,
    NEUTRAL_EMOJI,
    POLL_CHANNEL_ID,
    POLL_WEBHOOK_ID,
    POSITIVE_EMOJI,
    PostgreSQL,
    QUOTES_BOT_ID,
    QUOTES_CHANNEL_ID,
    QUOTES_DELETION_QUOTA,
    REACT_EMOTES,
    REACT_TRIGGERS,
    ROOT_ROLE_ID,
    STAFF_ROLE_ID,
    SUDO_ROLE_ID,
    WELCOME_BOT_ID,
    WORD_MATCH_RE,
)

ascii_lowercase += " !?$()"


def convert_emoji(message: str) -> List[str]:
    """Convert a string to a list of emojis."""
    emoji_trans = list(map(iter, EMOJI_LETTERS))
    # Enumerate characters in the message

    emojified = []

    for character in message:
        index = ascii_lowercase.find(character)
        if index == -1:
            continue
        # Yield the next iteration of the letter
        try:
            emojified.append(next(emoji_trans[index]))
        except StopIteration:
            continue

    return emojified


async def emojify(message: Message, string: str):
    """Convert a string to emojis, and add those emojis to a message."""
    for emoji in convert_emoji(string.lower()):
        if emoji is not None:
            await message.add_reaction(emoji)


class FormerUser(UserConverter):
    async def convert(self, ctx, argument):
        try:
            return await ctx.bot.fetch_user(argument)
        except (NotFound, HTTPException):
            return await super().convert(ctx, argument)


class Fun(Cog):
    """
    Commands for fun!
    """

    # Embed sent when users try to ping staff
    ping_embed = (
        Embed(
            colour=0xFF0000,
            description="⚠ **Please make sure you have taken the following into account:** ",
        )
        .set_footer(
            text="To continue with the ping, react \N{THUMBS UP SIGN}, To delete this message and move on,"
            " react \N{THUMBS DOWN SIGN}"
        )
        .add_field(
            name="Cyber Discovery staff will not provide help for challenges.",
            value="If you're looking for help, feel free to ask questions in one of our topical channels.",
        )
        .add_field(
            name="Make sure you have emailed support before pinging here.",
            value="`support@joincyberdiscovery.com` are available to answer any and all questions!",
        )
    )

    def __init__(self, bot: Bot):
        self.bot = bot
        self.staff_role = None
        self.quote_channel = None
        self.fake_staff_role = None

    async def migrate_quotes(self):
        """Create and initialise the `quotes` table with user quotes."""
        async with self.bot.pool.acquire() as connection:
            await connection.execute(
                "CREATE TABLE IF NOT EXISTS quotes (quote_id bigint PRIMARY KEY, author_id bigint)"
            )
        quote_channel = self.bot.get_channel(QUOTES_CHANNEL_ID)
        async for quote in quote_channel.history(limit=None):
            await self.add_quote_to_db(quote)
        print("Quotes successfully imported.")

    @Cog.listener()
    async def on_ready(self):
        guild = self.bot.guilds[0]

        if self.staff_role is None:
            self.staff_role = guild.get_role(STAFF_ROLE_ID)

        if self.fake_staff_role is None:
            self.fake_staff_role = guild.get_role(FAKE_ROLE_ID)

        if not LOCAL_DEBUGGING:
            self.bot.pool = await asyncpg.create_pool(
                host=PostgreSQL.PGHOST,
                port=PostgreSQL.PGPORT,
                user=PostgreSQL.PGUSER,
                password=PostgreSQL.PGPASSWORD,
                database=PostgreSQL.PGDATABASE,
            )
            await self.migrate_quotes()

    @cooldown(1, 60, BucketType.user)
    @cooldown(4, 60, BucketType.channel)
    @cooldown(6, 3600, BucketType.guild)
    @Cog.listener()
    async def on_message(self, message: Message):
        # If a new quote is added, add it to the database.
        if message.channel.id == QUOTES_CHANNEL_ID and (
            message.author.id == QUOTES_BOT_ID or message.mentions is not None
        ):
            await self.add_quote_to_db(message)
            print(f"Message #{message.id} added to database.")

        if self.fake_staff_role in message.role_mentions and not message.author.bot:
            # A user has requested to ping official staff
            sent = await message.channel.send(embed=self.ping_embed, delete_after=30)
            await sent.add_reaction("\N{THUMBS UP SIGN}")
            await sent.add_reaction("\N{THUMBS DOWN SIGN}")

            def check(reaction, user):
                """Check if the reaction was valid."""
                user_is_staff = user.top_role.id in (ROOT_ROLE_ID, SUDO_ROLE_ID)
                return all(
                    (
                        user == message.author or user_is_staff,
                        str(reaction.emoji) in "\N{THUMBS UP SIGN}\N{THUMBS DOWN SIGN}",
                    )
                )

            try:
                # Get the user's reaction
                reaction, _ = await self.bot.wait_for(
                    "reaction_add", timeout=30, check=check
                )

            except asyncio.TimeoutError:
                pass

            else:
                if str(reaction) == "\N{THUMBS UP SIGN}":
                    # The user wants to continue with the ping
                    await self.staff_role.edit(mentionable=True)
                    staff_ping = Embed(
                        title="This user has requested an official staff ping!",
                        colour=0xFF0000,
                        description=message.content,
                    ).set_author(
                        name=f"{message.author.name}#{message.author.discriminator}",
                        icon_url=message.author.avatar_url,
                    )
                    # Send the embed with the user's content
                    await message.channel.send(
                        self.staff_role.mention, embed=staff_ping
                    )
                    await self.staff_role.edit(mentionable=False)
                    # Delete the original message
                    await message.delete()

            finally:
                await sent.delete()

        ctx = await self.bot.get_context(message)

        if ctx.valid or message.author.bot:
            # Don't react to valid commands or messages from bots.
            return

        # Check if the message contains a trigger
        for trigger in REACT_TRIGGERS:
            reg = WORD_MATCH_RE.format(trigger)
            if re.search(reg, message.content, re.IGNORECASE):
                to_react = REACT_TRIGGERS[trigger]
                if to_react in REACT_EMOTES:
                    for emote in to_react.split():

                        if len(emote) > 1:  # We have a string to react with
                            await emojify(message, emote)
                        else:
                            await message.add_reaction(emote)
                elif "{mention}" in to_react:
                    to_react = to_react.replace("{mention}", message.author.mention)
                    await ctx.send(to_react)
                else:
                    await ctx.send(to_react)
                return  # Only one auto-reaction per message

        # Adds waving emoji when a new user joins.
        if all(
            (
                "Welcome to the Cyber Discovery" in message.content,
                message.author.id == WELCOME_BOT_ID,
            )
        ):
            await message.add_reaction("\N{WAVING HAND SIGN}")

    @Cog.listener()
    async def on_raw_reaction_add(self, raw_reaction: RawReactionActionEvent):
        thumbs_down = "\N{THUMBS DOWN SIGN}"
        if all(
            (
                str(raw_reaction.emoji) == thumbs_down,
                raw_reaction.channel_id == QUOTES_CHANNEL_ID,
            )
        ):
            quotes_channel = self.bot.get_channel(QUOTES_CHANNEL_ID)
            logs_channel = self.bot.get_channel(LOGGING_CHANNEL_ID)
            message = await quotes_channel.fetch_message(raw_reaction.message_id)
            reaction = [
                react for react in message.reactions if str(react.emoji) == thumbs_down
            ][0]
            if reaction.count >= QUOTES_DELETION_QUOTA:
                if not LOCAL_DEBUGGING:
                    async with self.bot.pool.acquire() as connection:
                        await connection.execute(
                            "DELETE FROM quotes WHERE quote_id = $1", reaction.message.id
                        )
                mentions = ", ".join([user.mention async for user in reaction.users()])

                embed = Embed(
                    color=Colour.blue(),
                    title="Quote Deleted"
                )
                if reaction.message.embeds:
                    quote_embed = reaction.message.embeds[-1]  # Using last item has same effect as for loop
                    embed.description = quote_embed.description
                    embed.set_author(name=quote_embed.author.name, icon_url=quote_embed.author.icon_url)
                else:  # message doesn't have an embed, MUST be from a user
                    embed.description = message.content
                    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                embed.add_field(name="Deleted By", value=mentions)

                await reaction.message.delete()
                await logs_channel.send(embed=embed)

    @command()
    async def lmgtfy(self, ctx: Context, *args: str):
        """
        Returns a LMGTFY URL for a given user argument.
        """
        # Creates a lmgtfy.com url for the given query.
        request_data = {
            "q": " ".join(arg for arg in args if not arg.startswith("-")),
            "ie": int("-ie" in args),
        }
        url = "https://lmgtfy.com/?" + urlencode(request_data)

        await ctx.send(url)

        if "-d" in args:
            await ctx.message.delete()

    # Ratelimit to one use per user every minute and 4 usages per minute per channel
    @command(aliases=["emojify"])
    @cooldown(1, 60, BucketType.user)
    @cooldown(4, 60, BucketType.channel)
    async def react(self, ctx, *, message: str):
        """
        Emojifies a given string, and reacts to a previous message
        with those emojis.
        """
        if ctx.channel.id == QUOTES_CHANNEL_ID:
            await ctx.send("This command is disabled in this channel!", delete_after=10)
            return
        limit, _, output = message.partition(" ")
        if limit.isdigit():
            limit = int(limit)
        else:
            output = message
            limit = 2
        async for target in ctx.channel.history(limit=limit):
            pass
        await emojify(target, output)

    @command()
    async def xkcd(self, ctx: Context, number: str = None):
        """
        Fetches xkcd comics.
        If number is left blank, automatically fetches the latest comic.
        If number is set to '?', a random comic is fetched.
        """

        # Creates endpoint URI
        if number is None or number == "?":
            endpoint = "https://xkcd.com/info.0.json"
        else:
            endpoint = f"https://xkcd.com/{number}/info.0.json"

        # Fetches JSON data from endpoint
        async with ClientSession() as session:
            async with session.get(endpoint) as response:
                data = await response.json()

        # Updates comic number
        if number == "?":
            number = randint(1, int(data["num"]))  # noqa: B311
            endpoint = f"https://xkcd.com/{number}/info.0.json"
            async with ClientSession() as session:
                async with session.get(endpoint) as response:
                    data = await response.json()
        else:
            number = data["num"]

        # Creates date object (Sorry, but I'm too tired to use datetime.)
        date = f"{data['day']}/{data['month']}/{data['year']}"

        # Creates Rich Embed, populates it with JSON data and sends it.
        comic = Embed()
        comic.title = data["safe_title"]
        comic.set_footer(text=data["alt"])
        comic.set_image(url=data["img"])
        comic.url = f"https://xkcd.com/{number}"
        comic.set_author(
            name="xkcd",
            url="https://xkcd.com/",
            icon_url="https://xkcd.com/s/0b7742.png",
        )
        comic.add_field(name="Number:", value=number)
        comic.add_field(name="Date:", value=date)
        comic.add_field(name="Explanation:", value=f"https://explainxkcd.com/{number}")

        await ctx.send(embed=comic)

    @command()
    async def quotes(self, ctx: Context, member: FormerUser = None):
        """
        Returns a random quotation from the #quotes channel.
        A user can be specified to return a random quotation from that user.
        """
        quote_channel = self.bot.get_channel(QUOTES_CHANNEL_ID)

        async with self.bot.pool.acquire() as connection:
            if member is None:
                # fetchval() returns the first result of a query.
                message_id = await connection.fetchval(
                    "SELECT quote_id FROM quotes ORDER BY random() LIMIT 1"
                )
            else:
                message_id = await connection.fetchval(
                    "SELECT quote_id FROM quotes WHERE author_id=$1 ORDER BY random() LIMIT 1",
                    member.id,
                )

        if message_id is None:
            return await ctx.send("No quotes found.")

        message = await quote_channel.fetch_message(message_id)
        embed = None
        content = message.clean_content
        attachment_urls = [attachment.url for attachment in message.attachments]

        if message.embeds:
            embed = message.embeds[0]
        elif len(attachment_urls) == 1:
            image_url = attachment_urls.pop(0)
            embed = Embed()
            embed.set_image(url=image_url)

        for url in attachment_urls:
            content += "\n" + url

        await ctx.send(content, embed=embed)

    @command()
    async def quotecount(self, ctx: Context, member: FormerUser = None):
        """
        Returns the number of quotes in the #quotes channel.
        A user can be specified to return the number of quotes from that user.
        """
        async with self.bot.pool.acquire() as connection:
            total_quotes = await connection.fetchval("SELECT count(*) FROM quotes")

            if member is None:
                await ctx.send(f"There are {total_quotes} quotes in the database")
            else:
                user_quotes = await connection.fetchval(
                    "SELECT count(*) FROM quotes WHERE author_id=$1", member.id
                )
                await ctx.send(
                    f"There are {user_quotes} quotes from {member} in the database "
                    f"({user_quotes / total_quotes:.2%})"
                )

    @command()
    async def quoteboard(self, ctx: Context, page: int = 1):
        """Show a leaderboard of users with the most quotes."""
        users = ""
        current = 1
        start_from = (page - 1) * 10

        async with self.bot.pool.acquire() as connection:
            page_count = ceil(
                await connection.fetchval(
                    "SELECT count(DISTINCT author_id) FROM quotes"
                ) / 10
            )

            if 1 > page > page_count:
                return await ctx.send(":no_entry_sign: Invalid page number")

            for result in await connection.fetch(
                "SELECT author_id, COUNT(author_id) as quote_count FROM quotes "
                "GROUP BY author_id ORDER BY quote_count DESC LIMIT 10 OFFSET $1",
                start_from,
            ):
                author, quotes = result.values()
                users += f"{start_from + current}. <@{author}> - {quotes}\n"
                current += 1

        embed = Embed(colour=Colour(0xAE444A))
        embed.add_field(name=f"Page {page}/{page_count}", value=users)
        embed.set_author(name="Quotes Leaderboard", icon_url=CYBERDISC_ICON_URL)

        await ctx.send(embed=embed)

    async def add_quote_to_db(self, quote: Message):
        """
        Adds a quote message ID to the database, and attempts to identify the author of the quote.
        """
        author_id = None
        if quote.author.id == QUOTES_BOT_ID:
            if not quote.embeds:
                return
            embed = quote.embeds[0]
            icon_url = embed.author.icon_url
            if type(icon_url) == embeds._EmptyEmbed or "twimg" in icon_url:
                author_id = QUOTES_BOT_ID
            elif "avatars" in icon_url:
                try:
                    author_id = int(icon_url.split("/")[-2])
                except ValueError:
                    author_id = 0
            else:
                author_info = embed.author.name.split("#")
                if len(author_info) == 1:
                    author_info.append("0000")
                author = get(
                    quote.guild.members,
                    name=author_info[0],
                    discriminator=author_info[1],
                )
                author_id = author.id if author is not None else None
        else:
            author_id = quote.mentions[0].id if quote.mentions else None

        if not LOCAL_DEBUGGING:
            async with self.bot.pool.acquire() as connection:
                if author_id is not None:
                    await connection.execute(
                        "INSERT INTO quotes(quote_id, author_id) VALUES($1, $2) ON CONFLICT DO NOTHING",
                        quote.id,
                        author_id,
                    )
                else:
                    await connection.execute(
                        "INSERT INTO quotes(quote_id) VALUES($1) ON CONFLICT DO NOTHING",
                        quote.id,
                    )

            print(f"Quote ID: {quote.id} has been added to the database.")

    async def create_text_image(self, ctx: Context, person: str, text: str):
        """
        Creates an image of a given person with the specified text.
        """
        if len(text) > 100:
            return await ctx.send(
                ":no_entry_sign: Your text must be shorter than 100 characters."
            )
        drawing_text = textwrap.fill(text, 20)
        font = ImageFont.truetype("cdbot/resources/Dosis-SemiBold.ttf", 150)

        text_layer = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
        text_layer_drawing = ImageDraw.Draw(text_layer)
        text_layer_drawing.text(
            (0, 0), drawing_text, fill=(0, 0, 0), align="center", font=font
        )

        cropped_text_layer = text_layer.crop(text_layer.getbbox())
        cropped_text_layer.thumbnail((170, 110))

        image = Image.open(f"cdbot/resources/{person}SaysBlank.png")

        x = int((image.width / 5 + 20) - (cropped_text_layer.width / 2))
        y = int((image.height / 5 + 50 / 2) - (cropped_text_layer.height / 2))

        image.paste(cropped_text_layer, (x, y), cropped_text_layer)
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        await ctx.send(file=File(image_bytes, filename=f"{person}.png"))

    @command()
    async def agentj(self, ctx: Context, *, text: str):
        """
        Creates an image of Agent J with the specified text.
        """
        await self.create_text_image(ctx, "AgentJ", text)

    @command()
    async def jibhat(self, ctx: Context, *, text: str):
        """
        Creates an image of Jibhat with the specified text.
        """
        await self.create_text_image(ctx, "Jibhat", text)

    @command()
    async def agentq(self, ctx: Context, *, text: str):
        """
        Creates an image of Agent Q with the specified text.
        """
        await self.create_text_image(ctx, "AgentQ", text)

    @command()
    async def angryj(self, ctx: Context, *, text: str):
        """
        Creates an image of Angry Agent J with the specified text.
        """
        await self.create_text_image(ctx, "AngryJ", text)

    @command()
    async def angrylyne(self, ctx: Context, *, text: str):
        """
        Creates an image of Angry James Lyne with the specified text.
        """
        await self.create_text_image(ctx, "AngryLyne", text)

    @command()
    async def baldj(self, ctx: Context, *, text: str):
        """
        Creates an image of Bald Agent J with the specified text.
        """
        await self.create_text_image(ctx, "AgentJBadHairDay", text)

    @command()
    async def neveragoodtime(self, ctx: Context):
        """
        Returns the "as always it's never a good time to pop in" quote.
        """
        await ctx.send("https://cdn.discordapp.com/attachments/450107193820446722/546655387886157824/unknown.png")

    @command()
    async def tryharder(self, ctx: Context):
        """
        Returns the "Try Harder" music video.
        """
        await ctx.send("https://www.youtube.com/watch?v=t-bgRQfeW64")

    @command()
    async def hac(self, ctx: Context):
        """
        Hacks the specified user.
        """
        await ctx.send("Charging the Low Orbit Ion Canon, please stand by!")

    @command()
    async def dox(self, ctx: Context):
        """
        Doxes the specified user.
        """
        await ctx.send("OK, scraping their parent's public Facebook feed!")

    @command()
    async def theworstpunishmentwehave(self, ctx: Context):
        """
        Punishes a user.
        """
        await ctx.send("Ok, banning them from the Q&A server!")

    @command(hidden=True)
    async def suppressdissent(self, ctx: Context):
        await ctx.send("Let me call Theresa for ideas")

    @command(hidden=True)
    async def beano(self, ctx: Context):
        await ctx.send("*grumbles*")

    @command()
    async def flowchart(self, ctx: Context):
        """
        Sends the image of the challenge solving flowchart.
        """
        await ctx.send("https://cdn.discordapp.com/attachments/411573884597436416/767122366521278474/trythis.png")

    # Polls
    @command()
    async def suggest(self, ctx: Context, *, poll_question: str):
        """
        Takes a poll question and creates a poll in #polls.
        """
        confirm_msg = Embed(
            description=f":white_check_mark: Your suggestion has been sent to <#{POLL_CHANNEL_ID}> to be voted on.",
            color=0x6ABE6C)
        confirm_msg.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=confirm_msg)

        poll_webhook = await self.bot.fetch_webhook(POLL_WEBHOOK_ID)
        poll_embed = Embed(description=poll_question, color=0x37A7F3)
        poll_embed.set_footer(text=f"User ID: {ctx.message.author.id}")
        poll = await poll_webhook.send(embed=poll_embed, username=ctx.message.author.name,
                                       avatar_url=ctx.message.author.avatar_url, wait=True)
        await poll.add_reaction(POSITIVE_EMOJI)
        await poll.add_reaction(NEUTRAL_EMOJI)
        await poll.add_reaction(NEGATIVE_EMOJI)

    @command()
    async def unacceptable(self, ctx: Context):
        """
        Deem something as unacceptable.
        """
        await ctx.send("https://media1.tenor.com/images/7a2aa50ab07e6e5d61ec7ef1a45bc64f/tenor.gif?itemid=16269937")

    @command()
    async def quotebait(self, ctx: Context):
        """
        Trick someone into quoting your message.
        """
        await ctx.send("haha boobs")

    @command(hidden=True)
    async def thot(self, ctx: Context):
        await ctx.send("https://cdn.discordapp.com/attachments/543766802174443531/777203751227621466/thot.jpg")

    @command(hidden=True)
    async def subtler(self, ctx: Context):
        await ctx.send("https://media.discordapp.net/attachments/463657120441696256/703333784073797632/unknown.png")

    @command(hidden=True)
    async def subtle(self, ctx: Context):
        await ctx.send("https://cdn.discordapp.com/attachments/463657120441696256/560247422912167949/unknown.png")

    @command()
    async def whoarethecyberists(self, ctx: Context):
        """
        Returns a video explaining who the cyberists are.
        """
        await ctx.send("https://cdn.discordapp.com/attachments/458769653481865227/687638009427787791"
                       "/WhoAreTheCyberists_1.mp4")

    @command(aliases=['jibhatisnotinvolvedwiththat'], hidden=True)
    async def jibhatisnotinvolvedinthat(self, ctx: Context):
        """
        It's time to stop.
        """
        await ctx.send("https://imgur.com/CoWZ05t")

    @command()
    async def whynotboth(self, ctx: Context):
        """
        Why not?
        """
        await ctx.send("https://giphy.com/gifs/yosub-girl-taco-why-not-both-3o85xIO33l7RlmLR4I")

    @command()
    async def simples(self, ctx: Context):
        """
        It's not that hard!
        """
        await ctx.send("https://thumbs.gfycat.com/DigitalGrandBrocketdeer-small.gif")

    @command()
    async def window(self, ctx: Context):
        """
        Returns the window gif.
        """
        await ctx.send("https://media.giphy.com/media/c6DIpCp1922KQ/giphy.gif")

    @command(hidden=True, aliases=['boogie'])
    async def dance(self, ctx: Context):
        """
        Dance Tom dance!
        """
        await ctx.send("https://cdn.discordapp.com/attachments/450107193820446722/484757289476030465/ezgif.com-video"
                       "-to-gif3.gif")

    @command()
    async def thisisfine(self, ctx: Context):
        """
        There is nothing wrong here.
        """
        await ctx.send("https://media.giphy.com/media/z9AUvhAEiXOqA/giphy.gif")

    @command()
    async def inout(self, ctx: Context):
        """
        Returns the inout gif.
        """
        await ctx.send("https://media.giphy.com/media/11gC4odpiRKuha/giphy.gif")

    @command(hidden=True)
    async def zucc(self, ctx: Context):
        await ctx.send("https://tenor.com/view/zuck-zuckerberg-drink-drinks-water-gif-11631267")

    @command(hidden=True)
    async def succ(self, ctx: Context):
        await ctx.send("https://tenor.com/view/alex-jones-crying-silly-info-wars-gif-7295428")

    @command(hidden=True)
    async def shhh(self, ctx: Context):
        await ctx.send("Just ordered this to help: http://webiconspng.com/wp-content/uploads/2017/09/Shovel-PNG-Image"
                       "-95986.png")

    @command()
    async def suppressdissent(self, ctx: Context):
        """
        Suppress someone.
        """
        comments = ["It will be done my lord", "I guess we'll try the Trump approach this time",
                    "I'll get the CIA on the phone then", "Give me a minute to reread 1984"]
        await ctx.send(choice(comments))

    @command(hidden=True)
    async def murder(self, ctx: Context):
        await ctx.send("rm -rf / --no-preserve-root")


def setup(bot):
    """
    Required boilerplate for adding functionality of cog to bot.
    """
    bot.add_cog(Fun(bot))
