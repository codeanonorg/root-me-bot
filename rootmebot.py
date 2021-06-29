import os
from asyncio.tasks import sleep
import logging
from pathlib import Path
from typing import Union
from urllib import parse
from discord.ext.commands.errors import UserInputError

import requests
from discord.ext import commands
from discord.ext.tasks import loop

from database import Database
from embeds import *
from model import ChallengeInfo, User

ROOT_DIR = Path(__file__).parent

bot = commands.Bot(command_prefix='!')
base_url = os.environ.get("ROOTME_API_URL", "https://api.www.root-me.org/")
api_key = os.environ["ROOTME_API_KEY"]
filename = Path(os.environ.get("BOT_DATABASE_PATH", ROOT_DIR / "data.json"))
rootmechannel = int(os.environ["BOT_CHANNEL_ID"])
bot_token = os.environ["BOT_TOKEN"]
update_db_rate = int(os.environ.get("ROOTME_UPDATE_DB_RATE", 60))

database = Database(filename, autocommit=True)

logger = logging.getLogger(__name__)


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
    """update the local data from the API and check for solves"""
    logger.debug("update_db()")
    await bot.wait_until_ready()

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
            database.set_user(new_user_data)
            await sleep(0.05)


@bot.command()
async def add_user(context, user_id: str):
    """<user ID>"""
    logger.info("Adding user %r", user_id)
    try:
        if int(user_id) > 0:
            if (new_info := get_user_info(user_id)):
                database.set_user(new_info)
                logger.debug("Resolved id %r -> %r", user_id, new_info.nom)
                await context.channel.send(
                    f"successfuly added user {new_info.nom}")
            else:
                logger.warn("Couldn't get user info for id %r", user_id)
                await context.channel.send(f"error getting this user's info")
        else:
            logger.error("User ID must be a positive integer (got %r)",
                         user_id)
            await context.channel.send(f"user ID must be a positive integer")
    except ValueError as ex:
        logger.exception("Value error: %s", str(ex), exc_info=ex)
        await context.channel.send(f"user ID must be a positive integer")


@bot.command()
async def find_user(context, username: str):
    """<user name>"""
    username = parse.quote(username, safe="")
    logger.info("Find user %r", username)
    raw_data = requests.get(f"{base_url}auteurs?nom={username}",
                            cookies={"api_key": api_key})
    if (raw_data.status_code == 404):
        logger.error("User %r not found", username)
        await context.channel.send("no match for this username")
    elif (raw_data.status_code == 401):
        logger.error("Invalid API Key, got Unauthorized status")
        await context.channel.send(
            "api key is not valid. Please provide me with a correct api at launch"
        )
    elif (raw_data.status_code != 200):
        logger.error("Got response status code %i", raw_data.status_code)
        await context.channel.send("unknown error")
    else:
        data = raw_data.json()  # type: ignore
        matched_users = [(user['nom'], user['id_auteur'])
                         for user in data[0].values()]
        logger.debug("Found %d matching user profiles", len(matched_users))
        embed = makeFindEmbed(matched_users)
        await context.channel.send(embed=embed)


@bot.command()
async def remove_user(context, user_id: str):
    """<user ID>"""
    if (user := database.remove_user(user_id)):
        logger.info("Removed user %r (ID: %s)", user.nom, user.id_auteur)
        await context.channel.send(f"Successfully removed user {user.nom}")
    else:
        logger.info("Remove user: ID %r does not exist", user_id)
        await context.channel.send("This user is not registered")


@bot.command()
async def scoreboard(context):
    logger.debug("Show scoreboard")
    users = [(u.nom, u.score) for u in database.iter_users()]
    users.sort(key=lambda x: int(x[1]), reverse = True)
    if len(users) == 0:
        await context.channel.send(
            "The list of users is empty. Please add users first!")
    else:
        embed = makeScoreBoardEmbed(users)
        await context.channel.send(embed=embed)


#@bot.command()
#async def help(context):
#    embed = discord.Embed()
#    embed.add_field(name="list of commands", value = "add_user <user id> : register a user\nremove_user <user id> : unregister a user\nhelp : shows this message\nreset_database : unregister all users")
#    await context.channel.send(embed = embed)


@bot.command()
async def reset_database(context):
    logger.debug("Reset database")
    database.reset()
    await context.channel.send("database has been reset")


if __name__ == "__main__":
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            'level={levelname} module={name!r} message={message!r}',
            style='{'))
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)

    update_db.start()
    logger.info("Starting bot")
    bot.run(bot_token)
