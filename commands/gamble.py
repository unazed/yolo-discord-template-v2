import asyncio
import random

from .command_utils import arguments, send_event


EMOJIS = (":banana:", ":apple:", ":pear:", ":tomato:")


@arguments(int)
async def invoke(client, message, amount):
    user = (await send_event(client, "query", {"uid": str(message.author.id)}))['data']
    if user['balance'] < amount:
        return await message.channel.send(f"<@{message.author.id}>, you have too little money to place a bet this large")
    elif amount <= 0:
        return await message.channel.send(f"<@{message.author.id}>, your input amount must be positive")
    client.database_pipe.send({
        "event": "give-money",
        "uid": str(message.author.id),
        "amount": -amount
        })
    message = await message.channel.send("Spinning the slot machine")
    await asyncio.sleep(1)
    for _ in range(3):
        random_sample = random.sample(EMOJIS, 3)
        await message.edit(content="Spinning the slot machine\n"
                                +  ' '.join(random.sample(EMOJIS, 3)))
        await asyncio.sleep(0.5)
    if random_sample == random_sample[0] * 3:
        client.database_pipe.send({
            "event": "give-money",
            "uid": str(message.author.id),
            "amount": amount * 10
            })
        return await message.channel.send(f"<@{message.author.id}>, you've hit the jackpot! ${amount*10} has been credited to your account")
    return await message.channel.send(f"<@{message.author.id}>, unlucky, try again next time :smile:")
