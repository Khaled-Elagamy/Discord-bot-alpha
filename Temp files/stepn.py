import json
import os
import discord
from discord.ext import commands
from discord import Option
from datetime import datetime
import db_commands
from keep_alive import keep
import hashlib
import base64
import asyncio
from utils.sessions_manager import save_sessions,load_sessions,update_session
from utils.utils import format,check_channel
import utils.log_setup

logger = utils.log_setup.logging.getLogger("bot")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

help_command = commands.DefaultHelpCommand(no_category='Commands',
                                           ephemeral=True,
                                           mention_author=True)
bot = commands.Bot(command_prefix='/',
                   description="Hey there, I'm Botty (for example)!",
                   help_command=help_command,
                   intents=intents)
##Put the commands in cog to be slash ##


@bot.check
async def globally_block_dms(ctx):
    if ctx.guild is None:
        raise commands.CommandError("Attempted to execute command in DM.")
    return True
    


    


##ToDo create new voice channel on press and handel this channel and after it end get the file ready or send it and if new voice channel created create new file and make every file avaliable for only 24 hours 
# handle user joining or leaving voice channel


@bot.listen('on_message')
async def dm(message):
  if message.author == bot.user: # Don't reply to itself. Could again be client for you
        return
  if isinstance(message.channel,discord.DMChannel): #If you want this to work in a group channel, you could also check for discord.GroupChannel ////make some configuration to make random messages according to numebr of times 
        await message.channel.send("No private messages while at work")

"""
# handle command to send attendance records to admins
@bot.listen('on_message')
async def attendance(message):
  if message.content.startswith("!send_attendance"):
    if message.author.guild_permissions.administrator:
      admins = [str(admin.id) for admin in message.mentions]
      channel = message.channel_mentions[
        0] if message.channel_mentions else message.channel
      records = list(sessions.values())
      await send_records_to_admins(records, admins, channel)

#handle the attendance to admin
@bot.slash_command(
  guild_ids=[os.getenv("Guild")],
  description="Send the attendence file")
async def send_attendencse(ctx, send_option: Option(discord.TextChannel,
                                                   "Choose the channel")):
  await ctx.respond(f"The default channel has been set to {channel}.",
                 ephemeral=True)
""" 

 

@bot.command()
async def handle_command(ctx, command):
  logger.info(command)
  if command.startswith('set_prefix'):
    parts = command.split(' ')
    if len(parts) < 2:
      await ctx.send('Missing argument')
      return
    new_prefix = parts[2]
    bot.command_prefix = new_prefix
    await ctx.send('Prefix updated to: ' + new_prefix)
  elif command.startswith('set_admin'):
    new_admin = command.split(' ')[1]
    bot.admins.append(new_admin)
    await ctx.send('New admin added: ' + new_admin)
  else:
    await ctx.send('Invalid command')


@bot.command(name='hello')
async def hellocommand(ctx):
  await ctx.reply("Hello!")


@bot.user_command(brief="greet commands for help")
async def greet(ctx, user: discord.User):
  await ctx.send(f"Hello,{ctx.author.mention} says hello to {user.mention}!")


# load saved sessions from file on bot startup


#using py-cord
@bot.event
async def on_application_command_error(ctx, error):
  if isinstance(error, commands.MissingRole):
    await ctx.respond('You do not have the correct role for this command.',
                      ephemeral=True)
  elif isinstance(error, commands.MissingPermissions):
    await ctx.respond(
      'You do not have the required Permissions to Use this command\n Contact the Admin',
      ephemeral=True)
  elif isinstance(error, commands.CheckFailure):
        await ctx.respond("You do not have permission to use this command.",ephemeral=True)
  elif isinstance(error, discord.errors.NotFound):
        await ctx.respond("What you want is not found {Maybe has been removed}.",ephemeral=True)
  elif isinstance(error,commands.CommandError):
        if str(error) == "Attempted to add a bot as a bot admin.":
            await ctx.respond("You cannot add a bot as a bot admin.",ephemeral=True)
        elif str(error) == "Attempted to execute command in DM.":
            await ctx.respond("Sorry,But you cannot execute commands in DM.",ephemeral=True)
        else:
            await ctx.respond("An error occurred while adding bot admin.", ephemeral=True)
  else:
    await ctx.respond("An error occurred while processing your request.", ephemeral=True)
    logger.warning(f"Something unexpected happened {error}")
    raise error

@bot.command()
async def prfix(ctx):
	server_id = str(ctx.guild.id)
	# Set the value in Replit DB
	#await db_commands.add_value(server_id,'file_contents', file_contents)
	#data = await db_commands.get_value(server_id,'file_contents')
	logger.info(f"{data}")
	await ctx.send(f"My prefix is {bot.command_prefix}")


@bot.command()
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, prefix):
  """Command to Change the Default bot prefix"""
  bot.command_prefix = prefix
  await ctx.send(f"Prefix updated to: {prefix}")

"""
@bot.slash_command(
  guild_ids=[os.getenv("Guild")],
  description="Choose the channel to be the main admin channel")
async def set_default_channel(ctx, channel: Option(discord.TextChannel,
                                                   "Choose the channel")):
  await ctx.respond(f"The default channel has been set to {channel}.",
                    ephemeral=True)
"""

      
@bot.event
async def on_ready():
  logger.info(f"Logged in as {bot.user.name}")
  


bot.load_extension('cogs.owner')
bot.load_extension('cogs.admin')
bot.load_extension('cogs.on_voice_update')
bot.load_extension('cogs.create_channel')
bot.load_extension('cogs.attendance')
bot.run(os.getenv("Token"))
