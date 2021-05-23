from .command_utils import no_arguments


@no_arguments
async def invoke(client, message):
    client.log_channel = message.channel
    await client.log_channel.send("This has been configured as the log channel, better yet, "
                                  "modify 'config.txt' for a permanent solution")
