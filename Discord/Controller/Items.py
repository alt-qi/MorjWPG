import sys; sys.path.append('..'); sys.path.append('.')
from typing import Any

from nextcord import Interaction, Member

from Service.Items import Item, ItemFabric
from Service.Country import OneCountry
from Controller.exceptions import NoItemsThatName, WrongFormParameter
from Discord.Cogs.Cog import MyCog


async def create_item(inter: Interaction, cog: MyCog, 
                      item_type: str, parameters: dict[str, Any]):
    item = ItemFabric().get_item(item_type)
    item_parameters = await get_parameters(inter, cog, parameters)
        
    item.insert(item_parameters)
    await cog.send(inter, 'Create Item', 'Предмет создан')

async def update_item(inter: Interaction, cog: MyCog, item_type: str, 
                      name: str, parameters: dict[str, Any]):
    item = ItemFabric().get_item(item_type)
    item_id = await get_item_id(inter, cog, item, name)
    if parameters['needed_for_purchase'] == '-':
        parameters['needed_for_purchase'] = ' '

    item_parameters = await get_parameters(inter, cog, parameters)
    item.update(item_id, item_parameters)

    await cog.send(inter, 'Update Item', 'Предмет обновлен')

async def delete_item(inter: Interaction, cog: MyCog, 
                      item_type: str, name: str):
    item = ItemFabric().get_item(item_type)
    if name == 'all':
        item.delete()
    else:
        item_id = await get_item_id(inter, cog, item, name)
        item.delete(item_id)
    
    await cog.send(inter, 'Delete Item', 'Предмет удален')


async def buy_item(inter: Interaction, cog: MyCog, item_type: str, 
                   user: Member, name: str, count: int):
    item = ItemFabric().get_item(item_type)
    country = OneCountry(cog.get_country_name(user))

    item_id = await get_item_id(inter, cog, item, name)
    item.buy(country, item_id, count)

    await cog.send(inter, 'Buy Item', 'Предмет куплен')

async def sell_item(inter: Interaction, cog: MyCog, item_type: str,
                    seller: Member, customer: Member,
                    name: str, count: str, price: float):
    item = ItemFabric().get_item(item_type)
    seller_country = OneCountry(cog.get_country_name(seller))
    customer_country = OneCountry(cog.get_country_name(customer))

    switch = await cog.confirm(
        inter, customer, 
        f'{customer.mention}, вы согласны купить {count} {name} за {price}?'
    )

    if switch:
        item_id = await get_item_id(inter, cog, item, name)
        item.sell(seller_country, customer_country, 
                  item_id, count, price)
    
        await cog.send(inter, 'Sell Item', 'Предмет продан')
    else:
        return


_DEFAULT_VALUE = None
async def get_parameters(inter: Interaction, cog: MyCog,
                         parameters: dict[str, Any]) -> dict[str, Any]:
    item_parameters = {}

    for i in parameters:
        if parameters[i] == _DEFAULT_VALUE:
            continue

        if i == 'needed_for_purchase':
            needed_for_purchase = {}
            item = ItemFabric().get_item('build')

            for j in parameters[i].split(','):
                j = j.split(':')
                match j:
                    case str(name), str(count):
                        count = int(count)
                        name = await get_item_id(inter, cog, item, name)
                        needed_for_purchase[name] = count
                    case _:
                        raise WrongFormParameter('Необходимо для покупки')
            value = needed_for_purchase
        else:
            value = parameters[i]

        item_parameters[i] = value
    
    return item_parameters

async def get_item_id(inter: Interaction, cog: MyCog, 
                      item: Item, name: str) -> int:
    items = item.get_id(name)
    if len(items) == 0:
        raise NoItemsThatName(name)
    elif len(items) == 1:
        return tuple(items.values())[0]
    else:
        id_ = await cog.question(
                inter, 'Выбери предмет, который ты имел ввиду', items
                )
        return id_