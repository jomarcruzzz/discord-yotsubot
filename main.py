import discord
import command
import os
import json
import dropbox

client = discord.Client()

bot_token = os.environ.get("bot_token", None)
name_cookie = os.environ.get("name_cookie", None)
exclusive_servers = os.environ.get("exclusive_servers", None)
dbx_token = os.environ.get("dbx_token", None)

try:
    with open("local_env.json") as data_file:
        data = json.load(data_file)
        bot_token = data["bot_token"]
        name_cookie = data["name_cookie"]
        exclusive_servers = data["exclusive_servers"]
        dbx_token = data["dbx_token"]
except:
    print("local env not found")

cmd = None
isReady = False

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    global cmd
    global isReady
    global dbx_token
    dbx = dropbox.Dropbox(dbx_token)
    cmd = command.Command(client, dbx)
    isReady = True
    testGame = discord.Game()
    testGame.name = "!commands for list"
    await client.change_presence(game=testGame)

@client.event
async def on_message(message):
    if not isReady:
        return
    #if message.author.name == client.user.name:
    #    print('this is me')

    is_no_u = await check_for_no_u_message(message)
    is_cookie_gay = await check_message_from_cookie_gay(message)
    if is_no_u or is_cookie_gay:
        await send_no_u_message(message)
    else:
        await cmd.parse(message)

async def check_message_from_cookie_gay(message):
    if message.author.name != name_cookie:
        return False

    print('this is cookie')

    for mention in message.mentions:
        if mention.name == client.user.name:
            if message.content.lower().__contains__('gay') or message.content.lower().__contains__('ghey'):
                return True
            return False
    return False

async def check_for_no_u_message(message):
    if(message.author.name == client.user.name):
        return False

    for mention in message.mentions:
        if mention.name == client.user.name:
            if message.content.lower().__contains__('no u'):
                return True
            return False

async def send_no_u_message(message):
    authorId = "<@" + message.author.id + ">"
    await client.send_message(message.channel, authorId + " no u")

client.run(bot_token)