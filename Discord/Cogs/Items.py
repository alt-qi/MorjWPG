from nextcord import Member, Interaction, slash_command, SlashOption
from nextcord.ext import application_checks
from nextcord.ext.commands import Bot

from Discord.Controller.Items import create_item, sell_item, update_item, \
                                     delete_item, buy_item
from Discord.Cogs.Cog import MyCog


_ITEM_PARAMETER = SlashOption(
    name='тип-предмета',
    description='Определяет тип предмета',
    choices={'здание': 'build', 'юнит': 'unit'}
)

class Items(MyCog):

    _ADD_PARAMETERS = {
        'name': SlashOption(
            name='имя',
            description='Присваивает имя предмету'
        ),
        'price': SlashOption(
            name='цена',
            description='Цена за которую будет продаваться предмет'
        ),
        'description': SlashOption(
            name='описание',
            description='Описание, которое будет пояснять игроку о предмете',
            required=False,
            default=None
        ),
        'buyability': SlashOption(
            name='возможность-покупки',
            description='Определяет, могут ли игроки покупать предмет',
            required=False,
            default=None
        ),
        'saleability': SlashOption(
            name='возможность-продажи',
            description=('Определяет, могут ли игроки продавать, '
                         'между собой предмет'),
            required=False,
            default=None
        ),
        'needed_for_purchase': SlashOption(
            name='необходимо-для-покупки',
            description=('Необходимые для покупки предмета здания, '
                         'необходимо указать по форме '
                         '`здание: количество`'),
            required=False,
            default=None
        )
    }
    
    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='add-build', description='Добавить новое здание', 
                   default_permission=False)
    async def add_build(
            self, inter: Interaction,
            name: str = _ADD_PARAMETERS['name'],
            price: float = _ADD_PARAMETERS['price'],
            description: str = _ADD_PARAMETERS['description'],
            income: float = SlashOption(
                name='доход',
                description=('Доход, который будет выдаваться ' 
                             'за каждое здание в ход'),
                required=False,
                default=None
            ),
            buyability: bool = _ADD_PARAMETERS['buyability'],
            saleability: bool = _ADD_PARAMETERS['saleability'],
            needed_for_purchase: str = _ADD_PARAMETERS['needed_for_purchase']
    ):
        await create_item(
            inter, self, 'build',
            {'name': name,
             'price': price,
             'description': description,
             'income': income,
             'buyability': buyability,
             'saleability': saleability,
             'needed_for_purchase': needed_for_purchase})

    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='add-unit', description='Добавить нового юнита', 
                   default_permission=False)
    async def add_unit(
            self, inter: Interaction,
            name: str = _ADD_PARAMETERS['name'],
            price: float = _ADD_PARAMETERS['price'],
            description: str = _ADD_PARAMETERS['description'],
            features: str = SlashOption(
                name='характеристики',
                description=('Нужны для удобства, должны показывать '
                             'характеристики юнита, определенной '
                             'формы нет'),
                required=False,
                default=None
            ),
            buyability: bool = _ADD_PARAMETERS['buyability'],
            saleability: bool = _ADD_PARAMETERS['saleability'],
            needed_for_purchase: str = _ADD_PARAMETERS['needed_for_purchase']
    ):
        await create_item(
            inter, self, 'unit',
            {'name': name,
             'price': price,
             'description': description,
             'features': features,
             'buyability': buyability,
             'saleability': saleability,
             'needed_for_purchase': needed_for_purchase})


    _UPDATE_PARAMETERS = {
        'name': SlashOption(
            name='имя',
            description='Имя изменяемого предмета'
        ),
        'new_name': SlashOption(
            name='новое-имя',
            description='Новое имя для предмета',
            required=False,
            default=None
        ),
        'new_price': SlashOption(
            name='новая-цена',
            description='Новая цена предмета',
            required=False,
            default=None
        ),
        'new_description': SlashOption(
            name='новое-описание',
            description='Новое описание предмета',
            required=False,
            default=None
        ),
        'new_buyability': SlashOption(
            name='новая-возможность-покупки',
            description='Присваивает новое значение возможности покупки',
            required=False,
            default=None
        ),
        'new_saleability': SlashOption(
            name='новая-возможность-продажи',
            description='Присваивает новое значение возможности продажи',
            required=False,
            default=None
        ),
        'new_needed_for_purchase': SlashOption(
            name='новые-необходимые-для-покупки',
            description=('Новое значение необходимых для покупки зданий предметов, '
                         'если хотите удалить их, напишите -'),
            required=False,
            default=None
        )
    }

    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='update-build', description='Изменить параметры здания', 
                   default_permission=False)
    async def update_build(
            self, inter: Interaction,
            name: str = _UPDATE_PARAMETERS['name'],
            new_name: str = _UPDATE_PARAMETERS['new_name'],
            new_price: float = _UPDATE_PARAMETERS['new_price'],
            new_description: str = _UPDATE_PARAMETERS['new_description'],
            new_income: str = SlashOption(
                name='новый-доход',
                description='Новый доход здания',
                required=False,
                default=None
            ),
            new_buyability: bool = _UPDATE_PARAMETERS['new_buyability'],
            new_saleability: bool = _UPDATE_PARAMETERS['new_saleability'],
            new_needed_for_purchase: str = _UPDATE_PARAMETERS['new_needed_for_purchase']
    ):
        await update_item(inter, self, 'build', name,
                          {'name': new_name,
                           'price': new_price,
                           'description': new_description,
                           'income': new_income,
                           'buyability': new_buyability,
                           'saleability': new_saleability,
                           'needed_for_purchase': new_needed_for_purchase})

    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='update-unit', description='Изменить параметры юнита', 
                   default_permission=False)
    async def update_unit(
            self, inter: Interaction,
            name: str = _UPDATE_PARAMETERS['name'],
            new_name: str = _UPDATE_PARAMETERS['new_name'],
            new_price: float = _UPDATE_PARAMETERS['new_price'],
            new_description: str = _UPDATE_PARAMETERS['new_description'],
            new_features: str = SlashOption(
                name='новые-характеристики',
                description='Новые характеристики юнита',
                required=False,
                default=None
            ),
            new_buyability: bool = _UPDATE_PARAMETERS['new_buyability'],
            new_saleability: bool = _UPDATE_PARAMETERS['new_saleability'],
            new_needed_for_purchase: str = _UPDATE_PARAMETERS['new_needed_for_purchase']
    ):
        await update_item(inter, self, 'unit', name,
                          {'name': new_name,
                           'price': new_price,
                           'description': new_description,
                           'features': new_features,
                           'buyability': new_buyability,
                           'saleability': new_saleability,
                           'needed_for_purchase': new_needed_for_purchase})


    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='del-item', description='Удалить предмет', 
                   default_permission=False)
    async def delete_item(self, inter: Interaction,
                          item_type: str = _ITEM_PARAMETER,
                          name: str = SlashOption(
                              name='имя',
                              description=('Имя удаляемого предмета, если указать all, ' 
                                           'то удалятся все предметы')
                          )
    ):
        await delete_item(inter, self, item_type, name)
    

    _BUY_PARAMETERS = {
        'name': SlashOption(
            name='имя',
            description='Имя покупаемого предмета'
        ),
        'count': SlashOption(
            name='количество',
            description='Количество покупаемого предмета',
            required=False,
            default=1
        )
    }

    @application_checks.check(MyCog.players_perf)
    @slash_command(name='buy', description='Купить предмет')
    async def buy(self, inter: Interaction,
                  item_type: str = _ITEM_PARAMETER,
                  name: str = SlashOption(
                      name='имя',
                      description='Имя покупаемого предмета'
                  ),
                  count: int = SlashOption(
                      name='количество',
                      description='Количество покупаемого предмета',
                      required=False,
                      default=1
                  )
    ):
        await buy_item(inter, self, item_type, 
                       inter.user, name, count)


    @application_checks.check(MyCog.players_perf)
    @slash_command(name='sell', description='Продать предмет')
    async def sell(self, inter: Interaction,
                   item_type: str = _ITEM_PARAMETER,
                   name: str = SlashOption(
                       name='имя',
                       description='Имя продаваемого предмета'
                   ),
                   count: int = SlashOption(
                        name='количество',
                        description='Количество продаваемых предметов'
                   ),
                   price: float = SlashOption(
                        name='цена',
                        description='За сколько вы хотите продать предмет'
                   ),
                   customer: Member = SlashOption(
                        name='покупатель',
                        description='Тот, кому вы продаете предмет'
                   )
    ):
        if self.check_player(customer):
            await sell_item(inter, self, item_type, 
                            inter.user, customer, 
                            name, count, price)

def setup(bot: Bot):
    bot.add_cog(Items(bot))
