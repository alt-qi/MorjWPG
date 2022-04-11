import traceback
import sys

from nextcord import Interaction
from nextcord.errors import ApplicationInvokeError
from nextcord.ext.commands import Cog, Bot
from nextcord.ext import application_checks

from Discord.Cogs.exceptions import IsntCurator, IsntRuler, NoAnswer
from Discord.Controller.exceptions import NoItemsThatName, WrongFormParameter
from Service.exceptions import CantTransact


class Events(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
    
    @Cog.listener()
    async def on_application_command_error(self, inter: Interaction, error: Exception):
        if isinstance(error, ApplicationInvokeError):
            error = error.original

        if isinstance(error, application_checks.errors.ApplicationMissingRole):
            message = ':x: У вас не достаточно прав для этого'
        
        elif isinstance(error, IsntCurator):
            message = ':x: Вы не куратор'
        elif isinstance(error, IsntRuler):
            message = ':x:'+str(error)
        
        elif isinstance(error, NoAnswer):
            message = ':x: Я не дождался ответа'

        elif isinstance(error, NoItemsThatName):
            message = ':x:'+str(error)
        elif isinstance(error, WrongFormParameter):
            message = ':x:'+str(error)

        elif isinstance(error, CantTransact):
            message = ':x:'+str(error)
            
        else:
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            return
        
        await inter.send(message)


def setup(bot: Bot):
    bot.add_cog(Events(bot))