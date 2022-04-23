from nextcord import Member, Interaction, slash_command, SlashOption
from nextcord.ext import application_checks
from nextcord.ext.commands import Bot

from Discord.Controller.Lists import get_shop, get_inventory, edit_inventory, \
                                     delete_inventory, delete_item_inventory
from Discord.Cogs.Cog import MyCog
from Discord.Cogs.Config import list_items
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
        'name': SlashOption(
            name='имя',
            description='Имя предмета, который будет изменен'
        ),
        'count': SlashOption(
            name='количество',
            description='Количество добавляемого предмета',
            required=False,
            default=1
        ),
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
    @slash_command(name='edit-inv-build', description='Изменить инвентарь зданий')
    async def edit_inventory_build(
        self, inter: Interaction,
        name: str = _INVENTORY_PARAMETERS['name'],
        count: int = _INVENTORY_PARAMETERS['count'],
        player: Member = _INVENTORY_PARAMETERS['player'],
        for_all_countries: bool = _INVENTORY_PARAMETERS['for_all_countries']
    ):
        await edit_inventory(
            inter, self, 'build', player, 
            for_all_countries, list_items().items['builds'][name], count
        )

    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='edit-inv-unit', description='Изменить инвентарь юнитов')
    async def edit_inventory_unit(
        self, inter: Interaction,
        name: str = _INVENTORY_PARAMETERS['name'],
        count: int = _INVENTORY_PARAMETERS['count'],
        player: Member = _INVENTORY_PARAMETERS['player'],
        for_all_countries: bool = _INVENTORY_PARAMETERS['for_all_countries']
    ):
        await edit_inventory(
            inter, self, 'unit', player, 
            for_all_countries, list_items().items['units'][name], count
        )

    _DELETE_INVENTORY_ITEM_PARAMETERS = {
            'name': SlashOption(
                name='имя',
                description='Имя удаляемого предмета'
            )
    }
    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='del-inv-build', description='Удалить здание из инвентаря')
    async def delete_inventory_build(
        self, inter: Interaction,
        name: str = _DELETE_INVENTORY_ITEM_PARAMETERS['name'],
        player: Member = _INVENTORY_PARAMETERS['player'],
        for_all_countries: bool = _INVENTORY_PARAMETERS['for_all_countries']
    ):
        await delete_item_inventory(
                inter, self, 'build', player, 
                for_all_countries, list_items().items['builds'][name]
        )

    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='del-inv-unit', description='Удалить юнита из инвентаря')
    async def delete_inventory_unit(
        self, inter: Interaction,
        name: str = _DELETE_INVENTORY_ITEM_PARAMETERS['name'],
        player: Member = _INVENTORY_PARAMETERS['player'],
        for_all_countries: bool = _INVENTORY_PARAMETERS['for_all_countries']
    ):
        await delete_item_inventory(
                inter, self, 'build', player, 
                for_all_countries, list_items().items['units'][name]
        )

    @edit_inventory_build.on_autocomplete('name')
    @delete_inventory_build.on_autocomplete('name')
    async def inv_build_autocomplete(self, inter: Interaction, name: str):
        await inter.response.send_autocomplete(
                list_items().get_same_items(list_items().items['builds'], name)
        )

    @edit_inventory_unit.on_autocomplete('name')
    @delete_inventory_unit.on_autocomplete('name')
    async def inv_unit_autocomplete(self, inter: Interaction, name: str):
        await inter.response.send_autocomplete(
                list_items().get_same_items(list_items().items['units'], name)
        )
    
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
