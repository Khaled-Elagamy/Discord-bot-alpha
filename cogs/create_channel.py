import discord
from discord.ext import commands
from discord import Option
import utils.db_commands as db_commands

##Button for checking to continue creating the temp channel
class Menu(discord.ui.View):
    value:bool =None

    def __init__(self, message, timeout=30):
        super().__init__(timeout=timeout)
        self.message = message
     
    async def disable_all_items(self):
      for item in self.children:
          item.disabled = True
      await self.message.edit(view=self)
      
    async def on_timeout(self) -> None:
        await self.disable_all_items()
        embed = discord.Embed(
            title="Warning",
            description="You took too long to respond!",
            color=discord.Color.red()
        )
        await self.message.edit(embed=embed, view=self)
      
    @discord.ui.button(label="Continue",style=discord.ButtonStyle.success)
    async def continu(self,button:discord.ui.Button,interaction:discord.Interaction):
        #await interaction.response.send_message("Procced",ephemeral=True)
        await interaction.response.edit_message(content=None)
        self.value=True
        self.stop()
  
    @discord.ui.button(label="Abort",style=discord.ButtonStyle.danger)
    async def abort(self,button:discord.ui.Button,interaction:discord.Interaction):
        await interaction.response.send_message("Action stopped",ephemeral=True)
        self.value=False
        self.stop()
      
async def button(ctx):
    embed = discord.Embed(
    title="Warning",
    description="There is an existed voice channel with that name. \n You can stop and recreate again",
    color=discord.Colour.dark_teal()
)
    view = Menu(ctx.message)
    await ctx.respond(embed=embed, view=view,ephemeral=True)
    await view.wait()
    await view.disable_all_items()
    return view.value

class Temp_channel(commands.Cog): # create a class for our cog that inherits from commands.Cog
  
    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
      
    @discord.slash_command()
    async def create_temp_channel(self,ctx,temp_name:Option(str,"Enter the name of the channel")):
        member = ctx.author
        voice_channel = discord.utils.get(ctx.guild.voice_channels, name=temp_name)
        if voice_channel is not None:
            value= await button(ctx)
            if value is False or value is None:
                return
            if value is True:
              pass
        if not member.voice or not member.voice.channel:
            await ctx.respond(f"{member.mention} you have to join a voice channel first",ephemeral=True)
        else:
            category = member.voice.channel.category
            new_channel = await category.create_voice_channel(name=temp_name)
            await new_channel.edit(position=0) # Set the position of the channel to be first in category 
            await db_commands.add_value(ctx.guild.id,"tracked_channels",str(new_channel.id))
            await member.edit(voice_channel= new_channel)
            await ctx.respond(f"{member.mention} has joined \"{new_channel}\" voice channel successfully",ephemeral=True)


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Temp_channel(bot)) # add the cog to the bot