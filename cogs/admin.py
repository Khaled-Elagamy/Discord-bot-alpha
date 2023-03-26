import discord
from discord.ext import commands
from discord import Option
from replit import db
import utils.db_commands as db_commands
import shutil
import hashlib

import utils.log_setup

logger = utils.log_setup.logging.getLogger("bot")

# Decorator that adds the given decorator to all methods in a class
def add_decorator_to_methods(decorator):
    def decorate(cls):
        for name, method in vars(cls).items():
            if callable(method) and not name.startswith("_"):
                setattr(cls, name, decorator(method))
        return cls
    return decorate
  
"""
def is_admin():
    try:
      async def check(ctx):
          server_id = str(ctx.guild.id)
          user_id = ctx.author.id
          data= await db_commands.get_values(server_id,"admins")
          if data:
              if isinstance(data, list):
                  admin_ids = [int(admin_id) for admin_id in data]
                  if user_id in admin_ids:
                      return True
                  else:
                      raise commands.MissingPermissions()
          else:
              await ctx.respond(f"{ctx.author.mention} you are not an admin for this bot ")
       
      return commands.check(check)
    except Exception as e:
      return e
"""
#Print all the admins of the bot     
async def get_admins(ctx,condition):
    server_id = str(ctx.guild.id)
    data= await db_commands.get_values(server_id,"admins")
    if data:
        if isinstance(data, list):
            admin_names = ", ".join(member.mention for member in ctx.guild.members if str(member.id) in data)
            if condition == "1":
                return f"\n The new admins for this bot are: {admin_names}."
            else:
                return f"\n The admins for this bot are {admin_names}."
        else:
            if condition == "1":
                  return f"\n No more admins registered for this bot."
            else:
                  return "\n No admins registered yet."
    else:
        return "Server data not found."
      
    #Print all the channels of the bot       
async def get_channels(ctx,condition):
    server_id = str(ctx.guild.id)
    data= await db_commands.get_values(server_id,"admin_channels")
    if data:
        if isinstance(data, list):
            channels_name = ", ".join(channel.mention for channel in ctx.guild.channels if str(channel.id) in data)
            if condition == "1":
                return f"\n The new channels for this bot are {channels_name}."
            else:
                return f"\n The channels for this bot are {channels_name}."
        else:
            if condition == "1":
                return f"\n No more channels registered for this bot."
            else:
                return "\n No channels registered yet."
    else:
        return "\n Server data not found."

      
@add_decorator_to_methods(discord.default_permissions(move_members=True))
#@add_decorator_to_methods(is_admin())
class Admin(commands.Cog): # create a class for our cog that inherits from commands.Cog

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot

    @commands.Cog.listener() 
    async def on_guild_join(self,guild):
        db_commands.server_check(str(guild.id))
        logger.info(f"The server has been made for {guild.name}")
        default_channel = guild.system_channel
        if default_channel is not None:
            await default_channel.send('Thanks for adding me to your server!')

    @commands.Cog.listener() 
    async def on_command_error(self,ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You are not a server admin to use this command.")

    #set the inviter of the bot     
    @discord.slash_command()
    async def set_owner(self,ctx):
        """Set the bot owner's user ID in the database"""
        server_id = str(ctx.guild.id)
        inviter = str(ctx.author.name)
        data = await db_commands.add_value(server_id, "inviter", inviter)
        if data:
            if isinstance(data, bool):
                await ctx.respond("Bot inviter's registered succesfully,You can use the commands now.",ephemeral=True)
            else:
              await ctx.respond(f"Bot inviter {data} registered already,Cant use it again.",ephemeral=True) 
        else:
           await ctx.respond(f"Problem occured,Try again later.",ephemeral=True) 
  
    #Set the listening_voice_channel when join this it create new temp channel
    @discord.slash_command(description="Choose the channel to set as listening_voice_channel")
    async def set_listening_channel(self,ctx, channel: discord.VoiceChannel):
        server_id = str(ctx.guild.id)
        await channel.edit(user_limit=1)
        if await db_commands.add_value(server_id,"listening_voice_channel",(str(channel.id))):
            await ctx.respond(f"{channel.mention} has been set as the listening_voice_channel.",ephemeral=True)
          
    #Remove the listening_voice_channel when join this it create new temp channel
    @discord.slash_command(description="Remove the channel from being a listening_voice_channel")
    async def remove_listening_channel(self,ctx):
        server_id = str(ctx.guild.id)
        channel_id = await db_commands.get_values(server_id, "listening_voice_channel")
        if channel_id and channel_id is not None:
            voice_channel = self.bot.get_channel(int(channel_id))
            if voice_channel is not None and isinstance(voice_channel, discord.VoiceChannel):
                await voice_channel.edit(user_limit=0)  # Set the user limit to infinity
            await db_commands.empty_string(server_id, "listening_voice_channel")
            await ctx.respond(f"{voice_channel.mention} has been removed from being a listening_voice_channel.", ephemeral=True)
        else:
            await ctx.respond("There is no channel set as the listening_voice_channel.", ephemeral=True)      
          
    
    #Clear messages
    @discord.slash_command(description="Delete last number of messages")
    async def clear_messages(self,ctx,number:Option(int, "Number of messages to be deleted")):
        channel = ctx.channel
        messages = []
        async for message in channel.history(limit=number):
            messages.append(message)
        await ctx.respond(f"Last {number} messages have been removed.",delete_after=2)
        await channel.delete_messages(messages)

    @discord.slash_command()
    async def set_bot_admin(self,ctx, member: discord.Member):
        if member.bot:
            raise commands.CommandError("Attempted to add a bot as a bot admin.")
        server_id = str(ctx.guild.id)
        if await db_commands.add_value(server_id,"admins",(str(member.id))):
            message = await get_admins(ctx,'1')
            await ctx.respond(f"{member.mention} has been added as a bot admin.{message}",ephemeral=True)
        else:
            message = await get_admins(ctx,'2')
            await ctx.respond(f"{member.mention} is already a bot admin.{message}",ephemeral=True)
          
  
    ##Should add respond to work
    @discord.slash_command()
    async def remove_bot_admin(self,ctx, member: discord.Member):
        server_id = str(ctx.guild.id)
        if await db_commands.remove_value(server_id,"admins",(str(member.id))):
            message = await get_admins(ctx,'1')
            await ctx.respond(f"{member.mention} has been removed from bot admin.{message}",ephemeral=True)
        else:
            message = await get_admins(ctx,'2')
            await ctx.respond(f"{member.mention} is not a bot admin.{message}",ephemeral=True)
    
    ##ad channel to db
    @discord.slash_command(description="Choose the channel to add to admin channels")
    async def add_channel(self,ctx, channel: discord.TextChannel):
        server_id = str(ctx.guild.id)
        if await db_commands.add_value(server_id,"admin_channels",(str(channel.id))):
            message = await get_channels(ctx,'1')
            await ctx.respond(f"{channel.mention} has been added to the admin channels.{message}",ephemeral=True)
        else:
            message = await get_channels(ctx,'2')
            await ctx.respond(f"{channel.mention} is already found in the admin channels.{message}",ephemeral=True)
    ##remove channel  from db
    @discord.slash_command()
    async def remove_channel(self,ctx, channel: discord.TextChannel):
        server_id = str(ctx.guild.id)
        if await db_commands.remove_value(server_id,"admin_channels",(str(channel.id))):
            message = await get_channels(ctx,'1')
            await ctx.respond(f"{channel.mention} has been removed from the admin channels.{message}",ephemeral=True)
        else:
            message = await get_channels(ctx,'2')
            await ctx.respond(f"{channel.mention} is not in the admin channels.{message}",ephemeral=True)
          
    ##need to be done ##  TODO     new feature
    """
    @discord.slash_command()
    async def set_reminder_message(ctx, *, message):
        server_id = str(ctx.guild.id)
        await db_commands.server_check(server_id)
        db[server_id]["reminder_message"] = message
        await ctx.send("Reminder message has been set.")
    """    
    @commands.command()
    async def delete_server_settings(self,ctx):
        await ctx.message.delete()
        server_id = str(ctx.guild.id)
        hashed_server_id = hashlib.sha256(str(server_id).encode()).hexdigest()
        response = await db_commands.delete_server(server_id)
        if response:
          shutil.rmtree(f"servers_data/{hashed_server_id}")
          await ctx.send("The server settings have been deleted succesfully.")
        else:
          await ctx.send("The server settings are not found.")

          
        
def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Admin(bot)) # add the cog to the bot