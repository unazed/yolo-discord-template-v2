import aiohttp, discord
from .command_utils import arguments


@arguments(str)
async def invoke(client, message, avatar_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            try:
                await client.user.edit(avatar=await resp.read())
                await client.log("Changed avatar")
            except discord.errors.HTTPException:
                await client.log("Failed to change avatar")
                return await message.channel.send("You're changing my avatar too fast, try again later")
    await message.channel.send("My avatar should be adjusted")
