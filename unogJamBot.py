import nextcord
from nextcord.ext import commands
from nextcord.utils import get

import json
import os

JSON_FILE_PATH = 'teams_data.json' # JSON file path to store the team data


def read_team_data(): # Read the team data from the JSON file
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'r') as file:
            return json.load(file)
    return {} 

def write_team_data(data): # Write the team data to the JSON file
    with open(JSON_FILE_PATH, 'w') as file:
        json.dump(data, file, indent=4)

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
client = commands.Bot(command_prefix='/', intents=intents)


team_creators = read_team_data() # Dictionary to store the creator of each team
print(f"Initial team creators: {team_creators}")

SERVER_ID = 11111111111111# Server ID to determine where the bot is used

SPECIFIC_ROLE_NAME = 'YOUR_ROLE' # Role name to determine who can use the bot
SPECIFIC_CATEGORY_ID = 111111111111111 # Category ID to determine where the bot can create channels


pending_invites = {}   # Dictionary to store pending invites for each user
team_list = list(team_creators.keys())  # List to store the names of the teams


@client.event
async def on_ready(): # Print the bot name when the bot is ready
    print(f' {client.user} aktif.')


@client.slash_command(guild_ids=[SERVER_ID], description="Yardım komutlarını göster.") # Show help commands.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def yardım(interaction: nextcord.Interaction):
    await interaction.response.send_message(f'Komutlar:\n'
                                            '- /liste: Takım listesini ve üyelerini gösterir.\n'
                                            '- /takım <takım_ismi>: Takım oluşturur.\n'
                                            '- /davet <üye> <takım_ismi>: Üyeyi takıma davet eder.\n'
                                            '- /kabul <takım_ismi>: Daveti kabul eder.\n'
                                            '- /reddet <takım_ismi>: Daveti reddeder.\n'
                                            '- /ayrıl <takım_ismi>: Takımdan ayrılır.\n'
                                            '- /renk <takım_ismi> <renk>: Takım rengini değiştirir.\n'
                                            '- /isim <takım_ismi> <yeni_isim>: Takımın adını değiştirir.\n'
                                            '- /dağıt <takım_ismi>: Takımı dağıtır.')
    

@client.slash_command(guild_ids=[SERVER_ID], description="Yeni bir takım oluşturur.")  # Create a new team.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def takım(interaction: nextcord.Interaction, takım_ismi: str):
    guild = interaction.guild
    await interaction.response.defer()
    user_in_team = False

    # Check if the user is already in a team
    for role in interaction.user.roles:
        if role.name in team_creators:
            user_in_team = True
            await interaction.followup.send(f'Zaten bir takımda bulunuyorsunuz: {role.name}')
            return

    existing_role = get(guild.roles, name=takım_ismi)
    if existing_role:
        await interaction.followup.send(f'Takım {takım_ismi} zaten var.')
        return

    if not user_in_team:
        team_role = await guild.create_role(name=takım_ismi)
        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(send_messages=False),
            team_role: nextcord.PermissionOverwrite(send_messages=True)
        }

        category = get(guild.categories, id=SPECIFIC_CATEGORY_ID)
        if not category:
            await interaction.followup.send(f'Belirtilen kategori mevcut değil.')
            return

        voice_channel = await guild.create_voice_channel(f'{takım_ismi}', category=category, overwrites=overwrites)

       
        team_creators[takım_ismi] = {
            'takim_adi': voice_channel.name,
            'kurucu': interaction.user.name,
            'uyeler': [interaction.user.id],
            'uye_isimleri' : [interaction.user.name],
            'rol_id': team_role.id,
            'creator_id': interaction.user.id,
            'voice_channel_id': voice_channel.id,
        }
        write_team_data(team_creators)

        # Add the team role to the creator
        await interaction.user.add_roles(team_role)
        team_list.append(takım_ismi + '\n')

        await interaction.followup.send(f'Takım {takım_ismi} oluşturuldu.')
@client.slash_command(guild_ids=[SERVER_ID], description="Üyeyi takıma davet eder.") # Invite a member to the team.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def davet(interaction: nextcord.Interaction, üye: nextcord.Member, takım_ismi: str):
    guild = interaction.guild
    team_role = get(guild.roles, name=takım_ismi) 
    
    if team_role:
        if üye.id not in pending_invites: # Check if the user has pending invites
            pending_invites[üye.id] = [] # Create a list to store pending invites for the user
        pending_invites[üye.id].append(takım_ismi)  # Add the team name to the pending invites list
        await interaction.response.send_message(f'{üye.mention}, {takım_ismi} takımına davet edildiniz. Kabul etmek için /kabul {takım_ismi}, reddetmek için /reddet {takım_ismi} komutlarını kullanabilirsin.')
    else:
        await interaction.response.send_message(f'{takım_ismi} takımı bulunamadı.')


@client.slash_command(guild_ids=[SERVER_ID], description="Takım davetini kabul eder.") # Accept a team invite.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def kabul(interaction: nextcord.Interaction, takım_ismi: str):
    guild = interaction.guild
    team_role = get(guild.roles, name=takım_ismi)
    
    if team_role:
        if interaction.user.id in pending_invites and takım_ismi in pending_invites[interaction.user.id]:
            await interaction.user.add_roles(team_role)
            pending_invites[interaction.user.id].remove(takım_ismi)
            if takım_ismi in team_creators:
                team_creators[takım_ismi]['uyeler'].append(interaction.user.id)
                team_creators[takım_ismi]['uye_isimleri'].append(interaction.user.name)
                write_team_data(team_creators)
                await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımına katıldınız.')
            else:
                await interaction.response.send_message(f'{takım_ismi} takımı bulunamadı.')
    
            if not interaction.response.is_done():
                await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımına katıldınız.')
            else:
                print("Interaction has already been responded to.")
        else:
            await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımına davet edilmediniz.')
    else:
        await interaction.response.send_message(f'{takım_ismi} takımı bulunamadı.')

@client.slash_command(guild_ids=[SERVER_ID], description="Takım davetini reddeder.") # Decline a team invite.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def reddet(interaction: nextcord.Interaction, takım_ismi: str):
    if interaction.user.id in pending_invites and takım_ismi in pending_invites[interaction.user.id]:
        pending_invites[interaction.user.id].remove(takım_ismi)
        await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımına daveti reddettiniz.')
    else:
        await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımına davet edilmediniz veya davet bulunamadı.')

@client.slash_command(guild_ids=[SERVER_ID], description="Takımdan ayrıl.")  # Leave the team.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def ayrıl(interaction: nextcord.Interaction, takım_ismi: str):
    guild = interaction.guild
    team_role = get(guild.roles, name=takım_ismi)
    
    if team_role:
        if team_role in interaction.user.roles:
            await interaction.user.remove_roles(team_role)  # Remove the team role from the user
            team_creators[takım_ismi]['uyeler'].remove(interaction.user.id)
            
            if team_creators[takım_ismi]['creator_id'] == interaction.user.id:
                if team_creators[takım_ismi]['uyeler']:
                    new_creator_id = team_creators[takım_ismi]['uyeler'][0]
                    team_creators[takım_ismi]['creator_id'] = new_creator_id
                    new_creator = guild.get_member(new_creator_id)
                    await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımından ayrıldınız. Yeni takım lideri {new_creator.mention} oldu.')
                else:
                    voice_channel_id = team_creators[takım_ismi].get('voice_channel_id')
                    if voice_channel_id:
                        voice_channel = get(guild.voice_channels, id=voice_channel_id)
                        if voice_channel:
                            await voice_channel.delete()
                    del team_creators[takım_ismi]
                    await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımından ayrıldınız ve takımda başka üye kalmadığı için takım dağıtıldı.')
            else:
                await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımından ayrıldınız.')
            
            write_team_data(team_creators)
        else:
            await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımında değilsiniz.')
    else:
        await interaction.response.send_message(f'{takım_ismi} takımı bulunamadı.')

@client.slash_command(guild_ids=[SERVER_ID], description="Takımı dağıtır.")  # Disband the team.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def dağıt(interaction: nextcord.Interaction, takım_ismi: str):
    guild = interaction.guild
    team_role = get(guild.roles, name=takım_ismi)
    if team_role:
        # Check if the user is the creator of the team
        creator_id = team_creators.get(takım_ismi, {}).get('creator_id')
        if creator_id == interaction.user.id:
            voice_channel = get(guild.voice_channels, id=team_creators[takım_ismi]['voice_channel_id'])  # Get the voice channel of the team
            if voice_channel:
                await voice_channel.delete()  # Delete the voice channel of the team
            
            await team_role.delete()
            del team_creators[takım_ismi]  # Delete the team from the dictionary
            write_team_data(team_creators)  # Write the updated team_creators dictionary to the JSON file
            
            await interaction.response.send_message(f'Takım {takım_ismi} dağıldı.')  # Send a message if the team is disbanded
        else:
            await interaction.response.send_message(f'{takım_ismi} takımını dağıtmak için yetkiniz yok.')  # Send a message if the user doesn't have permission to disband the team
    else:
        await interaction.response.send_message(f'{takım_ismi} takımı bulunamadı.')

@client.slash_command(guild_ids=[SERVER_ID], description="Takım listesini ve üyelerini gösterir.") # Show the team list and members.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def liste(interaction: nextcord.Interaction):
    guild = interaction.guild
    team_list = list(team_creators.keys())
    team_list.sort()
    if not team_list:
        await interaction.response.send_message('Hiç takım bulunamadı.')
        return
    
    team_list_str = ''
    for team_name in team_creators.keys():
        team_list_str += f'------------------------\n{team_name} - '
        member_names = []
        for member_id in team_creators[team_name]['uyeler']:
            member = guild.get_member(member_id)
            if member:
                member_names.append(member.name)
                member_names.append(', ')

        team_list_str +=''.join(member_names) + '\n'
    team_list_str += '------------------------'
    await interaction.response.send_message(f'Takımlar:\n{team_list_str}')  # Send the team list and members




# Predefined colors
COLORS = {
    'kırmızı': nextcord.Color.red(),
    'mavi': nextcord.Color.blue(),
    'yeşil': nextcord.Color.green(),
    'sarı': nextcord.Color.gold(),
    'turuncu' : nextcord.Color.orange(),
    'pembe': nextcord.Color.magenta(),
    'mor': nextcord.Color.purple(),
    'rasgele': nextcord.Color.random(),
    'siyah': nextcord.Color.dark_theme(),
    'gri': nextcord.Color.light_grey(),
    'turkuaz': nextcord.Color.teal()
}

@client.slash_command(guild_ids=[SERVER_ID], description=" Takım rengini değiştirir. ") # Change the team color.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def renk(interaction: nextcord.Interaction, takım_ismi: str, renk: str):
    guild = interaction.guild
    team_role = get(guild.roles, name=takım_ismi)
    
    if team_role and renk in COLORS:
        await team_role.edit(color=COLORS[renk])
        await interaction.response.send_message(f'{takım_ismi} takımının rengi {renk} olarak değiştirildi.')
    else:
        await interaction.response.send_message(f'{takım_ismi} takımı bulunamadı veya renk bulunamadı.')

@client.slash_command(guild_ids=[SERVER_ID], description="Takımın adını değiştirir.") # Change the team name.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def isim(interaction: nextcord.Interaction, takım_ismi: str, yeni_isim: str):
    guild = interaction.guild
    team_role = get(guild.roles, name=takım_ismi)
    
    # Check if the new name is already taken
    if get(guild.roles, name=yeni_isim):
        await interaction.response.send_message(f'{yeni_isim} ismi zaten başka bir takım tarafından kullanılıyor.')
        return
    
    if team_role and team_creators.get(takım_ismi, {}).get('creator_id') == interaction.user.id:
        await team_role.edit(name=yeni_isim)
        
        voice_channel_id = team_creators.get(takım_ismi, {}).get('voice_channel_id')
        voice_channel = get(guild.voice_channels, id=voice_channel_id)
        
        if voice_channel:
            await voice_channel.edit(name=yeni_isim)
        
        # Update the team_creators dictionary with the new team name
        team_creators[yeni_isim] = team_creators.pop(takım_ismi)
        
        await interaction.response.send_message(f'{takım_ismi} takımının adı {yeni_isim} olarak değiştirildi.')
    else:
        await interaction.response.send_message(f'{takım_ismi} takımı bulunamadı veya ad değiştirme yetkiniz yok.')







client.run('YOUR_BOT_TOKEN') # Run the bot with the token