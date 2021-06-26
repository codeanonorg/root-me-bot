from model import ChallengeInfo, User
import discord

UserList = list[tuple[str, str]]


def makeFindEmbed(usersTuppleList: UserList):
    embed = discord.Embed()
    embed.title = "Users IDs matching your research (50 firsts)"
    userString = ""
    for name, userID in usersTuppleList:
        userString += f"{name} : {userID}\n"
    embed.add_field(name="Name : ID", value=userString)
    return embed


def makeChallengeEmbed(challenge: ChallengeInfo, user: User):
    embed = discord.Embed()
    embed.title = f"New challenge solved by {user.nom}"
    embed.add_field(name="Title :",
                    value=f"{challenge.titre} ({challenge.score} points)",
                    inline=False)
    embed.add_field(name="Category :",
                    value=f"{challenge.rubrique}",
                    inline=False)
    embed.add_field(name="Difficulty :",
                    value=f"{challenge.difficulte}",
                    inline=False)
    return embed


def makeRegisteredUsersEmbed(usersTuppleList: UserList):
    embed = discord.Embed()
    embed.title = "Registered users"
    userString = ""
    for name, userID in usersTuppleList:
        userString += f"{name} : {userID}\n"
    embed.add_field(name="Name : ID", value=userString)
    return embed


def makeScoreBoardEmbed(usersTuppleList: UserList):
    embed = discord.Embed()
    embed.title = "Scoreboard"
    userString = ""
    i = 1
    for name, score in usersTuppleList:
        userString += f"{i} - {name} : {score} points\n"
        i += 1
    embed.add_field(name="ranking by points", value=userString)
    return embed
