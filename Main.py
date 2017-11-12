# importing discord.py rewrite. Make sure you have it installed
import discord
import logging

# More imports
import asyncio
import datetime

# import database
import sqlite3

# More discord.py imports
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

# sets up discord.py logging in chat
logging.basicConfig(level=logging.INFO)


# Lets the prefix be changeable and set server by server
async def get_pre(bot, message):
    # Reads the database to get the prefix for that guild
    prefix = bot_config.read_database("bot_prefix", "guild_id", message.guild.id)
    # print("prefix =", prefix)

    # Checks if there was anything in the database for that server
    if prefix[0] != None:
        # If there was returns the prefix from the database plus poll
        return str(prefix[0]) + "poll "

    # Otherwise returns the default which is !poll
    return "!poll "  # or a list, ["pre1","pre2"]

def check_if_allowed_role(ctx):
    allowed_role = bot_config.read_database("allowed_role","guild_id", ctx.guild.id)
    if allowed_role[0] != None:
        return ctx.author.role == allowed_role[0]
    else:
        return True


# Simple bot descirption
description = '''A bot to easily gather information neatly from simple to answer polls.
Made by Tim#3506 and CodeCo#3866.'''

# Sets up the bot using the prefix function we made before and the description
bot = commands.Bot(command_prefix=get_pre, description=description)
# Overides the default python help command so we can use it.
bot.remove_command("help")


# Creates the bot config class
class bot_config:
    def __init__(self, guild_id):
        self.guild_id = guild_id

    # Function
    @classmethod
    def database_setup(cls):
        db = sqlite3.connect('poll_settings.db')
        cursor = db.cursor()
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS poll_settings(id INTEGER PRIMARY KEY, guild_id TEXT UNIQUE, poll_channel TEXT, allowed_role TEXT, ping_role TEXT, bot_prefix TEXT, colour TEXT)''')
        db.commit()
        return db, cursor

    @classmethod
    def database_write(cls, guild_id):
        db, cursor = cls.database_setup()
        cursor.execute('''INSERT OR IGNORE INTO poll_settings(guild_id, poll_channel, allowed_role, ping_role, bot_prefix, colour)
                          VALUES(?,?,?,?,?,?)''', (str(guild_id), None, None, None, None, None))
        db.commit()
        db.close()
        # if args != None:
        #    cls.database_update(args[0],args[1],"guild_id",guild_id)

    @classmethod
    def database_update(cls, field, value, check, check_value):
        db, cursor = cls.database_setup()
        cursor.execute('''UPDATE poll_settings SET ''' + str(field) + ''' = ? WHERE ''' + str(check) + ''' = ? ''',
                       (str(value), str(check_value)))
        db.commit()
        db.close()

    @classmethod
    def read_database(cls, field, check, check_value):
        db, cursor = cls.database_setup()
        cursor.execute('''SELECT ''' + field + ''' FROM poll_settings WHERE ''' + check + '''''''=?''',
                       (str(check_value),))
        value = cursor.fetchone()
        db.close()
        return value

        # @classmethod
        # def check_channel(cls,ctx):
        #    channel = cls.read_database("poll_channel", "guild_id", ctx.guild.id)
        #    if channel[0] == None:
        #        return ctx
        #    else: return bot.get_channel(channel)


class poll(object):
    def __init__(self, question, options, option_score=None):
        self.question = question
        self.options = options
        self.option_score = option_score


        # instance function to set up and send embed

    async def send_embed(self, ctx):
        # await ctx.send("<@&339409818064388096 >")
        i = 1
        if "?" not in self.question:
            self.question += "?"
        # sets up embed
        em = discord.Embed(title=bot.user.name, colour=0xF1F1F1, timestamp=datetime.datetime.today())
        em.description = "```yaml\n" + self.question + "```"
        em.set_thumbnail(url="https://cdn3.iconfinder.com/data/icons/complete-set-icons/512/graph.png")
        # iterates through options dict and adds to embed
        for x in self.options:
            em.description += "\n`" + str(i) + " | 0 | ` " + x
            i += 1
            if i > 9:
                break
        em.description += "\n\n Total Votes : 0"

        # sends embed
        print("│ ACTION: Sending Embed                            │")

        channel = bot_config.read_database("poll_channel","guild_id", ctx.guild.id)
        if channel[0] != None:
            channel = bot.get_channel(int(channel[0]))
        else:
            channel = ctx

        message = await channel.send(embed=em)
        em.set_footer(text="Poll ID : " + str(message.id))
        await message.edit(embed=em)
        await self.database_write(message, ctx)
        await self.add_reactions(message)

    '''async def new_vote(self, emoj):
        for x in range(1, (len(self.options) + 1)):
            if ("fe"+str(x)) in emoji.name.encode('utf-16'):
                print("+1 votes for "+self.options[x])'''

    # REACTION MANAGERS
    async def add_reactions(self, message):
        print(
            "│ ACTION: Adding Reactions                         │\n└──────────────────────────────────────────────────┘\n")
        for x in range(1, (len(self.options) + 1)):
            await message.add_reaction(str(x) + "\u20e3")
            asyncio.sleep(0.25)

    '''@classmethod
    async def get_values(cls, messgae_id):
        print(await bot.get_message(messgae_id))'''

    async def edit_upvote_message(self, message_id, channelid):
        i = 1
        print("editing message")
        print("options = ", self.options)
        print("optionscore = ", self.option_score)
        print("question =", self.question)
        em = discord.Embed(title=bot.user.name, colour=0xF1F1F1, timestamp=datetime.datetime.today())
        em.description = "```yaml\n" + self.question + "```"
        em.set_thumbnail(url="https://cdn3.iconfinder.com/data/icons/complete-set-icons/512/graph.png")
        # iterates through options dict and adds to embed
        for x in self.options:
            if x != None:
                em.description += "\n`" + str(i) + " | " + str(self.option_score[i - 1] - 1) + " |` " + str(x)
                i += 1
        em.description += "\n \nTotal Votes : " + await self.total_votes()
        print("made embed sending")
        message = await bot.get_channel(channelid).get_message(message_id)
        em.set_footer(text="Poll ID : " + str(message.id))
        await message.edit(embed=em)

    async def total_votes(self):
        total = 0
        for x in self.option_score:
            if x != None:
                total = total + x - 1
        return str(total)

    @classmethod
    async def get_upvote_value(cls, message_id, emoji):
        # print((emoji.name.encode('utf-16')))
        x = -4
        for i in range(0, 10):
            # print(("xfe"+str(i)))
            # print(("xfe"+str(i)) in str(emoji.name.encode('utf-16')))
            if ("fe" + str(i)) in str(emoji.name.encode('utf-16')):
                # print(i)
                poll = await cls.read_database("op" + str(i), "poll_id", message_id)
                print("upovte of ", poll[0])

                return i
        return False


        # for i in range(0#,len(poll)):
        #    if str(x) in str(emoji.name.encode('utf-16')):
        #        print(poll[i])
        #        return poll[i]
        #    x+=1

    # DATABASE
    @classmethod
    def database_setup(cls):
        db = sqlite3.connect('poll.db')
        cursor = db.cursor()
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS polls(id INTEGER PRIMARY KEY, poll_id TEXT, guild_id TEXT, created_by TEXT,
                                                question TEXT, op1 TEXT, op1Score INTEGER, op2 TEXT, op2Score INTEGER, op3 TEXT, op3Score INTEGER,
                                                op4 TEXT, op4Score INTEGER, op5 TEXT, op5Score INTEGER, op6 TEXT, op6Score INTEGER,
                                                op7 TEXT, op7Score INTEGER, op8 TEXT, op8Score INTEGER, op9 TEXT, op9Score INTEGER)
            ''')
        db.commit()
        return db, cursor

    async def database_write(self, message, ctx):
        db, cursor = self.database_setup()
        row = [str(message.id), str(message.guild.id), str(ctx.author.id), self.question]
        for i in range(0, 9):
            try:
                # print(self.options[i])
                row.append(self.options[i])
                row.append(0)
            except IndexError:
                row.append(None)
                row.append(None)
                # print("Failed")
                # print(row)

        cursor.execute('''INSERT INTO polls(poll_id, guild_id, created_by, question, op1, op1Score, op2, op2Score, op3, op3Score, op4, op4Score, op5,
                                            op5Score, op6, op6Score, op7, op7Score, op8, op8Score, op9, op9Score)
                                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (row))
        db.commit()
        db.close
        # await self.database_read(message)

    @classmethod
    async def read_database(cls, field, check, check_value):
        db, cursor = cls.database_setup()
        cursor.execute('''SELECT ''' + field + ''' FROM polls WHERE ''' + check + '''''''=?''', (str(check_value),))
        value = cursor.fetchone()
        db.close()
        return value

    @classmethod
    async def get_poll(cls, message_id):
        db, cursor = cls.database_setup()
        # print("message_id =",message_id)
        cursor.execute('''SELECT * FROM polls WHERE poll_id = ?''', (str(message_id),))
        poll = cursor.fetchone()
        # print("Poll = ", poll)
        db.close()
        return poll

    @classmethod
    async def update_database(cls, field, value, check, check_value):
        db, cursor = cls.database_setup()
        print(field)
        cursor.execute('''UPDATE polls SET ''' + str(field) + ''' = ? WHERE ''' + str(check) + ''' = ? ''',
                       (str(value), str(check_value)))
        db.commit()
        db.close()

    @classmethod
    async def create_poll_object(cls, message_id):
        poll = await cls.get_poll(message_id)
        poll = list(poll)
        question = poll[4]
        options = poll
        for i in range(0, 5):
            del options[0]
            # print(options)
        optionscore = options
        options = options[0::2]
        del optionscore[0]
        optionscore = optionscore[0::2]
        # print("option=",options)
        # print("optionscore=",optionscore)
        # print("question= ",question)
        return cls(question, options, optionscore)


# Message when bot starts up and is ready
@bot.event
async def on_ready():
    print('\n')
    print('┌────────────────────────────────────────────────────────┐')
    print('│', '      _____          _      ____        _       ', '      │')
    print('│', '     / ____|        | |    |  _ \      | |      ', '      │')
    print('│', '    | |     ___   __| | ___| |_) | ___ | |_ ___ ', '      │')
    print('│', '    | |    / _ \ / _` |/ _ \  _ < / _ \| __/ __|', '      │')
    print('│', '    | |___| (_) | (_| |  __/ |_) | (_) | |_\__ \\', '      │')
    print('│', '     \_____\___/ \__,_|\___|____/ \___/ \__|___/', '      │')
    print('│', '                                                       │')
    print('├────────────────────────────────────────────────────────┤')
    print('│', '                                                       │')
    print('│', 'Bot Info:', '                                             │')
    print('│', 'Version:      ', 'Poll 0.02 BETA                          │')
    print('│', 'Username:     ', bot.user.name, ('#'), bot.user.discriminator)
    print('│', 'User ID:      ', bot.user.id)
    print('│', 'Guild Count:  ', len(bot.guilds))
    print('│', '                                                       │')
    print('└────────────────────────────────────────────────────────┘')
    print('\n')
    print(' ~ ', 'If you require support, join the lounge at https://discord.gg/nj8EEwF')
    print(' ~ ', 'Check out our website at https://example.com/')
    print(' ~ ', 'You can view the documentaton from the website')
    print(' ~ ', 'Check out our website at https://example.com/')
    print(' ~ ', 'Code Polls created by Tim\u00233506 and CodeCo\u00233866')
    print('\n')
    print('INFO: This bot has been successfully loaded and is ready to be used.\n')

    await bot.change_presence(game=None)


@bot.command()
@commands.check(check_if_allowed_role)
@commands.cooldown(1, 10, BucketType.guild)
async def new(ctx, question: str, *options: commands.clean_content):
    print("┌──────────────────────────────────────────────────┐\n│ ACTION: Generating Poll in │", ctx.guild)
    polls = poll(question, options)
    await polls.send_embed(ctx)


async def help_embed(ctx):
    em = discord.Embed(title='Code Polls Help', colour=0xF1F1F1, timestamp=datetime.datetime.today())
    em.description = "**Commands**\n`!poll new \"Title\" One \"Option Two\" Three` - Creates a poll.\n`!poll settings channel #channel`- Sets the poll channel.\n`poll settings role \"Role Name, Role Name 2\"` - Sets the poll creation role(s).\n\n**Lounge**\nFeel free to pop into our Support Lounge at:\nhttps://discord.gg/nj8EEwF"
    em.set_thumbnail(url="https://cdn3.iconfinder.com/data/icons/complete-set-icons/512/graph.png")
    em.set_footer(text="Code Poll created by Tim#​3506 and CodeCo#​3866")
    await ctx.send(embed=em)

# HElP
@bot.group()
async def help(ctx):
    if ctx.invoked_subcommand is None:
        await help_embed(ctx)

@help.command()
async def settings(ctx):
    em = discord.Embed(title='Code Polls Setting Help', colour=0xF1F1F1, timestamp=datetime.datetime.today())
    em.description = "**Commands**\n`!poll settings change_prefix - Changes the command prefix for the server.\n\n`!poll settings channel #channel`- Sets the poll channel.\n`poll settings role \"Role Name, Role Name 2\"` - Sets the poll creation role(s)."
    em.set_thumbnail(url="https://cdn3.iconfinder.com/data/icons/complete-set-icons/512/graph.png")
    em.set_footer(text="Code Poll created by Tim#​3506 and CodeCo#​3866")
    await ctx.send(embed=em)



# SETTINGS

@bot.group()
async def settings(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Invalid settings command... Run `{}help settings` to get a list of commands'.format(await get_pre(ctx,ctx)))


@settings.command()
async def prefix(ctx, prefix: str):
    print("in Chnage prefix")
    print(prefix)
    bot_config.database_update("bot_prefix", prefix, "guild_id", ctx.guild.id)
    await ctx.send("You prefix is now " + prefix + ". A example command is `" + prefix + "poll help`")

@settings.command()
async def channel(ctx, channel : str):
    print("Channel Change")
    print(channel)
    bot_config.database_update("poll_channel", str(channel), "guild_id", ctx.guild.id)
    await ctx.send("Polls will now be posted in "+ str(ctx.guild.get_channel(int(channel))))


###TODO - UNFINISHED
@settings.command()
async def role(ctx, role_name : str):
    bot_config.database_update("allowed_roles", str(role_name))


@bot.command()
async def role_id(ctx, role_name : str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    await ctx.send("The role id for that is <@" + str(role.id) + ">")
    for i in ctx.author.roles:
        if role == i:
            print("you have that role")
# EVENTS
@bot.event
async def on_message(message):
    if "@here" in message.content or "@everyone" in message.content:
        pass
    elif bot.user.mentioned_in(message):
        await bot.get_channel(message.channel.id).send("Use the prefix `!poll` ")
        await help_embed(bot.get_channel(message.channel.id))

    bot_config.database_write(message.guild.id)
    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(emoji, message_id, channel_id, user_id):
    upvote = await poll.get_upvote_value(message_id, emoji)
    if upvote:
        current_value = await poll.read_database("op" + str(upvote) + "Score", "poll_id", message_id)
        await poll.update_database("op" + str(upvote) + "Score", current_value[0] + 1, "poll_id", message_id)
        polls = await poll.create_poll_object(message_id)
        await polls.edit_upvote_message(message_id, channel_id)

        # poll.update_database("op"+upvote[0],)
        # id = bot.get_channel(channel_id)
        # await id.send(str(bot.get_user(user_id).name) + " upvoted " + str(upvote[0]))


@bot.event
async def on_raw_reaction_remove(emoji, message_id, channel_id, user_id):
    # print(emoji.name.encode('utf-16'))
    upvote = await poll.get_upvote_value(message_id, emoji)
    if upvote != False:
        current_value = await poll.read_database("op" + str(upvote) + "Score", "poll_id", message_id)
        await poll.update_database("op" + str(upvote) + "Score", current_value[0] - 1, "poll_id", message_id)
        polls = await poll.create_poll_object(message_id)
        await polls.edit_upvote_message(message_id, channel_id)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.send(
            "Please wait " + "{:0.2f}".format(error.retry_after) + " seconds before you try the command again.")
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Sorry that command is unknown. Please run `{}help` to get more help".format(await get_pre(ctx,ctx)))
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        print(await get_pre(ctx,ctx))
        await ctx.send("Make sure you typed the whole command. Type `{}help` to a full list of commands. ".format(await get_pre(ctx,ctx)))
    else:
        print(error)


# bot token. Change here
bot.run('INSERT TOKEN')
