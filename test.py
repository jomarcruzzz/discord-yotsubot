import re
import os
import requests
from bs4 import BeautifulSoup as BS
from PIL import Image
import praw
import time
import random
import uuid
import json

files = os.listdir("reactions")
files.append('loliPolice4.jpg')
print(" ".join(files))
#regex = ".\s(%s[0-9]*\.\w*).\s" % "loliPolice"
regex = "\s*(%s\d*\.\w*)\s*" % "aiGood"
print(regex)
matches = re.findall(regex, " ".join(files))
print(matches)

print("asdqweasd".replace("asd","qwe",1))

'''
url = "https://cdn.discordapp.com/attachments/370073365907767298/371802004688863253/FB_IMG_1492378612678.jpg"
f = open('test.jpg','wb')  #create file locally
f.write(requests.get(url).content)  #write image content to this file
f.close()
'''
#"https://ifunny.co/feeds/shuffle"
#"https://ifunny.co/fun/5guVpF5a2"
'''
ifunny = requests.get("https://ifunny.co/feeds/shuffle").content
soup = BS(ifunny,"html.parser")

div = soup.select("div.post__media > div.media")[0]
data_type = div.get("data-type")

if(data_type == "video"):
    print("recurse")
elif(data_type == "image"):
    print('gif content')
    content = div.get("data-source")
    print(content)
else:
    div = soup.select("div.post__media > div.media img")[0]
    content = div.get("src")
    f = open('tmp/test.jpg', 'wb')  # create file locally
    f.write(requests.get(content).content)  # write image content to this file
    f.close()
    test = Image.open("tmp/test.jpg")
    test.show()
    width, height = test.size
    print(width, height)
    test = test.crop((0,0,width,height-20))
    test.show()
    test.save("tmp/test2.jpg")
    print(content)

'''
'''
r = praw.Reddit(client_id='evotNYj0m13_hA', client_secret='xFWsYOv7WVKinLFWA1hftDVZzJs',user_agent='Yotsubot')
random_time = random.randrange(1356998400,int(time.time()))
posts = r.subreddit('aww').
i = 0
for post in posts:
    print(post.title)
    i += 1
print("Total:",i)
'''
'''
r = requests.get("https://www.reddit.com/r/aww/random.json",headers = {'User-agent': 'Yotsubot getting a random post'+uuid.uuid4().hex}).content
a = json.loads(r)
print(a[0].get('data').get('children')[0].get('data').get('domain'))
#if(domain == "i.redd.it" or domain == "imgur.com"):
'''
domain = "i.imgur.com"
url = "https://i.imgur.com/xQnyb1s.gifv"

if domain == "i.redd.it" or domain == "i.imgur.com" and (url.endswith(".jpg") or url.endswith(".png")):
    print("accepted")
else:
    print("recurse")
