import os

import nextcord
from nextcord.ext.commands import Bot


intents = nextcord.Intents.default()
intents.members = True

token = os.getenv('DISCORD_TOKEN')
client = Bot(token, intents=intents)

client.load_extension('Cogs.Config')
client.load_extension('Cogs.Events')

client.load_extension('Cogs.Items')
client.load_extension('Cogs.Economy')
client.load_extension('Cogs.Country')

client.load_extension('Cogs.Lists')
client.load_extension('Cogs.Income')

@client.event
async def on_ready():
    print('bot is ready')


client.run(token)
