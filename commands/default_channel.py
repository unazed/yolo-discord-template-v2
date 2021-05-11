from .command_utils import no_arguments


@no_arguments
async def invoke(client, message):
    channel = message.channel
    client.default_channel = channel
    client.primary_server = channel.guild
    await client.insert_database()
    await channel.send("The bot has been temporarily configured to treat this as the default "
                       "channel, better yet, modify `config.txt`.")
