import discord
import random
import re
import os
import requests
from bs4 import BeautifulSoup as BS
from PIL import Image
import uuid
import json

dbx_reactions_dir = "/reactions/"
dbx_reactions_for_approval_dir = "/reactions/forApproval/"

local_tempDir = "tmp/"
local_reactions_dir = "reactions/"

owner_id = os.environ.get('owner_id', None)
testing_server_id = os.environ.get('testing_server_id', None)

channel_bot_pms = "bot-pms"
channel_reactions_for_approval = "reactions-for-approval"

reactions_per_message = 50

if owner_id == None:
    with open("local_env.json") as data_file:
        data = json.load(data_file)
        owner_id = data["owner_id"]
        testing_server_id = data["testing_server_id"]

class Command():

    def __init__(self, client, dbx):
        self.client = client
        for server in client.servers:
            if server.id == testing_server_id:
                for channel in server.channels:
                    if channel.name == channel_bot_pms:
                        self.channel_bot_pms = channel
                        continue
                    if channel.name == channel_reactions_for_approval:
                        self.channel_reactions_for_approval = channel
                        continue
                break
        self.dbx = dbx

    async def __notexist__(self, message):
        print("Command does not exist. From",message.server.name,message.channel.name,message.author.name)

    async def __commands__(self, message):
        commands = ""
        commands += "!aww or !a - Fetch a random image of cute stuffs >.<" + "\n\n"
        commands += "!dadjoke or !d - Generate a dad joke" + "\n\n"
        commands += "!rdump or !rd - Fetch a random image content" + "\n\n"
        commands += "!react or !r {args} - Reaction command." + "\n" \
                        "> list - Fetch list of react images" + "\n" \
                        "> {react_name} - Fetch a react image" + "\n" \
                        "> add {react_name} - Add a react image for approval" + "\n\n"
        commands += "!purge or !p {args} - Purge command. (default=all)" + "\n" \
                        "> all - Purge all messages by the bot" + "\n" \
                        "> reacts - Purge all react images by the bot" + "\n\n"

        em = discord.Embed(title="Commands", description=commands)
        em.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        if message.author.id == owner_id:
            await self.client.send_message(self.channel_bot_pms, embed=em)
        else:
            await self.client.send_message(message.author, embed=em)

    async def parse(self, message):
        if not message.content.startswith("!"):
            return

        contents = message.content.split(" ");
        command = contents[0]
        command = command[1:]

        await getattr(self,'__%s__' % command,self.__notexist__)(message)

    async def __r__(self,message):
        await self.__react__(message)

    async def __react__(self,message):
        args = message.content.split(" ")
        if len(args) == 1:
            return

        arg = args[1]

        if arg == "list":
            file_list = get_files_list(self.dbx, dbx_reactions_dir)
            file_list.sort()
            range_len = int(len(file_list)/reactions_per_message) + 1
            for i in range(range_len):
                print("page ", i)
                tmp_list = file_list[i * reactions_per_message : i * reactions_per_message + reactions_per_message]
                em = discord.Embed(title="Reaction List " + str(i+1) + "/" + str(range_len), description="\n".join(tmp_list))
                em.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
                if message.author.id == owner_id:
                    await self.client.send_message(self.channel_bot_pms, embed=em)
                else:
                    await self.client.send_message(message.author, embed=em)
            return

        elif arg == "add":
            if len(message.attachments) == 0:
                em = discord.Embed(title="Command error", description="No attachments found")
                await self.client.send_message(message.channel, embed=em)
                return
            if len(args) != 3:
                em = discord.Embed(title="Command error", description="Invalid number of arguments")
                await self.client.send_message(message.channel, embed=em)
                return

            url = message.attachments[0].get("url")
            fileparts = message.attachments[0].get("filename").split(".")
            extension = "." + fileparts[len(fileparts)-1]

            filename = args[2] + extension
            if file_exists(self.dbx, filename, message.author.id == owner_id):
                em = discord.Embed(title="Command error", description="React name already exists")
                await self.client.send_message(message.channel, embed=em)
            else:
                result = save_react(self.dbx, url, filename, message.author.id == owner_id)
                if result:
                    em = None
                    if message.author.id == owner_id:
                        em = discord.Embed(title="Command success", description="Added " + args[2])
                    else:
                        em2 = discord.Embed(title="For approval", description=args[2])
                        em2.set_image(url=url)
                        await self.client.send_message(self.channel_reactions_for_approval, embed=em2)
                        em = discord.Embed(title="Command success", description="Added " + args[2] + " for approval")

                    await self.client.send_message(message.channel, embed=em)
                else:
                    em = discord.Embed(title="Command failed", description="Failed to add " + args[2])
                    await self.client.send_message(message.channel, embed=em)
            return

        elif message.author.id == owner_id and (arg == "approve" or arg == "reject"):
            if len(args) < 3 or len(args) > 4:
                em = discord.Embed(title="Command error", description="Invalid number of arguments")
                await self.client.send_message(message.channel, embed=em)
                return

            async for tmp_message in self.client.logs_from(self.channel_reactions_for_approval):
                print(tmp_message.embeds)
                if len(tmp_message.embeds) == 1 and tmp_message.embeds[0]["title"] == "For approval" and tmp_message.embeds[0]["description"] == args[2]:
                    parts = tmp_message.embeds[0]["image"]["url"].split("/")
                    parts = parts[len(parts)-1].split(".")
                    extension = "." + parts[len(parts)-1]
                    from_name = args[2] + extension
                    to_name = args[2] + extension
                    if len(args) == 4:
                        to_name = args[3] + extension
                    try:
                        self.dbx.files_move(dbx_reactions_for_approval_dir + from_name, dbx_reactions_dir + to_name)
                        await self.client.delete_message(tmp_message)
                        if message.channel == channel_reactions_for_approval:
                            await self.client.delete_message(message)
                    except:
                        em = discord.Embed(title="Approval failed", description="React name already exists")
                        await self.client.send_message(message.channel, embed=em)
                    break
            return

        else:
            exact = True
            if arg.endswith("."):
                arg = arg[0:-1]
                exact = False
            result = []
            start = 0
            while True:
                tmp_result = self.dbx.files_search(dbx_reactions_dir, arg, start=start)
                result.extend(tmp_result.matches)
                if not tmp_result.more:
                    break;
                start = tmp_result.start
            if len(result) == 0 or exact and not str(result[0].metadata.name).lower().startswith(arg.lower() + "."):
                em = discord.Embed(title="Command error", description="React does not exist")
                await self.client.send_message(message.channel, embed=em)
                return
            index = 0
            if not exact:
                index = random.randrange(len(result))
            name = result[index].metadata.name
            path = str(uuid.uuid4().hex)
            os.mkdir(local_tempDir + path)
            md, response = self.dbx.files_download(dbx_reactions_dir+name)
            f = open(local_tempDir + path + "/" + name, 'wb')  # create file locally
            f.write(response.content)  # write image content to this file
            f.close()
            extension = "." + name.split(".")[-1]
            await self.client.send_file(message.channel, local_tempDir + path + "/" + name, filename="react"+extension)
            os.remove(local_tempDir + path + "/" + name)
            os.rmdir(local_tempDir + path)

    async def __d__(self, message):
        await self.__dadjoke__(message)

    async def __dadjoke__(self, message):
        response = requests.get("https://icanhazdadjoke.com/slack")
        joke = response.json().get('attachments')[0].get('text')
        em = discord.Embed(title="Dad Joke", description=joke)
        await self.client.send_message(message.channel, embed=em)

    async def __rd__(self, message):
        await self.__rdump__(message)

    async def __rdump__(self, message):
        await self.client.send_typing(message.channel)
        path = fetch_ifunny_shuffle()
        await self.client.send_file(message.channel, path)
        os.remove(path)

    async def __a__(self, message):
        await self.__aww__(message)

    async def __aww__(self, message):
        await self.client.send_typing(message.channel)
        path = fetch_random_reddit_image_content('aww')
        await self.client.send_file(message.channel, path)
        os.remove(path)

    async def __p__(self, message):
        await self.__purge__(message)

    async def __purge__(self, message):
        args = message.content.split(" ")
        if len(args) == 1:
            args.append("all")

        arg = args[1]
        tmp_timestamp = None
        timestamp = None
        messages = 0
        if arg == "all":
            await self.client.purge_from(message.channel, limit=300,
                                         check=lambda m: m.author == self.client.user)

        elif arg == "reacts":
            await self.client.purge_from(message.channel, limit=300,
                                         check=lambda m: m.author == self.client.user and len(m.attachments) > 0
                                         and m.attachments[0]["filename"].startswith("react."))

def fetch_ifunny_shuffle():
    ifunny = requests.get("https://ifunny.co/feeds/shuffle").content
    soup = BS(ifunny, "html.parser")

    div = soup.select("div.post__media > div.media")[0]
    data_type = div.get("data-type")

    if data_type == "video":
        return fetch_ifunny_shuffle()
    elif data_type == "image":
        print('gif content')
        content = div.get("data-source")
        return download_image(content, local_tempDir)
    else:
        div = soup.select("div.post__media > div.media img")[0]
        content = div.get("src")

        path = download_image(content, local_tempDir)

        content = Image.open(path)
        width, height = content.size
        content = content.crop((0, 0, width, height - 20))
        content.save(path)

        return path


def fetch_random_reddit_image_content(subreddit):
    r = requests.get("https://www.reddit.com/r/"+subreddit+"/random.json",
        headers={"User-agent": "Yotsubot getting a random post" + uuid.uuid4().hex}).content
    item = json.loads(r)[0].get("data").get("children")[0].get("data")
    domain = item.get("domain")
    url = item.get("url")
    print('fetch')
    if (domain == "i.redd.it" or domain == "i.imgur.com") and (url.endswith(".jpg") or url.endswith(".png")):
        return download_image(url, local_tempDir)
    else:
        return fetch_random_reddit_image_content(subreddit)


def download_image(url, path):
    if path[-1] == "/":
        parts = url.split('/');
        parts = parts[len(parts) - 1].split(".")
        extension = "." + parts[len(parts) - 1]
        name = str(uuid.uuid4().hex)
        path += name + extension
    elif os.path.exists(path):
        return None
    f = open(path, 'wb')  # create file locally
    f.write(requests.get(url).content)  # write image content to this file
    f.close()
    return path


def get_files_list(dbx, arg):
    file_list = []
    response = None
    if isinstance(arg, str):
        response = dbx.files_list_folder(arg)
    else:
        response = dbx.files_list_folder_continue(arg)
    for metadata in response.entries:
        strings = metadata.name.split(".")
        if len(strings) == 2:
            file_list.append(strings[0])
    if response.has_more:
        file_list.extend(get_files_list(dbx, response.cursor))
    return file_list


def file_exists(dbx, path, isOwner):
    try:
        result = dbx.files_get_metadata(dbx_reactions_dir + path)
        return True
    except:
        if not isOwner:
            try:
                result = dbx.files_get_metadata(dbx_reactions_for_approval_dir + path)
                return True
            except:
                return False
        return False


def save_react(dbx, url, path, isOwner):

    if isOwner:
        path = dbx_reactions_dir + path
    else:
        path = dbx_reactions_for_approval_dir + path

    result = dbx.files_save_url(path, url)
    jobid = result.get_async_job_id()
    while True:
        result = dbx.files_save_url_check_job_status(jobid)
        if result.is_complete():
            return True
        elif result.is_failed():
            return False


def auto_role_tagging():
    print('auto_role_tagging start')
    '''
    for i, role in enumerate(message.author.roles):
        message.author.roles[i] = str(role)

    if message.content == "%refresh" and message.author.roles.__contains__("Admin"):
        print("refreshing")
    '''
    '''
    for member in message.server.members:
        for i, role in enumerate(member.roles):
            member.roles[i] = str(role)
        if member.roles.__contains__("Bots"):
            continue

        if member.game != None:
            print(member.name,"playing",member.game.name)
        else:
            print(member.name, "is not playing")

    print(message.raw_role_mentions)
    print(message.content)

    channel = discord.utils.get(message.server.channels, name="general");
    print(channel.name)
    async for m in client.logs_from(channel, 9999):
        print(m.content)
    '''

async def react_old(self, message):
    args = message.content.split(" ")
    if len(args) == 1:
        return
    reactName = args[1]
    files = os.listdir("reactions")

    if reactName == "list":
        reactList = "";
        for file in files:
            react = file.split(".")[0]
            if react.startswith("loliPolice"):
                react = react[:-1]
            if not reactList.__contains__(react):
                reactList += react + "\n"
        reactList = reactList[:-1]
        em = discord.Embed(title="Reaction List", description=reactList)
        em.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        if message.author.id == owner_id:
            await self.client.send_message(self.channel_bot_pms, embed=em)
        else:
            await self.client.send_message(message.author, embed=em)
        return;
    elif reactName == "add" and message.author.id == owner_id:
        if len(message.attachments) == 0:
            em = discord.Embed(title="Command error", description="No attachments found")
            await self.client.send_message(message.channel, embed=em)
            return
        if len(args) != 3:
            em = discord.Embed(title="Command error", description="Invalid number of arguments")
            await self.client.send_message(message.channel, embed=em)
            return

        url = message.attachments[0].get("url")
        fileparts = message.attachments[0].get("filename").split(".")
        extension = "." + fileparts[len(fileparts)-1]

        #regex = "\s*(%s\d*\.\w*)\s*" % reactName
        #matches = re.findall(regex, " ".join(files))
        path = local_reactions_dir + args[2] + extension
        result = download_image(url, path)
        if result == None:
            em = discord.Embed(title="Command error", description="React name already exists")
            await self.client.send_message(message.channel, embed=em)
        else:
            em = discord.Embed(title="Command success", description="Added " + args[2])
            await self.client.send_message(message.channel, embed=em)
        #f = open(reactionsDir + args[2] + extension, 'wb')  # create file locally
        #f.write(requests.get(url).content)  # write image content to this file
        #f.close()
        return
    else:
        regex = "\s*(%s\d*\.\w*)\s*" % reactName
        matches = re.findall(regex, " ".join(files))
        path = ""
        if len(matches) == 0:
            print("React does not exists.")
            return
        elif len(matches) == 1:
            path = local_reactions_dir + matches[0]
        else:
            i = random.randrange(0,len(matches)-1)
            path = local_reactions_dir + matches[i]

        await self.client.send_file(message.channel, path)