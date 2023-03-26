import discord

#function to format data in text
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
  
#function to create the name for temp channel
def check_channel(member:discord.Member):
    guild = member.guild
    existing_channels = [channel.name for channel in guild.voice_channels]
    channel_num = 1
    while f"Temp Channel {channel_num}" in existing_channels:
        channel_num += 1
    channel_name = f"Temp Channel {channel_num}"
    return channel_name