import os
import discord
import instaloader
from discord.ext import commands
import datetime
import mysql.connector

client = commands.Bot(command_prefix="$")

# login
L = instaloader.Instaloader()
L.login(os.getenv('INSTAGRAM_USER'), os.getenv('INSTAGRAM_PASSWORD'))

# connect to the database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="password",
    database="instatracker"
)

cursor = db.cursor()

# get today and yesterday's date
today = datetime.datetime.now().strftime("%Y-%m-%d")
yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")


# running the bot
@client.event
async def on_ready():
    print("Logged in!")


# add a profile to the database
@client.command()
async def addprofile(ctx, arg):
    query = "SELECT * FROM user WHERE username = %s"
    args = (arg,)

    cursor.execute(query, args)

    # if profile is not found in the database
    if not cursor.rowcount:
        PROFILE = arg
        profile = instaloader.Profile.from_username(L.context, PROFILE)

        # insert instagram profile into database
        sql = "INSERT INTO profile (username, userid, pfp, discord_channel) VALUES (%s, %s, %s, %s)"
        values = (profile.username, str(profile.userid), profile.profile_pic_url, str(ctx.message.channel.id))

        cursor.execute(sql, values)
        db.commit()

        if cursor.rowcount >= 1:
            embed = discord.Embed(
                title="Success!",
                description="The profile has been added.",
                colour=discord.Colour.blue()
            )

            embed.add_field(name="Username", value=profile.username, inline=False)
            embed.add_field(name="UserID", value=str(profile.userid), inline=False)
            embed.add_field(name="In channel", value=str(ctx.message.channel.id), inline=False)
            embed.set_image(url=profile.profile_pic_url)

            await ctx.send(embed=embed)

        # if profile could not be added
        else:
            embed = discord.Embed(
                title="Error",
                description="There was an error adding the profile.",
                colour=discord.Colour.blue()
            )

            await ctx.send(embed=embed)
            
    # if profile is in the database
    else:
        embed = discord.Embed(
            title="Error",
            description="Your profile has already been added to the database.",
            colour=discord.Colour.blue()
        )

        await ctx.send(embed=embed)

# calculate the difference in followers
def calculateDifference(day1, day2):
    day2 = set(day2)
    return [follower for follower in day1 if follower not in day2]


# check followers of profile
@client.command()
async def checkFollowers(ctx):
    cursor.execute("SELECT * FROM user")
    values = cursor.fetchall()

    # get followers
    for value in values:
        PROFILE = value[1]
        profile = instaloader.Profile.from_username(L.context, PROFILE)
        numFollowers = set(profile.get_followers())

        for follower in numFollowers:
            sql = "INSERT INTO followers (username, userid, follows, day) VALUES (%s, %s, %s, %s)"
            values = (follower.username, str(follower.userid), str(profile.userid), today)

            cursor.execute(sql, values)
            db.commit()

        await calculateFollowers(ctx, value[2], value[4], profile)


async def calculateFollowers(ctx, userid, channel, profile):
    todayFollowers = []
    yesterdayFollowers = []

    # today's followers
    query = "SELECT * FROM followers WHERE day = %s AND follows = %s"
    args = (today, userid)
    cursor.execute(query, args)
    followers = cursor.fetchall()

    for follower in followers:
        todayFollowers.append(follower[2])

    # yesterday's followers
    query = "SELECT * FROM followers WHERE day = %s AND follows = %s"
    args = (yesterday, userid)
    cursor.execute(query, args)
    followers = cursor.fetchall()

    for follower in followers:
        yesterdayFollowers.append(follower[2])

    followed = []
    unfollowed = []
    differences = calculateDifference(todayFollowers, yesterdayFollowers)

    # find new/removed followers
    for difference in differences:
        query = "SELECT * FROM followers WHERE userid = %s ORDER BY id LIMIT 1"
        args = (difference,)

        cursor.execute(query, args)
        values = cursor.fetchall()

        if difference in todayFollowers:
            for user in values:
                followed.append(user[1] + " <" + difference + ">")

        elif difference in yesterdayFollowers:
            for user in values:
                unfollowed.append(user[1] + " <" + difference + ">")

    unfollowedProfiles = 0
    unfollowEmbed = ""

    for profile in unfollowed:
        unfollowedProfiles += 1

        if unfollowedProfiles == 1:
            unfollowEmbed = profile
        else:
            unfollowEmbed += "\n" + profile

    if unfollowedProfiles == 0:
        unfollowEmbed = "No one!"

    followedProfiles = 0
    followEmbed = 0

    for profile in followed:
        followedProfiles += 1

        if followedProfiles == 1:
            followEmbed = profile
        else:
            followEmbed += "\n" + profile

    if followedProfiles == 0:
        followEmbed = "No one!"

    # send at 8:30 am
    if datetime.datetime.now().strftime("%H") == "8" and datetime.datetime.now().strftime("%H") == "30":
        embed = discord.Embed(
            title="Your Instagram Summary:",
            colour=discord.Colour.blue()
        )
        embed.set_thumbnail(url=profile.profile_pic_url)
        embed.add_field(name="Username", value=profile.username, inline=True)
        embed.add_field(name="UserID", value=str(profile.userid), inline=True)
        embed.add_field(name="Yesterday's Followers", value=str(len(yesterdayFollowers)), inline=False)
        embed.add_field(name="Today's Followers", value=str(len(todayFollowers)), inline=False)
        embed.add_field(name="New followers", value=followEmbed, inline=False)
        embed.add_field(name="Unfollowers", value=unfollowEmbed, inline=False)

        await ctx.send_message(discord.Object(id=str(channel)), embed=embed)

client = discord.Client()
client.run("TOKEN")
