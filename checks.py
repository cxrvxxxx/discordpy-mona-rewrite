from config import Config

def is_whitelisted(ctx):
    config_path = f'./config/{ctx.guild.id}.ini'
    config = Config(config_path)

    if config.get('cogs.whitelist', ctx.author.id):
        return True
    else:
        return False

def whitelist_level(ctx, level=0):
    config_path = f'./config/{ctx.guild.id}.ini'
    config = Config(config_path)

    access = config.getint('cogs.whitelist', ctx.author.id)

    if access >= level:
        return True
    else:
        return False