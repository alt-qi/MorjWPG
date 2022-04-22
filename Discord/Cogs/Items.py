from typing import Any

from nextcord import Member, Interaction, slash_command, SlashOption
from nextcord.embeds import Embed
from nextcord.ext import application_checks
from nextcord.ext.commands import Bot

from Discord.Cogs.View import Pages
from Discord.Controller.Items import create_item, sell_item, update_item, \
                                     delete_item, buy_item
from Discord.Cogs.Cog import MyCog
from Service.Items import ItemFabric


_ITEM_PARAMETER = SlashOption(
    name='тип-предмета',
    description='Определяет тип предмета',
    choices={'здание': 'build', 'юнит': 'unit'}
)
class Items(MyCog):
    items: dict[str, Any]
    buyable_items: dict[str, Any]
    saleable_items: dict[str, Any]
    deletable_items: dict[str, Any]

    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.items = {}
        self.buyable_items = {}
        self.saleable_items = {}
        self.deletable_items = {}

        self.get_all_items()
        
    def get_all_items(self):
        for item in ('builds', 'units'):
            self.get_items(item)
            self.get_buyable_items(item)
            self.get_saleable_items(item)
            self.get_deletable_items(item)

    def get_items(self, item_type: str):
        self.items[item_type] = ItemFabric().get_item(item_type).get_all_items()
    def get_buyable_items(self, item_type: str):
        self.buyable_items[item_type] = ItemFabric().get_item(item_type).get_buyable_items()
    def get_saleable_items(self, item_type: str):
        self.saleable_items[item_type] = ItemFabric().get_item(item_type).get_saleable_items()
    def get_deletable_items(self, item_type: str):
        self.deletable_items[item_type] = ItemFabric().get_item(item_type).get_all_items()
        self.deletable_items[item_type]['all'] = -1


    @slash_command(name='help', description='Помощь с ботом кураторам')
    async def help(self, inter: Interaction):
        self.page
        help_pages = [
            Embed(
                title='Необходимое для покупки', 
                description=(
                    '**Необходимое для покупки** - параметр необходимых для покупки зданий. '
                    'Он должен указываться по форме: `здание: количество`. '
                    'Также поддерживаются специальные параметры: \n'

                    '\n- **Не должно выполняться(знак !)** - если условие обозначенное таким ' 
                    'параметром будет выполняться, то это условие будет ложным \n'

                    '- **Пропорционально количеству предметов(знак \*)** - означает, ' 
                    'что количество необходимых для покупки зданий будет ' 
                    'пропорционально уже купленным предметам||, то есть если у вас уже есть 1 Пехота,  ' 
                    'для которой вам надо иметь 1 Казарму, то чтобы купить вторую надо иметь уже 2 Казармы||. ' 
                    'Ход с которым увеличивается количество необходимых предметов выражен количеством \n'

                    '\n**Параметры указываются перед формой**, вот так: '
                    '`параметр(тут нет пробела)здание: количество`, '
                    'можно также указать несколько параметров. \n')
            ),
            Embed(
                title='Группы необходимых для покупки',
                description=(
                    'Также поддерживаются **группы необходимых для покупки условий**, ' 
                    'они заключаются в (): `(здание: количество, здание: количество, ...)` '
                    'К группам также применимы следующие параметры: \n'

                    '\n- **Не должно выполняться(знак !)** - означает то же самое, '
                    'что и в случае с одиночными условиями, только относится к целой группе \n'

                    '- **Что-либо из этого(знак |)** - означает, что если соблюдается '
                    'хотя бы одно условие, то игрок может купить предмет \n'

                    '\n**Форма примерно такая же как и в случае с одиночными условиями**: '
                    '`параметр(условие, условие, ...)`. **Группы можно вкладывать друг в '
                    'друга**, а также **применять к основной группе**||(в которой вы начинаете писать)|| '
                    'параметры, необходимо ее просто заключить в скобки и написать перед ней параметры')
            )
        ]

        view = Pages(inter.user, help_pages, timeout=300)
        await inter.response.send_message(embed=help_pages[0], view=view)
        view.msg = await inter.original_message()


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
                         'подробности смотреть в /help'),
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
        await update_item(
                inter, self, 'build', self.items['builds'][name],
                {'name': new_name,
                 'price': new_price,
                 'description': new_description,
                 'income': new_income,
                 'buyability': new_buyability,
                 'saleability': new_saleability,
                 'needed_for_purchase': new_needed_for_purchase}
        )

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
        await update_item(
                inter, self, 'unit', self.items['units'][name],
                {'name': new_name,
                 'price': new_price,
                 'description': new_description,
                 'features': new_features,
                 'buyability': new_buyability,
                 'saleability': new_saleability,
                 'needed_for_purchase': new_needed_for_purchase}
        )

    @update_build.on_autocomplete('name')
    async def update_build_autocomplete(self, inter: Interaction, name: str):
        await inter.response.send_autocomplete(
                list(self.items['builds'].keys())
        )
    @update_unit.on_autocomplete('name')
    async def update_unit_autocomplete(self, inter: Interaction, name: str):
        await inter.response.send_autocomplete(
                list(self.items['units'].keys())
        )

    _DELETE_PARAMETERS = {
            'name': SlashOption(
                name='имя',
                description=('Имя удаляемого предмета, если указать all, ' 
                             'то удалятся все')
            )
    }
    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='del-build', description='Удалить здание')
    async def delete_build(self, inter: Interaction,
                           name: str = _DELETE_PARAMETERS['name']
    ):
        await delete_item(inter, self, 'build', self.deletable_items['builds'][name])

    @application_checks.check(MyCog.curators_perf)
    @slash_command(name='del-unit', description='Удалить юнита')
    async def delete_unit(self, inter: Interaction,
                          name: str = _DELETE_PARAMETERS['name']
    ):
        await delete_item(inter, self, 'unit', self.deletable_items['units'][name])

    @delete_build.on_autocomplete('name')
    async def delete_build_autocomplete(self, inter: Interaction, name: str):
        await inter.response.send_autocomplete(
                list(self.deletable_items['builds'].keys())
        )
    @delete_unit.on_autocomplete('name')
    async def delete_unit_autocomplete(self, inter: Interaction, name: str):
        await inter.response.send_autocomplete(
                list(self.deletable_items['units'].keys())
        )

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
    @slash_command(name='buy-build', description='Купить здание')
    async def buy_build(
            self, inter: Interaction,
            name: str = _BUY_PARAMETERS['name'],
            count: int = _BUY_PARAMETERS['count']
    ):
        await buy_item(
                inter, self, 'build', inter.user,
                self.buyable_items['builds'][name], count
        )

    @application_checks.check(MyCog.players_perf)
    @slash_command(name='buy-unit', description='Купить юнита')
    async def buy_unit(
            self, inter: Interaction,
            name: str = _BUY_PARAMETERS['name'],
            count: int = _BUY_PARAMETERS['count']
    ):
        await buy_item(
                inter, self, 'unit', inter.user,
                self.buyable_items['units'][name], count
        )

    @buy_build.on_autocomplete('name')
    async def buy_build_autocomplete(self, inter: Interaction, name: str):
        await inter.response.send_autocomplete(
            list(self.buyable_items['builds'].keys())
        )
    @buy_unit.on_autocomplete('name')
    async def buy_unit_autocomplete(self, inter: Interaction, name: str):
        await inter.response.send_autocomplete(
            list(self.buyable_items['units'].keys())
        )

    _SELL_PARAMETERS = {
        'name': SlashOption(
            name='имя',
            description='Имя продаваемого предмета'
        ),
        'count': SlashOption(
            name='количество',
            description='Количество продаваемых предметов'
        ),
        'price': SlashOption(
            name='цена',
            description='За сколько вы хотите продать предмет'
        ),
        'customer': SlashOption(
            name='покупатель',
            description='Тот, кому вы продаете предмет'
        )
    }
    @application_checks.check(MyCog.players_perf)
    @slash_command(name='sell-build', description='Продать здание')
    async def sell_build(
            self, inter: Interaction,
            name: str = _SELL_PARAMETERS['name'],
            count: int = _SELL_PARAMETERS['count'],
            price: float = _SELL_PARAMETERS['price'],
            customer: Member = _SELL_PARAMETERS['customer']
    ):
        if self.check_player(customer):
            await sell_item(
                    inter, self, 'build', 
                    inter.user, customer, 
                    name, self.saleable_items['builds'][name], 
                    count, price
            )

    @application_checks.check(MyCog.players_perf)
    @slash_command(name='sell-unit', description='Продать юнита')
    async def sell_unit(
            self, inter: Interaction,
            name: str = _SELL_PARAMETERS['name'],
            count: int = _SELL_PARAMETERS['count'],
            price: float = _SELL_PARAMETERS['price'],
            customer: Member = _SELL_PARAMETERS['customer']
    ):
        if self.check_player(customer):
            await sell_item(
                    inter, self, 'unit', 
                    inter.user, customer, 
                    name, self.saleable_items['units'][name], 
                    count, price
            )

    @sell_build.on_autocomplete('name')
    async def sell_build_autocomplete(self, inter: Interaction, name: str):
        await inter.response.send_autocomplete(
                list(self.saleable_items['builds'].keys())
        )
    @sell_unit.on_autocomplete('name')
    async def sell_unit_autocomplete(self, inter: Interaction, name: str):
        await inter.response.send_autocomplete(
                list(self.saleable_items['units'].keys())
        )



def setup(bot: Bot):
    bot.add_cog(Items(bot))
