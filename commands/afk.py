from .command_utils import arguments


@arguments(status=str)
async def invoke(client, message, status=None):
    if message.author.id in client.afk_group:
        del client.afk_group[message.author.id]
        return await message.channel.send(f"<@{message.author.id}>, I've removed you from the AFK group")
    client.afk_group[message.author.id] = status or "n/a"
    await message.channel.send(f"`{message.author.name}`, I've added you to the AFK group")
