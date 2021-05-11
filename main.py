from collections import Counter
import asyncio
import discord
import time, inspect
import importlib
import multiprocessing
import string
from format_parser.fmtparser import loadfile
from dbms import database


_print = print
def print(*args, **kwargs): 
    prev_fn = inspect.currentframe().f_back.f_code.co_name
    _print(f"[{time.strftime('%H:%M:%S')}] [UmbcoDiscordBot] [{prev_fn}]",
           *args, **kwargs)


def dbprint(*args, **kwargs): 
    prev_fn = inspect.currentframe().f_back.f_code.co_name
    _print(f"[{time.strftime('%H:%M:%S')}] [DatabasePipe] [{prev_fn}]",
           *args, **kwargs)


def parse_command(command):
    index, tokens = 0, []
    current_token = ""
    is_parsing_string = False

    while index != len(command):
        current_char = command[index]
        if is_parsing_string:
            if current_char == is_parsing_string:
                tokens.append(current_token)
                current_token = ""
                is_parsing_string = False
            else:
                current_token += current_char
        elif current_char in string.whitespace:
            if current_token:
                tokens.append(current_token)
                current_token = ""
        elif current_char in '"\'':
            is_parsing_string = current_char
        else:
            current_token += current_char
        index += 1

    if is_parsing_string:
        return False
    elif current_token:
        return tokens + [current_token]
    return tokens


class UmbcoDiscordBot(discord.Client):
    def __init__(self, config, command_dispatch_table):
        intents = discord.Intents.default()
        intents.members = True
        super(UmbcoDiscordBot, self).__init__(intents=intents)

        self.config                 = config
        self.command_dispatch_table = command_dispatch_table
        self.prefix                 = self.config['bot_configuration']['prefix']

        self.golden_customer    = None
        self.notorious          = None
        self.customer           = None
    
        self.default_channel    = None
        self.log_channel        = None
        self.primary_server     = None

        self.afk_group          = {}
        self.command_cache      = {}

        self.channel_intake     = {}
        self.channel_top_user   = {}
        self.slowmode_lock      = {}
        self.spam_counter       = Counter()

        self.unverified_vouches = {}

        self.database_pipe, slave = multiprocessing.Pipe()
        self.database_proc = multiprocessing.Process(target=database.poll_indefinitely, args=(
            slave, self.config['database_configuration']['directory'] 
            ))

        self.database_proc.start()
        if self.database_pipe.poll(3) is None:
            raise IOError("database process didn't send acknowledgement")
        state = self.database_pipe.recv()
        if state['error']:
            raise IOError(state['message'])
        dbprint(state['message'])

    async def log(self, message, title=None):
        if self.log_channel:
            embed = discord.Embed(title=title or "Log message", description=f"{message}", color=0xaa0000)
            embed.set_author(name="Umbco", icon_url=self.user.avatar_url)
            embed.set_footer(text=f"{time.strftime('%H:%M:%S')}")
            await self.log_channel.send(embed=embed)

    async def insert_database(self):
        if self.primary_server is None:
            print("tried to update database, but primary server isn't set")
            return

        members = {}
        for member in await self.primary_server.chunk():
            if member.bot:
                continue
            members[member.id] = {
                    "roles": [role.id for role in member.roles],
                    "username": member.name
                }
        self.database_pipe.send({
            "event": "update",
            "data": members
            })
        await self.log("Saved database to disk")

    async def on_message_delete(self, message):
        await self.log(f"`{message.content}` -- <@{message.author.id}>", "Message deleted")

    async def on_message_edit(self, before, after):
        await self.log(f"`{before.content}` -> `{after.content}` -- <@{before.author.id}>", "Message edited")

    async def on_ready(self):
        self.default_channel = self.get_channel(int(self.config['channel_configuration']['default_channel']))
        self.log_channel = self.get_channel(int(self.config['channel_configuration']['log_channel']))
        self.primary_server = self.default_channel.guild

        if self.default_channel is not None:
            self.golden_customer    = self.primary_server.get_role(int(self.config['specific_role_permissions']['Golden Customer']))
            self.notorious          = self.primary_server.get_role(int(self.config['specific_role_permissions']['Notorious']))
            self.customer           = self.primary_server.get_role(int(self.config['specific_role_permissions']['Customer']))
            self.member             = self.primary_server.get_role(int(self.config['specific_role_permissions']['Member']))

            await self.insert_database()
            await self.default_channel.send(f"Umbco bot is up & running, type `{self.config['bot_configuration']['prefix']}help` "
                                             "to get started :smile:")
        else:
            print("default channel not found, database services won't be available until you run "
                 f"`{self.prefix}set_default_channel` in your main channel")

        if self.log_channel is None:
            print("log channel not found, no logging will be available until you run "
                 f"`{self.prefix}set_log_channel`")

        print("configuration loaded, bot is ready")
        await self.log("Bot is ready for execution")

    async def monitor_intake(self, channel):
        if channel.id not in self.channel_intake:
            self.channel_intake[channel.id] = {
                    "last_msg": time.time(),
                    "dt": 1
                    }
            return False

        user_count = Counter()
        async for message in channel.history(limit=10):
            if message.author.bot:
                continue
            user_count[message.author.id] += 1
        top_id, amount = user_count.most_common()[0]

        if channel.id not in self.channel_top_user:
            self.channel_top_user[channel.id] = {
                    "user": None,
                    "usage": None
                    }

        total_messages = sum(user_count.values())

        self.channel_top_user[channel.id].update({
            "user": self.primary_server.get_member(top_id),
            "usage": amount/total_messages
            })

        statistics = self.channel_intake[channel.id]

        statistics.update({
            "last_msg": time.time(),
            "dt": time.time() - statistics['last_msg'],
            "avg": (time.time() - statistics['last_msg'] + statistics['dt'])**1.25
            })
        
        if statistics['avg'] < self.config['slowmode_parameters']['avg_threshold']:
            if channel.id in self.slowmode_lock:
                return
            self.slowmode_lock[channel.id] = True
            if self.spam_counter[channel.id] == 2:
                await channel.send("Locking channel due to repeated spam")
                asyncio.create_task(self.lock_channel_for_period(channel,
                    self.config['channel_configuration']['autolock_period']))
                self.spam_counter[channel.id] = 0
                return True
            self.spam_counter[channel.id] += 1
            await channel.edit(slowmode_delay=self.config['slowmode_parameters']['cooldown_period'])
            asyncio.create_task(self.slowmode_stop(channel))
            asyncio.create_task(self.mute_for_period(self.primary_server.get_member(top_id),
                self.config['channel_configuration']['automute_period']))
            await channel.send(f"Possible spam detected, slowmode turned on. <@{top_id}> has been muted "
                               f"as he held {amount/total_messages * 100:.2f}% of the past {total_messages} messages")

            return True
        return False

    async def lock_channel_for_period(self, channel, time_):
        locked_roles = (self.member, self.golden_customer, self.notorious)
        overwrites = [*map(channel.overwrites_for, locked_roles)]
        for overwrite in overwrites:
            overwrite.send_messages = False
        for role in locked_roles:
            await channel.set_permissions(role, overwrite=overwrite)
        await asyncio.sleep(time_)
        for overwrite in overwrites:
            overwrite.send_messages = True
        for role in locked_roles:
            await channel.set_permissions(role, overwrite=overwrite)
        del self.slowmode_lock[channel.id]

    async def slowmode_stop(self, channel):
        await asyncio.sleep(self.config['slowmode_parameters']['cooldown_period'])
        await channel.edit(slowmode_delay=0)
        await channel.send("Slowmode has been disabled")
        del self.slowmode_lock[channel.id]

    async def mute_for_period(self, user, time_):
        overwrites = [channel.overwrites_for(user) for channel in self.primary_server.text_channels]
        for overwrite in overwrites:
            overwrite.send_messages = False
        for channel in self.primary_server.text_channels:
            await channel.set_permissions(user, overwrite=overwrite)
        await asyncio.sleep(time_)
        for overwrite in overwrites:
            overwrite.send_messages = True
        for channel in self.primary_server.text_channels:
            await channel.set_permissions(user, overwrite=overwrite)

    async def autorole_after_period(self, member, role, period):
        await asyncio.sleep(period)
        await member.give_roles(role)

    async def on_member_join(self, member):
        asyncio.create_task(self.autorole_after_period(
            member, self.member, self.config['channel_configuration']['autorole_after']
            ))
        await self.default_channel.send(f"<@{member.id}> has joined, welcome :smile:")

    async def on_message(self, message):
        author, content, channel = message.author, message.content, message.channel

        if author.bot or self.primary_server is None:
            return
        else:
            await self.monitor_intake(channel)
        
        for mention in message.mentions:
            if (status := self.afk_group.get(mention.id, None)) is not None:
                await message.delete()
                return await channel.send(f"`{mention.name}` is AFK: {status!r}")
        
        if not content.startswith(self.prefix):
            return

        tokens = parse_command(content[len(self.prefix):])
        if tokens is False:
            return await channel.send(f"<@{author.id}>, you've missed a quotation mark in your arguments")

        command, *args = tokens
        if (command := self.command_dispatch_table.get(command, None)) is None:
            return
        elif (restricted := command.get("restricted", None)) is not None:
            for role in author.roles:
                if str(role.id) in self.config['specific_role_permissions']:
                    break
            else:
                await self.log(f"<@{author.id}> tried to execute a privileged command, {command!r}")
                return await channel.send(f"<@{author.id}>, you don't have sufficient permissions to execute this command")
        command = command['file']
        try:
            if command not in self.command_cache:
                print(f"admitting command module {command!r} into cache")
                self.command_cache[command] = importlib.import_module(self.config['bot_configuration']['root_command_directory'].strip("/") + f".{command[:-3]}")
            else:
                self.command_cache[command] = importlib.reload(self.command_cache[command])
        except ModuleNotFoundError:
            return await channel.send(f"<@{author.id}>, an internal error occurred. The command you're attempting to run "
                                       "is unimplemented.")
        await self.command_cache[command].invoke(self, message, args)


if __name__ == "__main__":
    config = loadfile("config.txt")
    command_dispatch_table = loadfile("command-dispatch-table.txt", global_=False)
    bot = UmbcoDiscordBot(config, command_dispatch_table)
    bot.run(config['bot_info']['token'])
