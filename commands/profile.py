import time
import discord
from .command_utils import no_arguments, send_event


@no_arguments
async def invoke(client, message):
    resp = await send_event(client, "query", {"uid": message.author.id})
    embed = discord.Embed(title="Profile", description="View balance, vouches, daily reclaim, etc.", color=0xaa007f)
    
    embed.set_author(name=f"{message.author.name}", icon_url=message.author.avatar_url)
    embed.add_field(name="Balance", value=f"${resp['data']['balance']}", inline=True)
    embed.add_field(name="Vouches", value=resp['data'].get("vouches", ), inline=True)

    daily_claim_timestamp = 60*60*24 - (time.time() - resp['data']['last-daily'])
    if daily_claim_timestamp <= 0:
        daily_claim_timestamp = "now"
    else:
        daily_claim_timestamp = f"{daily_claim_timestamp/(60*60):.2f} hours"

    embed.add_field(name="Daily reclaim", value=daily_claim_timestamp)

    embed.set_footer(text="Umbco 2021")
    await message.channel.send(embed=embed)
