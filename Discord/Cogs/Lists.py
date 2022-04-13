from nextcord import Member, Interaction, slash_command, SlashOption
from nextcord.ext import application_checks
from nextcord.ext.commands import Bot

from Discord.Controller.Lists import get_shop, get_inventory, edit_inventory, \
                                     delete_inventory, delete_item_inventory
from Discord.Cogs.Cog import MyCog
from Discord.Cogs.Items import _ITEM_PARAMETER


class Lists(MyCog):

    @application_checks.check(MyCog.curators_players_perf)
    @slash_command(name='shop', description='Посмотреть магазин предметов')
    async def shop(
        self, inter: Interaction,
        item_type: str = _ITEM_PARAMETER,
        page: int = SlashOption(
            name='страница',
            description='Страница с которой начать просмотр магазина',
            required=False,
            default=1
        )
    ):
        await get_shop(inter, self, item_type, page)
    

    @application_checks.check(MyCog.curators_players_perf)
    @slash_command(name='inv', description='Просмотреть инвентарь')
    async def inventory(
        self, inter: Interaction,
        item_type: str = _ITEM_PARAMETER,
        player: Member = SlashOption(
              name='игрок',
              description='Игрок, чей инвентарь вы хотите увидеть',
              required=False,
              default=None
        ),
        page: int = SlashOption(
            name='страница',
            description='Страница, с которой вы хотите начать просмотр инвентаря',
            required=False,
            default=1
        )
    ):
        await get_inventory(inter, self, item_type, player, page)

    _INVENTORY_PARAMETERS = {
        'player': SlashOption(
            name='игрок',
            description='Игрок у которого будет изменен инвентарь',
            required=False,
            default=None
        ),
        'for_all_countries': SlashOption(
            name='для-всех-стран',
            description='Изменить инвентари всем игрокам',
            required=False,
            default=False
        )
    }
    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='edit-inv', description='Изменить инвентарь')
    async def edit_inventory(
        self, inter: Interaction,
        item_type: str = _ITEM_PARAMETER,
        name: str = SlashOption(
            name='имя',
            description='Имя предмета, который будет добавлен в инвентарь'
        ),
        count: int = SlashOption(
            name='количество',
            description='Количество добавляемого предмета',
            required=False,
            default=1
        ),
        player: Member = _INVENTORY_PARAMETERS['player'],
        for_all_countries: bool = _INVENTORY_PARAMETERS['for_all_countries']
    ):
        await edit_inventory(inter, self, item_type, player, 
                             for_all_countries, name, count)
    
    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='del-inv-item', description='Удалить предмет из инвентаря')
    async def delete_inventory_item(
        self, inter: Interaction,
        item_type: str = _ITEM_PARAMETER,
        name: str = SlashOption(
            name='имя',
            description='Имя удаляемого предмета'
        ),
        player: Member = _INVENTORY_PARAMETERS['player'],
        for_all_countries: bool = _INVENTORY_PARAMETERS['for_all_countries']
    ):
        await delete_item_inventory(inter, self, item_type, player, 
                                    for_all_countries, name)
    
    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='del-inv', description='Удалить инвентарь')
    async def delete_inventory(
        self, inter: Interaction,
        item_type: str = _ITEM_PARAMETER,
        player: Member = _INVENTORY_PARAMETERS['player'],
        for_all_countries: bool = _INVENTORY_PARAMETERS['for_all_countries']
    ):
        await delete_inventory(inter, self, item_type, player, for_all_countries)


def setup(bot: Bot):
    bot.add_cog(Lists(bot))
