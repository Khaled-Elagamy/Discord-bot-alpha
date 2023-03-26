import discord
from discord.ext import commands
import utils.db_commands as db_commands
from utils.utils import check_channel
from utils.sessions_manager import update_session

class VCCreator(commands.Cog): # create a class for our cog that inherits from commands.Cog
  
    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self,member, before, after):
      server_id=member.guild.id
      tracked_channels = await db_commands.get_values(server_id,"tracked_channels")
      try: 
        listening_voice_channel = int(await db_commands.get_values(server_id,"listening_voice_channel"))
      except ValueError:
        listening_voice_channel=""
      current_channel=None
      if tracked_channels: 
          if after and after.channel and (after.channel.id == listening_voice_channel or str(after.channel.id) in tracked_channels):
            #set as current channel
              if after.channel.id != listening_voice_channel:
                  current_channel=str(after.channel.id)
            ##To delete the channel if its empty
              if before and before.channel and str(before.channel.id) in tracked_channels:
                if len(before.channel.members) == 0:
                # send the file to a user
                  # delete the channel
                  await before.channel.delete() 
                  await db_commands.remove_value(server_id,"tracked_channels",str(before.channel.id))
      				# create a new voice channel with a random name
              if after.channel.id == listening_voice_channel:
                  if after.channel.user_limit != 1:
                    await after.channel.edit(user_limit=1)
                  temp_name=check_channel(member)
                  
                  new_channel = await after.channel.category.create_voice_channel(name=temp_name)
                  await new_channel.edit(position=0) # Set the position of the channel to be first in category 
                  await db_commands.add_value(server_id,"tracked_channels",str(new_channel.id))
                  await member.move_to(new_channel)
              if current_channel is not None:
                  await update_session(server_id,current_channel,str(member.name), str(member.nick), after.channel.id,self.bot)
          elif before and before.channel and (before.channel.id == listening_voice_channel or str(before.channel.id) in tracked_channels):
              #set as current channel
              current_channel=str(before.channel.id)
              if len(before.channel.members) == 0:
                # send the file to a user
                  # delete the channel
                  if before.channel.id != listening_voice_channel:
                      await before.channel.delete()
                      await db_commands.remove_value(server_id,"tracked_channels",str(before.channel.id))
      
              await update_session(server_id,current_channel,str(member.name), str(member.nick), None,self.bot)
          
          # Get the voice channel object
          voice_channel = before.channel or after.channel
          if voice_channel and voice_channel.id == listening_voice_channel:
              # Get the number of members in the voice channel
              num_members = len(voice_channel.members)
              if num_members == 0:
                  # All members have left the voice channel, send the JSON file to a user
                  user = await self.bot.fetch_user(member.id)
      							##change to embeded
                    ## send the file here
                
def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(VCCreator(bot)) # add the cog to the bot