import discord
from discord.ext import commands
from typing import Optional

import utils.db_commands as db_commands

# Decorator that adds the given decorator to all methods in a class
def add_decorator_to_methods(decorator):
    def decorate(cls):
        for name, method in vars(cls).items():
            if callable(method) and not name.startswith("_"):
                setattr(cls, name, decorator(method))
        return cls
    return decorate
  
@add_decorator_to_methods(commands.is_owner())
class Owner(commands.Cog): # create a class for our cog that inherits from commands.Cog
    """
    This commands are for the server team, most require admin or owner permissions
    """
  
    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot


    @commands.command()
    async def get_server_data(self,ctx,server_id: str):
      data=await db_commands.get_all_server_data(server_id)
      await ctx.send(f"{data}")
      logger.info(f"{data}")

    @commands.command()
    async def add_newkey_toservers(ctx, key, value, server_id: Optional[int] = None):
      if server_id is not None:
          await add_new_key(server_id, key, value)
          logger.info(f"Added {key} with {value} to server {server_id}")
      else:
          server_ids = [guild.id for guild in self.bot.guilds]
          for server_id in server_ids:
              await add_new_key(server_id, key, value)
          logger.info(f"Added {key} with {value} to all servers")
        
    @commands.command()
    async def remove_key_fromservers(ctx, key):
      if server_id is not None:
          await remove_keys(key)
          logger.info(f"Removed {key} from all servers ")
      
    @discord.slash_command()
    async def get_guilds(self,ctx):
        guilds = self.bot.guilds
        number=1
        for guild in guilds:
            await ctx.send(f"{number}-{guild.name}---{[guild.id]}")
            number+=1
          
    @discord.slash_command()
    async def load(self,ctx, cog: str):
        try:
            self.bot.load_extension(f"cogs.{cog.lower()}")
            response = f"Extension {cog} loaded successfully."
            logger.debug(f"Loadded COG: {cog}")
        except Exception as e:
            response = f"Error loading extension {cog}: {e}"
            logger.error(f"Error Loading COG: {cog} : {e}")
        await ctx.respond(response, ephemeral=True)
      
    @discord.slash_command()
    async def unload(self,ctx, cog: str):
        try:
            self.bot.unload_extension(f"cogs.{cog.lower()}")
            response = f"Extension {cog} unloaded successfully."
            logger.debug(f"UnLoadded COG: {cog}")
        except Exception as e:
            response = f"Error unloading extension {cog}: {e}"
            logger.error(f"Error Unloading COG: {cog} : {e}")
        await ctx.respond(response, ephemeral=True) 
      
    @discord.slash_command()
    async def reload(self,ctx, cog: str):
        try:
            self.bot.reload_extension(f"cogs.{cog.lower()}")
            response = f"Extension {cog} reloaded successfully."
            logger.debug(f"ReLoadded COG: {cog}")
        except Exception as e:
            response = f"Error reloading extension {cog}: {e}"
            logger.error(f"Error Reloading COG: {cog} : {e}")
        await ctx.respond(response, ephemeral=True)


  
def setup(bot): # this is called by Pycord to setup the cog
     bot.add_cog(Owner(bot)) # add the cog to the bot