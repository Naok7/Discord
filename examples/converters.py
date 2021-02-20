# This example requires the 'members' privileged intent to use the Member converter.

import typing

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot("!", intents=intents)


@bot.command()
async def userinfo(ctx: commands.Context, user: discord.User):
    # In the command signature above, you can see that the `user`
    # parameter is typehinted to `discord.User`. This means that
    # during command invocation we will attempt to convert
    # the value passed as `user` to a `discord.User` instance.

    # NOTE: typehinting acts as a converter within discord.py only.
    # In standard Python it is use for documentation and IDE assistance purposes.

    # If the conversion is successful we will have a User instance
    # and can do the following:
    await ctx.send(user.mention)

@userinfo.error
async def userinfo_error(ctx: commands.Context, error: Exception):
    # if the conversion above fails for any reason, it will raise `commands.errors.BadArgument`
    # so we handle this in this error handler:
    if isinstance(error, commands.BadArgument):
        return await ctx.send("Couldn't find that user.")
    else:
        # Raise the error to the global error handler
        raise error

# Manual use of converters will follow:
@bot.command()
async def channel_or_member(ctx: commands.Context, argument: str):
    # NOTE: command parameters are `str` type by default, the typehint above is just for completeness' sake.

    # If you use this pattern commonly, consider making a Custom Converter.
    # See: https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#advanced-converters

    # If for any reason you have an ID, but it may be of one of more
    # items, like a TextChannel or Member, you can manually call the converters
    # like the following:
    member_converter = commands.MemberConverter()
    try:
        # Try and convert to a Member instance.
        member = await member_converter.convert(ctx, argument)
    except commands.MemberNotFound:
        # Could not convert to a Member instance.
        pass
    else:
        # We have our `member` so lets return here.
        return await ctx.send("Member found: {}".format(member))

    # Do the same for TextChannel...
    textchannel_converter = commands.TextChannelConverter()
    try:
        channel = await textchannel_converter.convert(ctx, argument)
    except commands.ChannelNotFound:
        pass
    else:
        return await ctx.send("Channel found: {}".format(channel))

    await ctx.send("No member or channel matching this ID was found.")

@bot.command()
async def alternative_channel_or_member(ctx: commands.Context, target: typing.Union[discord.Member, discord.TextChannel]):
    # This command signature utilises the `typing.Union` typehint.
    # The `commands` framework attempts a conversion of each type in this Union *in order*.
    # So, it will attempt to convert whatever is passed to `target` to a `discord.User` instance.
    # If that fails, it will attempt to convert it to a `discord.TextChannel` instance.
    # See: https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#typing-union
    # NOTE: If a Union typehint converter fails it will raise `commands.errors.BadUnionArgument`
    # instead of `commands.errors.BadArgument`.

    # This is a more user-friendly alternative to the previous command.

    # Let's check the type we actually got...
    if isinstance(target, discord.User):
        return await ctx.send("User found: {}".format(target.mention))
    elif isinstance(target, discord.TextChannel): # this could be an `else` but for completeness' sake.
        return await ctx.send("Channel found: {}".format(target.mention))

# Built-in type converters.
@bot.command()
async def trial_converter(ctx: commands.Context, number: int, maybe: bool):
    # We want an `int` and a `bool` parameter here.
    # `bool` is a slightly special case, as shown here:
    # See: https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#bool

    await ctx.send("Number: {} -- Bool: {}.".format(number, maybe))

bot.run("token")
