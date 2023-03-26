

#modal 
class MyModal(discord.ui.Modal):
    channel_name=None
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs,timeout=20)

        self.add_item(discord.ui.InputText(label="Channel name -{You have 30 second to respond}", style=discord.InputTextStyle.singleline,placeholder="Enter the name for the voice channel"))

    async def on_timeout(self) -> None:
        await self.message.channel.send("timeout")
        self.stop()
      
    async def callback(self, interaction: discord.Interaction):
        self.channel_name=self.children[0].value
        await interaction.response.defer()
        #await interaction.response.send_message(f"Channel \"{self.channel_name}\" created",ephemeral=True)
        self.stop()
    
 
      
@bot.slash_command()
async def send_modal(ctx):
    """Shows an example of a modal dialog being invoked from a slash command."""
    view = MyModal(title="Voice channel name")
    message = await ctx.send_modal(view)
    view.message=message
    await view.wait()
    result=view.channel_name
    if result is not None:
        await ctx.send(f"the result is here{result}")
    else:
        if ctx.author.voice:
            await ctx.author.move_to(None)
        print("no")

##Button for checking to continue creating the temp channel
class Channel_button(discord.ui.View):
  
    value:bool =None
    channel_name=None

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit("Timedout: You took too long to respond!",view=self)
    
    async def on_timeout(self) -> None:
        await self.disable_all_items()
      
    @discord.ui.button(label="Create the voice channel",style=discord.ButtonStyle.success)
    async def Create(self,button:discord.ui.Button,interaction:discord.Interaction):
        #await interaction.response.send_message("Procced",ephemeral=True)
        view2 = MyModal(title="Voice channel name")
        message2=await interaction.response.send_modal(view2)
        view2.message=message2
        await view2.wait()
        self.channel_name=view2.channel_name
        self.value=True
        self.stop()



async def button(user):
    view = Channel_button(timeout=30)
    """
    try:
    except discord.errors.Forbidden:
        message.channel.send("Open your dms to be able to create ")
    """
    ###check for if the bot can send the user in dm in the update channle make it optional if you cant send then use the default value (Temp_channel) and send a message open your dm to be able to set custom names or use/create temp channel    or you can make context menu to select between custom name or default
    message = await user.send(view=view)
    view.message = message
    await view.wait()
    await view.disable_all_items()
    if view.value is True:  
        result=view.channel_name
        if result is not None:
            await user.send(f"Channel {result} Created succesfully")
            return result
        else:
            if user.voice:
                await user.move_to(None)
            logger.info("no")  
            return False
          
    elif view.value is False or view.value is None:
        return False


#delete
class MyViewssss(discord.ui.View):

  async def on_timeout(self) -> None:
    # Step 2
    for item in self.children:
      item.disabled = True

    # Step 3
    await self.message.edit(view=self)

  @discord.ui.button(label='Example')
  async def example_button(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
    await interaction.response.send_message('Hello!', ephemeral=True)


@bot.command()
async def timeout_example(ctx):
  """An example to showcase disabling buttons on timing out"""
  view = MyView()
  # Step 1
  view.message = await ctx.send('Press me!', view=view)

