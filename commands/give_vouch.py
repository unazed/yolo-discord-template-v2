import random
from .command_utils import arguments


@arguments(str, int)
async def invoke(client, message, _, amount):
    if client.customer not in message.author.roles:
        return await message.channel.send(f"<@{message.author.id}>, you must be of Customer role to vouch")
    elif amount not in (-1, 1):
        return await message.channel.send(f"<@{message.author.id}>, you can only vouch -1 or +1")
    elif not message.mentions:
        return await message.channel.send(f"<@{message.author.id}>, no user mentioned to vouch")
    user = message.mentions[0]
    vid = random.randint(1, 65535)
    if vid in client.unverified_vouches:
        vid = random.randint(1, 65535)
    if user.id not in client.unverified_vouches:
        client.unverified_vouches[user.id] = []
    client.unverified_vouches[user.id].append({
        "amount": amount,
        "id": vid
        })
    await message.channel.send(f"<@{user.id}> has to execute `{client.prefix}accept_vouch {vid}` to accept this vouch, "
                                "otherwise, they may choose to ignore it")
