from .command_utils import no_arguments, send_event


@no_arguments
async def invoke(client, message):
    resp = await send_event(client, "daily", {
        "uid": message.author.id
        })
    if not resp['error']:
        if (upgrade := resp.get("upgrade", None)) is None:
            return await message.channel.send(f"<@{message.author.id}>, you have been credited $50")
        elif upgrade == 1:
            await message.author.add_roles(client.golden_customer)
            await client.log(f"<@{message.author.id}> has been promoted to Golden Customer", "Rank promotion")
            return await message.channel.send(f"<@{message.author.id}>, you've been awarded the Golden Customer role!")
        elif upgrade == 2:
            await message.author.add_roles(client.notorious)
            await client.log(f"<@{message.author.id}> has been promoted to Notorious", "Rank promotion")
            return await message.channel.send(f"<@{message.author.id}>, you've been awarded the Notorious role!")
    return await message.channel.send(f"<@{message.author.id}>, try again in {resp['try-after']:.2f} hours")
