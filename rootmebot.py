from asyncio.tasks import sleep, wait
from discord import channel
import requests
try:
    import simplejson as json
except ImportError:
    import json
import discord
from discord.ext import commands
from discord.ext.tasks import loop
from urllib import parse
from embeds import *

bot = commands.Bot(command_prefix = '!')
#bot.remove_command("help")
base_url = "https://api.www.root-me.org/"
api_key = input("enter api key:")
#api_key = ""
filename = "data.json"
rootmechannel = 782199856181149706 #root-me-news
bot_token = ""

def getUserInfo(userID):
    """get user info from the root-me API using the user ID"""
    data = requests.get(base_url + "auteurs/" + userID, cookies = {"api_key" : api_key})
    print(data.status_code)
    if data.status_code == 200:
        return data.json()
    else:
        print("error getting user info")
        return 0


@loop(seconds=30)
async def updateDB():
    await bot.wait_until_ready()
    """update the local data from the API and check for solves"""
    print("updating")
    file = open(filename, "r")
    users = json.load(file)
    file.close()

    for user in users.values():
        new_user_data = getUserInfo(user["id_auteur"])
        for challenge in new_user_data["validations"]:
            if challenge not in user["validations"]:
                challenge_info = requests.get(base_url + f"challenges/{challenge['id_challenge']}", cookies = {"api_key" : api_key}).json()
                print(challenge_info)
                channel = bot.get_channel(rootmechannel)
                await channel.send(embed = makeChallengeEmbed(challenge_info, new_user_data))
        users[user["id_auteur"]] = new_user_data
        await sleep(0.05)
    file = open(filename, "w")
    json.dump(users, file, indent=4)
    file.close()

@bot.command()
async def add_user(context, arg1):
    """<user ID>"""
    try:
        if int(arg1) > 0:
            file = open(filename, "r")
            new_json = json.load(file)
            new_info = getUserInfo(arg1)
            file.close()
            if new_info != 0:
                new_json[new_info["id_auteur"]] = new_info
                file = open(filename, "w")
                json.dump(new_json, file, indent=4)
                file.close()
                await context.channel.send(f"successfuly added user {new_info['nom']}")
            else:
                await context.channel.send(f"error getting this user's info")
        else:
            await context.channel.send(f"user ID must be a positive integer")
    except ValueError:
        await context.channel.send(f"user ID must be a positive integer")

@bot.command()
async def find_user(context, arg1):
    """<user name>"""
    username = parse.quote(arg1, safe="")
    raw_data = requests.get(f"{base_url}auteurs?nom={username}", cookies= {"api_key" : api_key})
    if (raw_data.status_code == 404):
        await context.channel.send("no match for this username")
    elif (raw_data.status_code == 401):
        await context.channel.send("api key is not valid. Please provide me with a correct api at launch")
    elif (raw_data.status_code != 200):
        await context.channel.send("unknown error")
    else:
        data = raw_data.json()
        usernameTuppleList = [(user['nom'], user['id_auteur']) for user in data[0].values()]
        embed = makeFindEmbed(usernameTuppleList)
        await context.channel.send(embed = embed)
    


@bot.command()
async def remove_user(context, arg1):
    """<user ID>"""
    file = open(filename, "r")
    new_json = json.load(file)
    file.close()
    if arg1 in new_json:
        await context.channel.send(f"successfully removed user {new_json[arg1]['nom']}")
        new_json.pop(arg1)
        file = open(filename, "w")
        json.dump(new_json, file, indent=4)
        file.close()
    else:
        await context.channel.send("this user is not registered")

@bot.command()
async def scoreboard(context):
    users = []
    file = open(filename, "r")
    data = json.load(file)
    file.close()

    for user in data.values():
        users.append((user['nom'], user['score']))
    users.sort(key = lambda x : x[0])
    embed = makeScoreBoardEmbed(users)
    await context.channel.send(embed = embed)

#@bot.command()
#async def help(context):
#    embed = discord.Embed()
#    embed.add_field(name="list of commands", value = "add_user <user id> : register a user\nremove_user <user id> : unregister a user\nhelp : shows this message\nreset_database : unregister all users")
#    await context.channel.send(embed = embed)

@bot.command()
async def reset_database(context):
    empty = {}
    file = open(filename, "w")
    json.dump(empty, file)
    file.close()
    await context.channel.send("database has been reset")

updateDB.start()
bot.run("NjQyMDUwNjA4MjQ0NzE5NjQ2.XcRSOQ.5BwvmAHHB3VYS4LEPW6V4QzjgjY")