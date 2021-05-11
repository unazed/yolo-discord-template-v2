import discord
from .command_utils import (no_arguments, is_whitelisted)


@no_arguments
async def invoke(client, message):
    embeds = []
    current_embed = discord.Embed(color=0xffffff)

    dispatch_table = client.command_dispatch_table.copy()
    for command, val in [*dispatch_table.items()]:
        if (perm := val.get('restricted', None)) is not None \
                and not is_whitelisted(client, message.author, perm):
            del dispatch_table[command]

    command_octet = [ [*dispatch_table.items()][i:i+8] for i in range(0, len(dispatch_table), 8)]

    for octet in command_octet:
        for command, val in octet:
            current_embed.add_field(name=f"{command}", value=val['use'], inline=True)
        embeds.append(current_embed)
        current_embed = discord.Embed(color=0xffffff)

    for embed in embeds:
        embed.set_footer(text="Umbco 2021")
        await message.channel.send(embed=embed)
