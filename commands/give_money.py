from .command_utils import arguments


@arguments(str, int)
async def invoke(client, message, _, amount):
    if not message.mentions:
        return await message.channel.send(f"No person was mentioned")
    user = message.mentions[0]
    if user.bot:
        return await message.channel.send(f"Can't credit bots")
    client.database_pipe.send({
        "event": "give-money",
        "uid": str(user.id),
        "amount": amount
        })
    await message.channel.send(f"<@{user.id}> has been credited ${amount}")
