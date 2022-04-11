import sys; sys.path.append('..'); sys.path.append('.')

from nextcord import Interaction, Member

from Service.Economy import Economy
from Service.Country import OneCountry
from Discord.Cogs.Cog import MyCog
from Discord.Controller.Lists import get_country_parameters


async def get_balance(inter: Interaction, cog: MyCog, 
                      user: Member):
    country = OneCountry(cog.get_country_name(user))
    economy = Economy(country)

    money = economy.money()
    income = economy.income()

    await cog.send(inter, 'Balance', f'Деньги: {money}, Доход: {income}', user)

async def edit_money(inter: Interaction, cog: MyCog, money: float,
                     user: Member, for_all_countries: bool):
    if country := await get_country_parameters(inter, cog, user, for_all_countries):
        economy = Economy(country)
        economy.edit_money(money)

        await cog.send(inter, 'Edit Money', 'Деньги были изменены')

async def delete_money(inter: Interaction, cog: MyCog, 
                       user: Member, for_all_countries: bool):
    if country := await get_country_parameters(inter, cog, user, for_all_countries):
        economy = Economy(country)
        economy.delete_money()

        await cog.send(inter, 'Delete Money', 'Деньги были у всех удалены')

async def pay(inter: Interaction, cog: MyCog,
              payer: Member, payee: Member, money: float):
    country_payer = OneCountry(cog.get_country_name(payer))
    country_payee = OneCountry(cog.get_country_name(payee))

    economy = Economy(country_payer)
    economy.pay(country_payee, money)

    await cog.send(inter, 'Pay', 'Деньги переведены', payer)