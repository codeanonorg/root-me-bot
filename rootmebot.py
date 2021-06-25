from database import Database
from model import ChallengeInfo, User
from pathlib import Path
import os
from asyncio.tasks import sleep
from typing import Union
import requests
import json
from discord.ext import commands
from discord.ext.tasks import loop
from urllib import parse
from embeds import *

ROOT_DIR = Path(__file__).parent

bot = commands.Bot(command_prefix='!')
base_url = os.environ.get("ROOTME_API_URL", "https://api.www.root-me.org/")
api_key = os.environ["ROOTME_API_KEY"]
filename = Path(os.environ.get("BOT_DATABASE_PATH", ROOT_DIR / "data.json"))
rootmechannel = int(os.environ["BOT_CHANNEL_ID"])
bot_token = os.environ["BOT_TOKEN"]
update_db_rate = int(os.environ.get("ROOTME_UPDATE_DB_RATE", 60))

database = Database(filename, autocommit=True)


def get_user_info(userID: str) -> Union[User, None]:
    """get user info from the root-me API using the user ID"""
    data = requests.get(base_url + "auteurs/" + userID,
                        cookies={"api_key": api_key})
    print(data.status_code)
    if data.status_code == 200:
        return User(**data.json())  # type: ignore
    else:
        print("error getting user info")
        return None


@loop(seconds=update_db_rate)
async def update_db():
    await bot.wait_until_ready()
    """update the local data from the API and check for solves"""

    with database.transaction():
        for user in database.iter_users():
            new_user_data = get_user_info(user.id_auteur)
            if not new_user_data:
                continue
            for challenge in new_user_data.validations:
                if challenge not in user.validations:
                    challenge_info = ChallengeInfo(**requests.get(
                        base_url + f"challenges/{challenge.id_challenge}",
                        cookies={
                            "api_key": api_key
                        }).json())  # type: ignore
                    print(challenge_info)
                    channel = bot.get_channel(rootmechannel)
                    if channel is None:
                        raise ValueError(
                            f"Channel ID {rootmechannel!r} does not exist")
                    await channel.send(
                        embed=makeChallengeEmbed(challenge_info, new_user_data)
                    )
            database.set_user(user)
            await sleep(0.05)


@bot.command()
async def add_user(context, user_id: str):
    """<user ID>"""
    print(context)
    try:
        if int(user_id) > 0:
            if (new_info := get_user_info(user_id)):
                database.set_user(new_info)
                await context.channel.send(
                    f"successfuly added user {new_info.nom}")
            else:
                await context.channel.send(f"error getting this user's info")
        else:
            await context.channel.send(f"user ID must be a positive integer")
    except ValueError:
        await context.channel.send(f"user ID must be a positive integer")


@bot.command()
async def find_user(context, username: str):
    """<user name>"""
    username = parse.quote(username, safe="")
    raw_data = requests.get(f"{base_url}auteurs?nom={username}",
                            cookies={"api_key": api_key})
    if (raw_data.status_code == 404):
        await context.channel.send("no match for this username")
    elif (raw_data.status_code == 401):
        await context.channel.send(
            "api key is not valid. Please provide me with a correct api at launch"
        )
    elif (raw_data.status_code != 200):
        await context.channel.send("unknown error")
    else:
        data = raw_data.json()
        usernameTuppleList = [(user['nom'], user['id_auteur'])
                              for user in data[0].values()]
        embed = makeFindEmbed(usernameTuppleList)
        await context.channel.send(embed=embed)


@bot.command()
async def remove_user(context, arg1):
    """<user ID>"""
    file = open(filename, "r")
    new_json = json.load(file)
    file.close()
    if arg1 in new_json:
        await context.channel.send(
            f"successfully removed user {new_json[arg1]['nom']}")
        new_json.pop(arg1)
        file = open(filename, "w")
        json.dump(new_json, file, indent=4)
        file.close()
    else:
        await context.channel.send("this user is not registered")


@bot.command()
async def scoreboard(context):
    users = [(u.nom, u.score) for u in database.iter_users()]
    users.sort(key=lambda x: x[0])
    embed = makeScoreBoardEmbed(users)
    await context.channel.send(embed=embed)


#@bot.command()
#async def help(context):
#    embed = discord.Embed()
#    embed.add_field(name="list of commands", value = "add_user <user id> : register a user\nremove_user <user id> : unregister a user\nhelp : shows this message\nreset_database : unregister all users")
#    await context.channel.send(embed = embed)


@bot.command()
async def reset_database(context):
    database.reset()
    await context.channel.send("database has been reset")


update_db.start()
bot.run(bot_token)
