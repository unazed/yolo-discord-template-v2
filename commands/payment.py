from .command_utils import arguments

@arguments(which=str)
async def invoke(client, message, which=None):
    command = client.command_dispatch_table['payment']
    paypal, btc, eth = command['paypal'], command['bitcoin'], \
                        command['eth']
    if which is None or which not in command:
        return await message.channel.send(f"PayPal: `{paypal}`\nBitcoin: `{btc}`\n"
                                          f"Ethereum: `{eth}`")
    return await message.channel.send(f"`{command[which]}`")
