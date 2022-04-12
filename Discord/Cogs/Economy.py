from nextcord import Member, Interaction, slash_command, SlashOption
from nextcord.ext import application_checks
from nextcord.ext.commands import Bot

from Discord.Controller.Economy import get_balance, edit_money, delete_money, pay
from Discord.Cogs.Cog import MyCog


class Economy(MyCog):

    @application_checks.check(MyCog.curators_players_perf)
    @slash_command(name='balance', description='Узнать свой баланс и доход')
    async def get_balance(self, inter: Interaction,
                          player: Member = SlashOption(
                              name='игрок',
                              description='Игрок, баланс которого вы хотите посмотреть',
                              required=False,
                              default=None
                          )
    ):
        if player := await self.get_player(inter, player):
            await get_balance(inter, self, player)

    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='edit-money', description='Изменить деньги стране/странам')
    async def edit_money(self, inter: Interaction,
                         money: float = SlashOption(
                             name='деньги',
                             description='Значение на которое изменится баланс'
                         ),
                         player: Member = SlashOption(
                             name='игрок',
                             description='Игрок, чей баланс вы хотите изменить',
                             required=False,
                             default=None
                         ),
                         for_all_countries: bool = SlashOption(
                             name='для-всех-стран',
                             description='Если верно, то изменит деньги всем странам',
                             required=False,
                             default=None
                         )
    ):
        await edit_money(inter, self, money, player, for_all_countries)

    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='del-money', description='Удалить все деньги стране/странам')
    async def delete_money(self, inter: Interaction,
                           player: Member = SlashOption(
                               name='игрок',
                               description='Игрок, чей баланс будет удален',
                               required=False,
                               default=None
                           ),
                           for_all_countries: bool = SlashOption(
                               name='для-всех-стран',
                               description='Если верно, то удалятся все деньги стран',
                               required=False,
                               default=None
                           )
    ):
        await delete_money(inter, self, player, for_all_countries)
    
    @application_checks.check(MyCog.players_perf)
    @slash_command(name='pay', description='Перевести деньги')
    async def pay(self, inter: Interaction,
                  payee: Member = SlashOption(
                      name='получатель',
                      description='Игрок которому придут деньги'
                  ),
                  money: float = SlashOption(
                      name='деньги',
                      description='Отправляемые деньги'
                  )
    ):
        if self.check_player(payee):
            await pay(inter, self, inter.user, payee, money)


def setup(bot: Bot):
    bot.add_cog(Economy(bot))
