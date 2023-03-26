import os
import discord
import utils.log_setup
import utils.db_commands as db_commands
from discord.ext import commands
from discord import Option
from utils.sessions_manager import load_sessions
from utils.utils import format

logger = utils.log_setup.logging.getLogger("bot")

#Function to get files name existing in db for selection 
async def get_files_name(server_id):
    values=await db_commands.get_values(server_id,"files")
    options= []
    if values and isinstance(values, list):
        for value in values:
            parts = value.split("?")
            new_file_name = f"{parts[0]}-date:{parts[2]}"
            option = discord.SelectOption(label=new_file_name, value=value)
            options.append(option)
    else:
        options = [discord.SelectOption(label="❌No files found❌", value="none")]
    return options

#Selection menu 1.option 
class SurveyView(discord.ui.View):
    answer1 =None
    answer2 =None
  
    def __init__(self, server_id):
        super().__init__()
        self.server_id = server_id
        self.timeout = 30

      
    @discord.ui.select(
      placeholder="Where to send the data ?",
      options=[
        discord.SelectOption(label="MeOnly",value="MeOnly",description="Will be sent for you in DM!"),
        discord.SelectOption(label="Admin-chat",value="Admin-chat",description="Will be sent for channels registered for the bot!"),
        discord.SelectOption(label="Both",value="Both",description="Will be sent for you and the channels!")
      ]
    )
    async def select_option(self,select_item:discord.ui.Select,interaction:discord.Interaction):
        self.answer1 = select_item.values[0]
        self.children[0].disabled=True
        action_select=File(await get_files_name(server_id=self.server_id))
        self.add_item(action_select)
        await interaction.response.edit_message(view=self)
  
    async def files(self,interaction:discord.Interaction,choices):
        self.answer2 = choices
        self.children[1].disabled=True
        await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit("Timedout: You took too long to respond!",view=self)
        self.stop()
      
#Selection menu 2.option
class File(discord.ui.Select):
  def __init__(self,options):
    if len(options) < 2:
        max_values = 1
    else:
        max_values = 2
    super().__init__(options=options,placeholder="Which file to send ?",max_values=max_values)
  async def callback(self,interaction:discord.Interaction):
    await self.view.files(interaction,self.values)

    
  
class Attendence(commands.Cog): # create a class for our cog that inherits from commands.Cog
  
    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot

    # send attendance records to admins
    async def send_records_to_admin_channel(self,ctx):
        data= await db_commands.get_values(str(ctx.guild.id),"admin_channels")
        if data:
              if isinstance(data, list):
                 # admin_names = ", ".join(member.mention for member in ctx.guild.members if str(member.id) in data)
                  for channel_data in data:
                      channel_id = channel_data
                      channel = await self.bot.fetch_channel(channel_id)
                      if channel is not None:
                          await channel.send(file=discord.File("Attendence.txt", 'Attendence.txt'))
              else:
                  await ctx.respond("There are no channels for this bot.",ephemeral=True)
        else:
            await ctx.respond("Server data not found.",ephemeral=True)    
    ##Send attendence
    @discord.slash_command(name="send_attendence")
    @commands.has_permissions(administrator=True)
    #@commands.has_role(role id)
    async def send_attendence(self,ctx):
      server_id = ctx.guild.id
      view= SurveyView(server_id = ctx.guild.id)
      await ctx.respond(view=view,ephemeral=True)
      await view.wait()
      results = {
        "a1":view.answer1,
        "a2":view.answer2,
      } 
      if view.answer2 is None:
          return
      if results["a2"] != ['none'] :
          for result in results["a2"]:
              parts = result.split("?")
              logger.info(f"{parts[1]}")
              data = await load_sessions(self.bot,server_id,parts[1])
              if data:
                  format(data)
                  try:
                    if results["a1"] == 'MeOnly':  
                      try:
                          await ctx.author.send(
                            file=discord.File("Attendence.txt", 'Attendence.txt'))
                      except discord.errors.Forbidden:
                          await ctx.respond("Open your dms to be able to send the attendence",ephemeral=True)
                          return
                    elif results["a1"] == 'Admin-chat':            
                      await self.send_records_to_admin_channel(ctx)
                    elif results["a1"] == 'Both':
                      await self.send_records_to_admin_channel(ctx)
                      try:
                          await ctx.author.send(
                            file=discord.File("Attendence.txt", 'Attendence.txt'))
                      except discord.errors.Forbidden:
                          await ctx.respond("Open your dms to be able to Send the attendence",ephemeral=True)
                          return
                      
                  ##sent==false
                    await ctx.respond(f'Attendence has been sent to `{results["a1"]}` **NOTE**: if there is ''{NN} that means ''{No NickName} !',ephemeral=True)
                    os.remove('Attendence.txt')
                  except Exception as e:
                    return e
              else:
                await ctx.respond(f"This File is not found ,maybe was deleted",ephemeral=True)
      else: 
          await ctx.respond(f'There is no attendence found !',ephemeral=True)  
        
        

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Attendence(bot)) # add the cog to the bot