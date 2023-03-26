import os
import discord
import json
import hashlib
import base64
from datetime import datetime
import utils.db_commands as db_commands

# load saved sessions from file

#check if decoded before or not
def is_base64_encoded(value):
    try:
        decoded_value = json.loads(base64.b64decode(value.encode()).decode())
        return decoded_value
    except:
        return False


      
async def load_sessions(bot,server_id,current_channel):
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


# save sessions to file
def save_sessions(server_id,current_channel,sessions):
  hashed_server_id = hashlib.sha256(str(server_id).encode()).hexdigest()
  hashed_current_channel = base64.b64encode(json.dumps(current_channel).encode()).decode()
  
  os.makedirs(f"servers_data/{hashed_server_id}" ,exist_ok=True)
  with open(f"servers_data/{hashed_server_id}/{hashed_current_channel}.json", "w", encoding='utf-8') as f:
    json.dump(sessions, f, default=str, ensure_ascii=False, indent=4)

# update session data for user
async def update_session(server_id,current_channel,user_name, nick_name, channel,bot):
  sessions = await load_sessions(bot,server_id,current_channel)
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