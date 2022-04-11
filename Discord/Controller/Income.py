import sys; sys.path.append('..'); sys.path.append('.')
from datetime import time

from nextcord import Interaction

from Service.Income import Income
from Discord.Cogs.Cog import MyCog


async def get_income_times(inter: Interaction, cog: MyCog,
                           income: Income):
    income_times = income.get_income_times()

    await cog.send(inter, 'Income Times', 'Времена выдачи: '+', '.join(income_times)+
                                          '\nВремя в МСК')


async def add_income_time(inter: Interaction, cog: MyCog, 
                          income: Income, time: time):
    income.add_income_time(time)

    await cog.send(inter, 'Add Income Time', 'Вермя выдачи дохода добавлено')

async def delete_income_time(inter: Interaction, cog: MyCog,
                             income: Income, time: time):
    income.delete_income_time(time)

    await cog.send(inter, 'Delete Income Time', 'Время выдачи дохода удалено')