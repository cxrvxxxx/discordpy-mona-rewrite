from config import Config

def is_whitelisted(ctx):
    config_path = f'./config/{ctx.guild.id}.ini'
    config = Config(config_path)

    if config.get('cogs.whitelist', ctx.author.id):
        return True
    else:
        return False