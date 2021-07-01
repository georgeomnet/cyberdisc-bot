import os

from discord.ext import commands
from discord.ext.commands import Bot, BucketType, Cog, command, Context, cooldown
from git import Repo

from cdbot.constants import BOT_COMMAND_CHANNELS, JOINABLE_ROLES_IDS, WELCOME_CHANNEL_ID, WELCOME_MESSAGE

path = os.path.dirname(os.path.abspath(__file__))
path = "/".join(path.split("/")[:-2])

repo = Repo(path)
latest = repo.commit()


class General(Cog):
    """
    General Purpose Commands
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    def in_commands_channel(ctx):
        return ctx.channel.id in BOT_COMMAND_CHANNELS

    @Cog.listener()
    async def on_ready(self):
        print("Logged in as")
        print(self.bot.user.name)
        print(self.bot.user.id)
        print("------")
        message, *_ = latest.message.partition("\n")
        link = f"{next(repo.remote().urls)}/commit/{latest}"
        date = latest.authored_datetime.strftime("**%x** at **%X**")
        self.bot.log.info(
            "CyberDiscovery bot is now logged in.\n"
            f"Latest commit: **[{message}]({link})**"
            f"\nAuthor: **{latest.author}** on {date}"
        )

    @Cog.listener()
    async def on_member_join(self, member):
        join_msg_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        join_msg = await join_msg_channel.send(f"{member.mention}, {WELCOME_MESSAGE}")
        await join_msg.add_reaction('👋')

    @Cog.listener()
    async def on_member_remove(self, member):
        if member not in [ban.user for ban in await member.guild.bans()]:
            leave_msg_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
            await leave_msg_channel.send(f"**{member}** just left **Cyber Discovery**. Bye bye **{member}**...")

    @Cog.listener()
    async def on_member_ban(self, guild, user):
        ban_msg_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        await ban_msg_channel.send(f"**{user}** was banned...")

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        # Try provide some user feedback instead of logging all errors.

        if isinstance(error, commands.CommandNotFound):
            return  # No need to log unfound commands anywhere or return feedback

        if isinstance(error, commands.MissingRequiredArgument):
            # Missing arguments are likely human error so do not need logging
            parameter_name = error.param.name
            return await ctx.send(
                f"\N{NO ENTRY SIGN} Required argument {parameter_name} was missing."
            )
        elif isinstance(error, commands.CheckFailure):
            return await ctx.send(
                "\N{NO ENTRY SIGN} You do not have permission to use that command or it is disallowed in this channel."
            )
        elif isinstance(error, commands.CommandOnCooldown):
            retry_after = round(error.retry_after)
            return await ctx.send(
                f"\N{HOURGLASS} Command is on cooldown, try again after {retry_after} seconds."
            )

        # All errors below this need reporting and so do not return

        if isinstance(error, commands.ArgumentParsingError):
            # Provide feedback & report error
            await ctx.send(
                "\N{NO ENTRY SIGN} An issue occurred while attempting to parse an argument."
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("\N{NO ENTRY SIGN} Conversion of an argument failed.")
        else:
            await ctx.send(
                "\N{NO ENTRY SIGN} An error occured during execution, the error has been reported."
            )

        extra_context = {
            "discord_info": {
                "Channel": ctx.channel.mention,
                "User": ctx.author.mention,
                "Command": ctx.message.content,
            }
        }

        if ctx.guild is not None:
            # We are NOT in a DM
            extra_context["discord_info"]["Message"] = (
                f"[{ctx.message.id}](https://discordapp.com/channels/"
                f"{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id})"
            )
        else:
            extra_context["discord_info"]["Message"] = f"{ctx.message.id} (DM)"

        self.bot.log.exception(error, extra=extra_context)

    @command(aliases=["rank", "role"])
    @cooldown(1, 10, BucketType.user)
    @commands.check(in_commands_channel)
    async def join(self, ctx: Context, *, rank: str):
        """
        Join a rank.
        """
        try:
            new_role = next((role for role in ctx.guild.roles if role.name.lower() == rank.lower()), None)
            if new_role.id in sum(JOINABLE_ROLES_IDS, []):
                if new_role in ctx.author.roles:
                    await ctx.author.remove_roles(new_role, reason="Rank")
                    await ctx.send(f"{ctx.author.mention} You left **{new_role}**.")
                    return

                for role_ids in JOINABLE_ROLES_IDS:
                    if new_role.id in role_ids and (
                            (old_role := next(iter(set(role_ids) & set(role.id for role in ctx.author.roles)), False))):
                        old_role = ctx.guild.get_role(old_role)
                        await ctx.author.remove_roles(old_role, reason="Ranks")
                        await ctx.author.add_roles(new_role, reason="Ranks")
                        await ctx.send(f"{ctx.author.mention} You left **{old_role}** and joined **{new_role}**")
                        return

                await ctx.author.add_roles(new_role, reason="Ranks")
                await ctx.send(f"{ctx.author.mention} You joined **{new_role}**.")

            else:
                raise AttributeError
        except AttributeError:
            await ctx.send("That rank does not exist.")

    @command()
    async def bbcnews(self, ctx: Context):
        """
        Returns a link to BBC News.
        """
        await ctx.send("https://www.bbc.co.uk/iplayer/live/bbcnews")

    @command()
    async def skynews(self, ctx: Context):
        """
        Returns a link to Sky News.
        """
        await ctx.send("https://www.youtube.com/watch?v=9Auq9mYxFEE")

    @command()
    async def tos(self, ctx: Context):
        """
        Returns a link to discord's terms of service.
        """
        await ctx.send("https://www.discord.com/terms")

def setup(bot):
    bot.add_cog(General(bot))
