from discord.ext.commands import CommandError


class NoMongo(CommandError):
    def __str__(self):
        return 'MongoDB is not present, album commands not available.'


def check_mongo(ctx):
    print('check')
    print(ctx.bot.db)
    if ctx.bot.db:
        return True
    raise NoMongo
