from datetime import time

from nextcord import Interaction, slash_command, SlashOption
from nextcord.ext import application_checks
from nextcord.ext.commands import Bot

from Discord.Controller.Income import get_income_times, add_income_time, delete_income_time
from Discord.Cogs.Cog import MyCog
from Discord.Cogs.Config import Config
from Service.Income import Income


class CogIncome(MyCog):
    income: Income

    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.income = Income()

        self.income.add_observer(self)
    
    def update(self):
        channel = self.bot.get_channel(Config().publisher_channel)

        self.bot.loop.create_task(channel.send('Я выдал доход'))
    

    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='income', description='Выдать доход')
    async def get_out_income(self, inter: Interaction):
        self.income.income()
    
    @application_checks.check(MyCog.curators_players_perf)
    @slash_command(name='income-times', description='Посмотреть времена выдачи дохода')
    async def income_times(self, inter: Interaction):
        await get_income_times(inter, self, self.income)
    

    _INCOME_TIME = {
        'hours': SlashOption(
            name='час',
            description='Час выдачи дохода(в МСК)',
            min_value=0,
            max_value=24
        ),
        'minutes': SlashOption(
            name='минуты',
            description='Минуты выдачи дохода(в МСК)',
            min_value=0,
            max_value=59,
        )
    }
    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='add-income-time', description='Добавить время дохода')
    async def add_income_time(self, inter: Interaction,
                              hours: int = _INCOME_TIME['hours'],
                              minutes: int = _INCOME_TIME['minutes']
    ):
        await add_income_time(inter, self, self.income, time(hours, minutes))
    
    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='del-income-time', description='Удалить время дохода')
    async def delete_income_time(self, inter: Interaction,
                                 hours: int = _INCOME_TIME['hours'],
                                 minutes: int = _INCOME_TIME['minutes']
    ):
        await delete_income_time(inter, self, self.income, time(hours, minutes))

def setup(bot: Bot):
    bot.add_cog(CogIncome(bot))
