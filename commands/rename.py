import asyncio
import discord
from .command_utils import arguments


@arguments(str)
async def invoke(client, message, name):
    try:
        before = client.user.name
        task = asyncio.ensure_future(client.user.edit(username=name))
        await asyncio.sleep(2)
        if client.user.name == before:
            await client.log(f"Failed to change name to {name!r}")
            return await message.channel.send(f"Name changing failed, likely too many requests sent; try again later.")
    except discord.errors.HTTPException:
        return await message.channel.send(f"Too many users have this name, please try another.")
    await client.log(f"Name changed from {before!r} to {name!r}")
    await message.channel.send(f"My name is now `{name}`")
