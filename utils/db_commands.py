from replit import db
import json
import utils.log_setup

logger = utils.log_setup.logging.getLogger("bot")

# Check  server settings from the database (if any)
def server_check(server_id):
    if str(server_id) not in db:
        db[str(server_id)] = {
          "admins": [],
          "admin_channels": [],
          "tracked_channels": [],
          "files": [],
          "listening_voice_channel":""
        }
        logger.info("The server has been made")
    else:
        logger.info("The server is found already")
    server=db[str(server_id)]
    return server
  
# Load the saved settings from the database (if any)
async def get_server(server_id):
  server = db.get(server_id)
  if server is not None:
    return server
  else:
    return server_check(server_id)

    
# Load the raw saved settings from the database (if any)
async def get_server_raw(server_id):
    try:
        # Try to get the server data
        server_data = db.get_raw(server_id)
        if server_data is not None:
            return server_data
    except KeyError:
        # If server is not found in the database, create new server data
        server_data = server_check(server_id)
        server_data=db.get_raw(server_id)
    return server_data

    
  
# Function to set the data for a server
def save_data(server_id,data):
  db[str(server_id)] = data

# Function to add new keys to the server 
async def add_new_key(server_id,key,value):
  data= await get_server(str(server_id))
  data[key]=[value]  
  save_data(server_id,data)



# Function to add values for keys in server
async def add_value(server_id,key,value):
  data= await get_server(str(server_id))
  #Add exception here if data is none
  if key in data:
      if isinstance(data[key], str):
          data[key]=str(value)
          save_data(server_id,data)
          return True
      else:  
          if value not in data[key]:
            data[key].append(value)
            save_data(server_id,data)
            return True
          else:
            # Value is already in the list, handle the error here
            logger.info(f"{value} is already in {key} list for server {server_id}")  
  else:
      await add_new_key(server_id,key,value)


#Function to remove string values    
async def empty_string(server_id,key):
  data= await get_server(str(server_id))
  if isinstance(data[key], str):
      data[key]=""
      save_data(server_id,data)
      return True 
  else:
      logger.info("Wrong input type")
    
# Function to remove values for keys in server
async def remove_value(server_id,key,value):
  data= await get_server(str(server_id))
  if value in data[key]:
    data[key].remove(value)
    save_data(server_id,data)
    return True
  else:
    logger.info(f"{value} is not in the database")
  
##Remmber to remove that you can mention the bot here
async def get_values(server_id,key):
  data= await get_server_raw(str(server_id))
  if data is not None:
    data = json.loads(data)
    if isinstance(data[key], str):
        return data[key]
    else:
        json_data = data.get(key, [])
        if json_data:
            return json_data
        else:
          return "Nodata"
##Remmber to remove that you can mention the bot here
## add help cod form pycord dcoument (error command)

# Remove server settings from the database (if any)
async def delete_server(server_id):
  if server_id not in db.keys():
      return False
  del db[server_id]
  return True

##Owner db commands

# Function to remove keys from the all servers
async def remove_keys(key):
  for server in db.keys():
    data = db[server]
    if key in data:
        del data[key]
        db[server] = data
        save_data(server_id,data)
        return True
    else: 
        return "Nodata"
  

#Get certain server data
async def get_all_server_data(server_id):
  try:
      # Try to get the server data
      server_data = db.get_raw(server_id)
      if server_data is not None:
          return server_data
  except KeyError:
      # If server is not found in the database, create new server data
      return "Nodata"
  
#Get all servers id
async def get_all_servers_id():
  data= db.keys()
  return data


                        