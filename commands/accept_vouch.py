from .command_utils import arguments


@arguments(int)
async def invoke(client, message, vid):
    if message.author.id not in client.unverified_vouches \
            or not (vouches := client.unverified_vouches.get(message.author.id, [])):
        return await message.channel.send(f"<@{message.author.id}>, you don't have any unverified vouches")
    elif not any(vouch['id'] == vid for vouch in vouches):
        return await message.channel.send(f"<@{message.author.id}>, no vouches matching that ID")
    for vouch in vouches:
        if vouch['id'] == vid:
            client.database_pipe.send({
                "event": "add-vouch",
                "uid": str(message.author.id),
                "amount": vouch['amount']
                })
            return await message.channel.send(f"<@{message.author.id}>, the vouch has been accredited to your profile")
