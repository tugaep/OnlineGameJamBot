import nextcord
from nextcord.ext import commands
from nextcord.utils import get


intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
client = commands.Bot(command_prefix='/', intents=intents)


SERVER_ID = 111111111111111111 # Server ID to determine where the bot is used

SPECIFIC_ROLE_NAME = 'YOUR_ROLE' # Role name to determine who can use the bot
SPECIFIC_CATEGORY_ID = 1111111111111111 # Category ID to determine where the bot can create channels


team_creators = {} # Dictionary to store the creator of each team
pending_invites = {}   # Dictionary to store pending invites for each user





@client.event
async def on_ready(): 
    print(f' {client.user} aktif.')


@client.slash_command(guild_ids=[SERVER_ID], description="Yardım komutlarını göster.") # Show help commands.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def yardım(interaction: nextcord.Interaction):
    await interaction.response.send_message(f'Komutlar:\n'
                                            '- /takım <takım_ismi>: Takım oluşturur.\n'
                                            '- /davet <üye> <takım_ismi>: Üyeyi takıma davet eder.\n'
                                            '- /kabul <takım_ismi>: Daveti kabul eder.\n'
                                            '- /reddet <takım_ismi>: Daveti reddeder.\n'
                                            '- /dağıt <takım_ismi>: Takımı dağıtır.')
    

@client.slash_command(guild_ids=[SERVER_ID], description="Yeni bir takım oluşturur.") # Create a new team.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def takım(interaction: nextcord.Interaction, takım_ismi: str):
    guild = interaction.guild
    existing_role = get(guild.roles, name=takım_ismi)
    
    if existing_role:
        await interaction.response.send_message(f'{takım_ismi} takımı zaten var.') # Send a message if the team already exists
        return
    
    takım_rolü = await guild.create_role(name=takım_ismi) # Create a role for the team
    overwrites = {
        guild.default_role: nextcord.PermissionOverwrite(read_messages=False), # Set the default role permissions
        takım_rolü: nextcord.PermissionOverwrite(read_messages=True)
    }
    
    category = get(guild.categories, id=SPECIFIC_CATEGORY_ID) # Get the category to create the voice channel in
    if not category:
        await interaction.response.send_message(f'Kategori bulunamadı.')
        return
    
    voice_channel = await guild.create_voice_channel(f'{takım_ismi}', category=category, overwrites=overwrites) 
    
    team_creators[takım_ismi] = {
        'creator_id': interaction.user.id, # Store the creator of the team
        'voice_channel_id': voice_channel.id # Store the voice channel of the team
    }
    
    await interaction.user.add_roles(takım_rolü)  # Add the team role to the creator of the team
    
    await interaction.response.send_message(f'{takım_ismi} takımı oluşturuldu.') # Send a message if the team is created


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


@client.slash_command(guild_ids=[SERVER_ID], description="Daveti kabul eder.") # Accept the invitation.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def kabul(interaction: nextcord.Interaction, takım_ismi: str):
    guild = interaction.guild
    team_role = get(guild.roles, name=takım_ismi)
    
    if team_role and interaction.user.id in pending_invites and takım_ismi in pending_invites[interaction.user.id]: # Check if the user has pending invites
        await interaction.user.add_roles(team_role)  # Add the team role to the user
        pending_invites[interaction.user.id].remove(takım_ismi)  # Remove the team name from the pending invites list
        if not pending_invites[interaction.user.id]:
            del pending_invites[interaction.user.id]  # Delete the user from the pending invites dictionary if they don't have any pending invites
        await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımına katıldı!') # Send a message if the user accepts the invitation

    else:
        await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımına katılmak için davetiyeniz bulunmamaktadır.') # Send a message if the user doesn't have a pending invite


@client.slash_command(guild_ids=[SERVER_ID], description="Daveti reddeder.") # Decline the invitation.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def reddet(interaction: nextcord.Interaction, takım_ismi: str):
    if interaction.user.id in pending_invites and takım_ismi in pending_invites[interaction.user.id]: # Check if the user has pending invites
        pending_invites[interaction.user.id].remove(takım_ismi) # Remove the team name from the pending invites list
        if not pending_invites[interaction.user.id]: 
            del pending_invites[interaction.user.id] # Delete the user from the pending invites dictionary if they don't have any pending invites
        await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımına katılmayı reddetti.') # Send a message if the user declines the invitation
    else:
        await interaction.response.send_message(f'{interaction.user.mention}, {takım_ismi} takımına katılmak için davetiyeniz bulunmamaktadır.') # Send a message if the user doesn't have a pending invite


@client.slash_command(guild_ids=[SERVER_ID], description="Takımı dağıtır.") # Disband the team.
@commands.has_role(SPECIFIC_ROLE_NAME)
async def dağıt(interaction: nextcord.Interaction, takım_ismi: str):
    guild = interaction.guild
    team_role = get(guild.roles, name=takım_ismi)
    
    if team_role and takım_ismi in team_creators and team_creators[takım_ismi]['creator_id'] == interaction.user.id: # Check if the user is the creator of the team
        voice_channel = get(guild.voice_channels, id=team_creators[takım_ismi]['voice_channel_id']) # Get the voice channel of the team
        if voice_channel:
            await voice_channel.delete() # Delete the voice channel of the team
        
        await team_role.delete()
        del team_creators[takım_ismi] # Delete the team from the dictionary
        
        await interaction.response.send_message(f'Takım {takım_ismi} dağıldı.') # Send a message if the team is disbanded
    else:
        await interaction.response.send_message(f'{takım_ismi} takımını dağıtmak için yetkiniz yok.') # Send a message if the user doesn't have permission to disband the team



client.run('BOT_TOKEN') # Run the bot with the token