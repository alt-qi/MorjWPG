import sys; sys.path.append('..'); sys.path.append('.')
from typing import Any

import regex
from nextcord import Interaction, Member

from Service.Items import Item, Build, ItemFabric
from Service.Country import OneCountry
from Controller.exceptions import NoItemsThatName
from Discord.Cogs.Cog import MyCog


async def create_item(
        inter: Interaction, cog: MyCog, 
        item_type: str, parameters: dict[str, Any]
):
    try:
        item = ItemFabric().get_item(item_type)
        item_parameters = await get_parameters(inter, cog, parameters)
        
        item.insert(item_parameters)
        await cog.send(inter, 'Create Item', 'Предмет создан')
    finally:
        cog.get_all_items()

async def update_item(
        inter: Interaction, cog: MyCog, item_type: str, 
        item_id: int, parameters: dict[str, Any]
):
    try:
        del_needed_for_purchase = False
        item = ItemFabric().get_item(item_type)
        if parameters['needed_for_purchase'] == '-':
            parameters.pop('needed_for_purchase')
            del_needed_for_purchase = True

        item_parameters = await get_parameters(inter, cog, parameters)
        if del_needed_for_purchase:
            item_parameters['needed_for_purchase'] = {}

        item.update(item_id, item_parameters)

        await cog.send(inter, 'Update Item', 'Предмет обновлен')
    finally:
        cog.get_all_items()

async def delete_item(
        inter: Interaction, cog: MyCog, 
        item_type: str, item_id: int
):
    try:
        item = ItemFabric().get_item(item_type)
        item.delete(item_id)
    
        await cog.send(inter, 'Delete Item', 'Предмет удален')
    finally:
        cog.get_all_items()


async def buy_item(
        inter: Interaction, cog: MyCog, item_type: str, 
        user: Member, item_id: int, count: int
):
    item = ItemFabric().get_item(item_type)
    country = OneCountry(cog.get_country_name(user))

    item.buy(country, item_id, count)

    await cog.send(inter, 'Buy Item', 'Предмет куплен')

async def sell_item(
        inter: Interaction, cog: MyCog, item_type: str,
        seller: Member, customer: Member, 
        item_name: str, item_id: int, 
        count: str, price: float
):
    item = ItemFabric().get_item(item_type)
    seller_country = OneCountry(cog.get_country_name(seller))
    customer_country = OneCountry(cog.get_country_name(customer))

    switch = await cog.confirm(
        inter, customer, 
        f'{customer.mention}, вы согласны купить {count} {item_name} за {price}?'
    )

    if switch:
        item.sell(
                seller_country, customer_country, 
                item_id, count, price
        )
    
        await cog.send(inter, 'Sell Item', 'Предмет продан')
    else:
        return


_DEFAULT_VALUE = None

_SHOULD_NOT_BE = '!'
_ANYTHING = '|'
_GET_NEEDED_FOR_PURCHASE_PARAMETERS_PATTERN = rf'^([{_SHOULD_NOT_BE}{_ANYTHING}]*)\('
async def get_parameters(
        inter: Interaction, cog: MyCog,
        parameters: dict[str, Any]
) -> dict[str, Any]:
    item_parameters = {}

    for parameter in parameters:
        if parameters[parameter] == _DEFAULT_VALUE:
            continue

        if parameter == 'needed_for_purchase':
            if group_needed_for_purchase_parameters := regex.findall(
                    _GET_NEEDED_FOR_PURCHASE_PARAMETERS_PATTERN, 
                    parameters[parameter]
            ):
                group_needed_for_purchase_parameters = \
                        group_needed_for_purchase_parameters[0][0]

                parameters[parameter] = regex.sub(
                        _GET_NEEDED_FOR_PURCHASE_PARAMETERS_PATTERN, 
                        '', parameters[parameter]
                )[:-1]

            value = await get_needed_for_purchase_group(
                    inter, cog, group_needed_for_purchase_parameters, 
                    parameters[parameter]
            )

        else:
            value = parameters[parameter]

        item_parameters[parameter] = value
    
    return item_parameters

# Получение групп необходимых для покупки зданий по типу !|(Мельница: 2, (Завод: 1), Шахта: 3)
_GET_GROUPS_PATTERN = rf'([{_SHOULD_NOT_BE}{_ANYTHING}]*)\(((?:[^)(]++|(?R))*)\)(, [ ]*)?'
async def get_needed_for_purchase_group(
        inter: Interaction, cog: MyCog, 
        parameters: str, needed_for_purchase: str
) -> dict[str, Any]:
    group_needed_for_purchase = {'parameters': {}, 'needed_for_purchase': [], 'groups': []}

    _get_group_parameters(parameters, group_needed_for_purchase)
    await _get_needed_for_purchase_groups(
            inter, cog, needed_for_purchase, group_needed_for_purchase
    )
    await _get_needed_for_purchases(
            inter, cog, 
            regex.sub(_GET_GROUPS_PATTERN, ' ', needed_for_purchase), 
            group_needed_for_purchase
    )

    return group_needed_for_purchase


def _get_group_parameters(parameters: str, group_needed_for_purchase: dict[str, Any]):
    if _SHOULD_NOT_BE in parameters:
        group_needed_for_purchase['parameters']['should_not_be'] = True
    if _ANYTHING in parameters:
        group_needed_for_purchase['parameters']['type'] = 'Any'

async def _get_needed_for_purchase_groups(
        inter: Interaction, cog: MyCog,
        needed_for_purchase: str, group_needed_for_purchase: dict[str, Any]
):
    groups = regex.findall(_GET_GROUPS_PATTERN, needed_for_purchase)
    for group in groups:
        group_needed_for_purchase['groups'].append(
                await get_needed_for_purchase_group(inter, cog, group[0], group[1])
        )

_PROPORTIONALLY = '*'
_GET_NEEDED_FOR_PURCHASES_PATTERN = rf'([{_SHOULD_NOT_BE}{_PROPORTIONALLY}]*)([а-яА-я\w ]+):[ ]*(\d+)'
async def _get_needed_for_purchases(
        inter: Interaction, cog: MyCog,
        needed_for_purchases: str, group_needed_for_purchase: dict[str, Any]
):
    needed_for_purchases = regex.findall(_GET_NEEDED_FOR_PURCHASES_PATTERN, needed_for_purchases)
    for needed_for_purchase in needed_for_purchases:
        needed_for_purchase_group = {}
        if _SHOULD_NOT_BE in needed_for_purchase[0]:
            needed_for_purchase_group['should_not_be'] = True
        if _PROPORTIONALLY in needed_for_purchase[0]:
            needed_for_purchase_group['proportionally_items'] = True

        build_id = await get_item_id(inter, cog, Build(), needed_for_purchase[1])
        needed_for_purchase_group['needed_build_id'] = build_id

        count = int(needed_for_purchase[2])
        needed_for_purchase_group['count'] = count

        group_needed_for_purchase['needed_for_purchase'].append(needed_for_purchase_group)

async def get_item_id(inter: Interaction, cog: MyCog, 
                      item: Item, name: str) -> int:
    items = item.get_id_by_name(name)
    if len(items) == 0:
        raise NoItemsThatName(name)
    elif len(items) == 1:
        return tuple(items.values())[0]
    else:
        id_ = await cog.question(
                inter, f'Выбери предмет, который ты имел ввиду({name})', items
        )
        return id_
