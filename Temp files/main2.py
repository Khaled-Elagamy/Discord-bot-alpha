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

# load saved sessions from file

#check if decoded before or not
def is_base64_encoded(value):
    try:
        decoded_value = json.loads(base64.b64decode(value.encode()).decode())
        return decoded_value
    except:
        return False


      
async def load_sessions(server_id,current_channel):
  hashed_server_id = hashlib.sha256(str(server_id).encode()).hexdigest()
  try:
      if int(current_channel):
          hashed_current_channel = base64.b64encode(json.dumps(current_channel).encode()).decode()
  except ValueError:
      hashed_current_channel=current_channel
  try:
    with open(f"servers_data/{hashed_server_id}/{hashed_current_channel}.json", "r") as f:
      return json.load(f)
  except FileNotFoundError:
    if current_channel:
      try:        
        if is_base64_encoded(current_channel):
            current_channel=json.loads(base64.b64decode(current_channel.encode()).decode())
        channel = await bot.fetch_channel(current_channel)
      except discord.errors.NotFound:
        file_names = await db_commands.get_values(server_id, "files")
        file_name = next((f for f in file_names if hashed_current_channel in f), None)
        if file_name is not None:
            await db_commands.remove_value(server_id,"files",file_name)
            return False
          
      file_name = f"{channel}?{hashed_current_channel}"+ datetime.now().strftime("?%m-%d/%H-%M-%S") + ".json"
      await db_commands.add_value(server_id,"files",file_name)
      return {}
            
@bot.check
async def globally_block_dms(ctx):
    if ctx.guild is None:
        raise commands.CommandError("Attempted to execute command in DM.")
    return True
    



# save sessions to file
def save_sessions(server_id,current_channel,sessions):
  hashed_server_id = hashlib.sha256(str(server_id).encode()).hexdigest()
  hashed_current_channel = base64.b64encode(json.dumps(current_channel).encode()).decode()
  
  os.makedirs(f"servers_data/{hashed_server_id}" ,exist_ok=True)
  with open(f"servers_data/{hashed_server_id}/{hashed_current_channel}.json", "w", encoding='utf-8') as f:
    json.dump(sessions, f, default=str, ensure_ascii=False, indent=4)


# update session data for user
async def update_session(server_id,current_channel,user_name, nick_name, channel):
  sessions = await load_sessions(server_id,current_channel)
  if not ("Totalusers joined" in sessions):
    sessions.update({"Totalusers joined": 0})
  now = datetime.now().strftime("%d/%m %H:%M:%S")
  session = sessions.get(user_name)
  if session is None:
    sessions['Totalusers joined'] += 1
    if nick_name == "None":
      nick_name = user_name + "{NN}"
    sessions[user_name] = {
      "nick_name": nick_name,
      "first_time_joined":now,
      "start_time": now,
      "end_time": None,
      "total_time": "0 seconds"
    }
  elif channel is None:
    session["end_time"] = now
    timediffrence = datetime.strptime(str(
      session["end_time"]), "%d/%m %H:%M:%S") - datetime.strptime(
        str(session["start_time"]), "%d/%m %H:%M:%S")

    # add the new time to the old time
    old_time = int(session["total_time"].split()[0])
    total_time = old_time + timediffrence.seconds
    # calculate the time in minutes and hours
    minutes, seconds = divmod(total_time, 60)
    hours, minutes = divmod(minutes, 60)

    # construct the time string
    if hours > 0:
      time_str = f"{hours} hour{'s' if hours > 1 else ''} {minutes} minute{'s' if minutes > 1 else ''}"
    elif minutes > 0:
      time_str = f"{minutes} minute{'s' if minutes > 1 else ''} {seconds} second{'s' if seconds > 1 else ''}"
    else:
      time_str = f"{seconds} second{'s' if seconds > 1 else ''}"

    # update the JSON object with the new value and the constructed time string

    session["total_time"] = time_str
  else:
    session["start_time"] = now
    session["end_time"] = None

  # save updated session data
  save_sessions(server_id,current_channel,sessions)


# send attendance records to admins
async def send_records_to_admin_channel(ctx):
  data= await db_commands.get_values(str(ctx.guild.id),"admin_channels")
  if data:
        if isinstance(data, list):
           # admin_names = ", ".join(member.mention for member in ctx.guild.members if str(member.id) in data)
            for channel_data in data:
                channel_id = channel_data
                channel = await bot.fetch_channel(channel_id)
                if channel is not None:
                    await channel.send(
    file=discord.File("Attendence.txt", 'Attendence.txt'))
        else:
            await ctx.respond("There are no channels for this bot.",ephemeral=True)
  else:
      await ctx.respond("Server data not found.",ephemeral=True)

##Button for checking to continue creating the temp channel
class Menu(discord.ui.View):
  
    value:bool =None

    async def disable_all_items(self):
      for item in self.children:
          item.disabled = True
      await self.message.edit("Timedout: You took too long to respond!",view=self)

  
    async def on_timeout(self) -> None:
        await self.disable_all_items()

      
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
    embed = discord.Embed(colour=discord.Colour.dark_teal(),title="Warning", description="There is an existed voice channel with that name \n You can stop and recreate again")
    view = Menu(timeout=30)
    await ctx.respond(embed=embed,ephemeral=True)
    message = await ctx.respond(view=view,ephemeral=True)
    view.message = message
    await view.wait()
    await view.disable_all_items()
    return view.value

    
  
    
@bot.slash_command()
async def create_temp_channel(ctx,temp_name:Option(str,"Enter the name of the channel")):
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
     
        
def check_channel(member:discord.Member):
    guild = member.guild
    existing_channels = [channel.name for channel in guild.voice_channels]
    channel_num = 1
    while f"Temp Channel {channel_num}" in existing_channels:
        channel_num += 1
    channel_name = f"Temp Channel {channel_num}"
    return channel_name

##ToDo create new voice channel on press and handel this channel and after it end get the file ready or send it and if new voice channel created create new file and make every file avaliable for only 24 hours 
# handle user joining or leaving voice channel
@bot.event
async def on_voice_state_update(member, before, after):
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
                await update_session(server_id,current_channel,str(member.name), str(member.nick), after.channel.id)
        elif before and before.channel and (before.channel.id == listening_voice_channel or str(before.channel.id) in tracked_channels):
            #set as current channel
            current_channel=str(before.channel.id)
            if len(before.channel.members) == 0:
              # send the file to a user
                # delete the channel
                if before.channel.id != listening_voice_channel:
                    await before.channel.delete()
                    await db_commands.remove_value(server_id,"tracked_channels",str(before.channel.id))
    
            await update_session(server_id,current_channel,str(member.name), str(member.nick), None)
        
        # Get the voice channel object
        voice_channel = before.channel or after.channel
        if voice_channel and voice_channel.id == listening_voice_channel:
            # Get the number of members in the voice channel
            num_members = len(voice_channel.members)
            if num_members == 0:
                # All members have left the voice channel, send the JSON file to a user
                user = await bot.fetch_user(member.id)
    							##change to embeded
                  ## send the file here
    
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
  
#select menu 1.option 
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
      
#select menu 2.option
class File(discord.ui.Select):
  def __init__(self,options):
    if len(options) < 2:
        max_values = 1
    else:
        max_values = 2
    super().__init__(options=options,placeholder="Which file to send ?",max_values=max_values)
  async def callback(self,interaction:discord.Interaction):
    await self.view.files(interaction,self.values)

    
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

##Send attendence
@bot.slash_command(name="send_attendence")
@commands.has_permissions(administrator=True)
#@commands.has_role(role id)
async def send_attendence(ctx):
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
          data = await load_sessions(server_id,parts[1])
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
                  await send_records_to_admin_channel(ctx)
                elif results["a1"] == 'Both':
                  await send_records_to_admin_channel(ctx)
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
    
##function to forma data in text
def format(data):
  # write data to text file
  with open('Attendence.txt', 'w') as f:
    f.write('{:<20} {:<20}\n'.format('Total Users', data['Totalusers joined']))
    f.write('-' * 120 + '\n')
    f.write('{:<25} {:<25} {:<25} {:<25} {:<25} {:<20}\n'.format(
      'User', 'Real Name','first_time_joined', 'Start Time', 'End Time', 'Total Time'))
    f.write('-' * 120 + '\n')
    for key in data:
      if key == 'Totalusers joined':
        continue
      user_data = data[key]
      if user_data['end_time'] is None:
        end_time = "null"
      else:
        end_time = user_data['end_time']
      f.write('{:<25} {:<25} {:<25} {:<25} {:<25} {:<20}\n'.format(
        user_data['nick_name'], key,user_data['first_time_joined'],user_data['start_time'],
        end_time, user_data['total_time']))
  

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
@bot.command()
async def get_server_data(ctx,server_id):
  data=await db_commands.get_all_server_data(server_id)
  logger.info(f"{data}")

  
@bot.command()
@commands.is_owner()
async def get_guilds(ctx):
    guilds = bot.guilds
    number=1
    for guild in guilds:
        await ctx.send(f"{number}-{guild.name}---{[guild.id]}")
        number+=1
      
@bot.event
async def on_ready():
  logger.info(f"Logged in as {bot.user.name}")
  


bot.load_extension('admin')
bot.run(os.getenv("Token"))
