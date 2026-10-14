import os
import time
import logging
import asyncio
import traceback
import sys
import random
import vibes
from pathlib import Path
from vibes import Client, commands
from vibes.commands import (Context, CommandNotFound, BadArgument, MissingArguments, CommandError, NoPermission, OnCooldown, Cooldown)
from data import helper, drekbase

for d in ['logs', 'extensions']:
    if not os.path.exists(d):
        os.mkdir(d)


fmt = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(filename)s: %(message)s",
    datefmt="%m/%d %H:%M:%S",
)
fmt.converter = time.localtime


sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(fmt)

fh = logging.FileHandler(
    f"logs/{helper.system.started_at.strftime(helper.system.logfile_format)}.log",
    mode="a",
)
fh.setFormatter(fmt)

# Set global logger level to DEBUG to debug our own code
logging.basicConfig(level=logging.DEBUG, handlers=[fh, sh])

# Mute noisy third party libraries

for logger_name in ("matplotlib", "PIL", "httpx", "httpcore", "asyncio", "websockets", "aiomysql"):
    logging.getLogger(logger_name).setLevel(logging.WARNING)



TOKEN: str = os.getenv('VIBES_BOT_TOKEN')
client = Client(token=helper.getenv('VIBES_BOT_TOKEN'), prefix=helper.bot.prefix)


# Building
# Do not create the file ".drek124". This file is on my computer in order to build the repo's elements such as "env.txt"
if os.path.exists('.drek124'):
    _to_add = ["--- REQUIRED ENVIRONMENT VARIABLES ---"]
    with open('.env', 'r', encoding='utf-8') as f:
        envcontent = f.read().split('\n')

    for var in envcontent:
        if var.startswith('#') and '=' not in var:
            _to_add.append(var)

        elif '=' in var:
            _to_add.append(var.split('=')[0])

    with open('env.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(_to_add))


async def main():
    logging.info("Loading DB pool...")
    await drekbase.load_pool()
    # Loading extensions
    ext_folder = Path('extensions')
    for folder in [item for item in ext_folder.iterdir() if not item.is_file()] + [ext_folder]:
        for file in [item for item in folder.iterdir() if item.is_file() and item.name.endswith('.py') and not item.name.startswith('_')]:
            await client.load_extension(f"{ext_folder.name}.{folder.name}.{file.name[:-3]}")
            logging.info(f"Extension {folder.name}.{file.name[:-3]} has been loaded")
        

        
    await client.start()




@client.event()
async def on_connect():
    print(f"--- Logged in as {client.user} ---")

    logging.info('Syncing app commands...')
    synced = await client.sync_commands()
    logging.info(f'Synced {len(synced)} app commands')
    

@commands.command('time', cooldown=Cooldown(30, 1, Cooldown.CHAT))
async def streamtime(ctx: Context):
    total_seconds = int(round(ctx.stream.duration))
    
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or not parts: # Always show seconds unless everything is 0
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    # Join nicely (e.g., "2 hours and 3 seconds" or "1 hour, 15 minutes, and 4 seconds")
    if len(parts) > 1:
        result = ", ".join(parts[:-1]) + f", and {parts[-1]}"
    else:
        result = parts[0]

    await ctx.message.reply(f"{ctx.stream.channel} has been live for {result}")


@client.event()
async def on_stream_online(stream: vibes.Stream):
    print(f"{stream.channel} just went live! {stream.title}")

@client.event()
async def on_stream_offline(stream: vibes.Stream):
    print(f"{stream.channel} stopped streaming after {round(stream.duration/60, 1)}mins! {stream.title}")
 
@client.event()
async def on_viewer_join(stream: vibes.Stream, viewer: vibes.User):
    print(f"{viewer} is now watching {stream.title}")

@client.event()
async def on_viewer_leave(stream: vibes.Stream, viewer: vibes.User):
    print(f"{viewer} is no longer watching {stream.title}")

@client.event()
async def on_new_follower(user: vibes.User, viewer: vibes.User):
    print(f"{viewer} just followed {user}")

@client.event()
async def on_stream_like(stream: vibes.Stream, viewer: vibes.User):
    print(f"{viewer} just liked {stream.title}")

@client.event()
async def on_command_error(e: CommandError):
    if isinstance(e, CommandError):
        ctx: Context = e.context

        if isinstance(e, CommandNotFound):
            await ctx.message.reply("Command not found!")

        elif isinstance(e, BadArgument):
            await ctx.message.reply(f"Invalid argument, in \"{e.parameter.name}\"")

        elif isinstance(e, MissingArguments):
            await ctx.message.reply("Missing required argument(s)")

        elif isinstance(e, NoPermission):
            await ctx.message.reply(f"No permission! You must have {ctx.command.required_role.name.capitalize()} role.")

        elif isinstance(e, OnCooldown):
            await ctx.message.reply(f"You can only use this command {e.cooldown.max_uses} times per {e.cooldown.period}s. {round(e.available_after, 2)}s left.")
        else:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
    else:
        print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

@client.event()
async def on_donation(donation: vibes.Donation):
    print(f"""{donation.user} donated {donation.amount} {donation.currency} to {donation.streamer}!
    "{donation.message}"
    The donation is equivalent to ${donation.amount_usd} 
    """)

@client.event()
async def on_message(message: vibes.Message):
    if message.content.startswith(client.prefix):
        await client.process_commands(message)

    print(f"""[{message.stream.title}] {message.author}: "{message.content}" """)

@client.event()
async def on_message_delete(message: vibes.Message): 
    print(f"""A message by {message.author} has been deleted!""")







asyncio.run(main())