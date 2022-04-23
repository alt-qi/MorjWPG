import sys; sys.path.append('.')
from typing import Any
from abc import ABC, abstractmethod, abstractproperty

from nextcord import Interaction, Embed, Member, slash_command, \
                     SlashOption, Role
from nextcord.abc import GuildChannel
from nextcord.ext import application_checks
from nextcord.ext.commands import Bot, Cog

from Discord.Cogs.exceptions import IsntAdministrator
from Service.Items import ItemFabric
from Database.Database import database


class AbstractConfig(ABC):
    @abstractproperty
    def curator_role(self) -> int:
        pass
    @abstractproperty
    def player_role(self) -> int:
        pass
    @abstractproperty
    def publisher_channel(self) -> int:
        pass
    @abstractproperty
    def country_prefix(self) -> str:
        pass

    @abstractmethod
    def set_curator_role_id(self, id: int):
        pass
    @abstractmethod
    def set_player_role_id(self, id: int):
        pass
    @abstractmethod
    def set_publisher_channel_id(self, id: int):
        pass
    @abstractmethod
    def set_country_prefix(self, prefix: str):
        pass

class ConcreteConfig:
    _curator_role_id: int
    _player_role_id: int
    _publisher_channel_id: int
    _country_prefix: str

    def __init__(self):
        self._curator_role_id = self._get_id('curator_role')
        self._player_role_id = self._get_id('player_role')
        self._publisher_channel_id = self._get_id('publisher_channel')
        self._country_prefix = self._get_info('country_prefix')
    
    def _get_info(self, column: str) -> Any|None:
        if data := database().select_one(
            f'SELECT {column} '
             'FROM config'
        ):
             return data[column]

    def _get_id(self, column: str) -> int|None:
        if id := self._get_info(column):
            return int(id)

    @property
    def curator_role(self) -> int:
        return self._get_id('curator_role')
    @property
    def player_role(self) -> int:
        return self._get_id('player_role')   
    @property
    def publisher_channel(self) -> int:
        return self._get_id('publisher_channel')
    @property
    def country_prefix(self) -> str:
        return self._get_info('country_prefix')

    def set_curator_role_id(self, id: int):
        self._curator_role_id = id
        self._change_id(id, 'curator_role')
    def set_player_role_id(self, id: int):
        self._curator_role_id = id
        self._change_id(id, 'player_role')
    def set_publisher_channel_id(self, id: int):
        self._curator_role_id = id
        self._change_id(id, 'publisher_channel')
    def set_country_prefix(self, prefix: str):
        self._curator_role_id = prefix
        self._change_config(prefix, 'country_prefix')
        
    def _change_config(self, value, column: str):
        database().insert(
            'UPDATE config '
           f'SET {column} = %s',
            value
        )    

    def _change_id(self, value: int, column: str):
        self._change_config(str(value), column)

conf = ConcreteConfig()

def Config() -> AbstractConfig:
    return conf

class CogConfig(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
    
    @staticmethod
    def administration_perf(inter: Interaction):
        return CogConfig.check_administrator(inter.user)
    
    @staticmethod
    def check_administrator(user: Member) -> bool:
        if user.guild_permissions.administrator:
            return True
        else:
            raise IsntAdministrator

    async def send(self, inter: Interaction, title: str, message: str):
        embed = Embed(title=title,
                      description=message,
                      color=0x8cd1ff)

        await inter.send(embed=embed)

    @application_checks.check(administration_perf)
    @slash_command(name='set-curator-role', description='Присвоить роль куратора')
    async def set_curator_role(self, inter: Interaction,
                               role: Role = SlashOption(
                                   name='роль',
                                   description='Роль куратора'
                               )
    ):
        Config().set_curator_role_id(role.id)
        
        await self.send(inter, 'Set Curator Role', 'Роль куратора присвоена')
    
    @application_checks.check(administration_perf)
    @slash_command(name='set-player-role', description='Присвоить роль игрока')
    async def set_player_role(self, inter: Interaction,
                              role: Role = SlashOption(
                                  name='роль',
                                  description='Роль игрока'
                              )
    ):
        Config().set_player_role_id(role.id)

        await self.send(inter, 'Set Player Role', 'Роль игрока присвоена')

    @application_checks.check(administration_perf)
    @slash_command(name='set-publish-channel', description='Присвоить канал публикаций о выдаче дохода')
    async def set_publish_channel(self, inter: Interaction,
                                    channel: GuildChannel = SlashOption(
                                        name='канал',
                                        description='Текстовый канал в который бот будет публиковать сообщения о доходе',
                                    )
    ):
        
        Config().set_publisher_channel_id(channel.id)
        
        await self.send(inter, 'Set Publisher Channel', 'Канал для публикации присвоен')
    
    @application_checks.check(administration_perf)
    @slash_command(name='set-country-prefix', description='Присвоить префикс роли страны')
    async def set_publisher_channel(self, inter: Interaction,
                                    prefix: str = SlashOption(
                                        name='префикс',
                                        description='Префикс с которого начинаются имена роли стран'
                                    )
    ):
        Config().set_country_prefix(prefix)

        await self.send(inter, 'Set Country Prefix', 'Префикс для стран присвоен')

class AbstractListItems(ABC):
    items: dict[str, Any]
    buyable_items: dict[str, Any]
    saleable_items: dict[str, Any]
    deletable_items: dict[str, Any]

    @abstractmethod
    def get_all_types_items(self):
        pass

    @abstractmethod
    def get_same_items(self, items: dict[str, int], name: str) -> list[str]:
        pass

class ListItems(AbstractListItems):
    items: dict[str, Any]
    buyable_items: dict[str, Any]
    saleable_items: dict[str, Any]
    deletable_items: dict[str, Any]

    def __init__(self):
        self.items = {}
        self.buyable_items = {}
        self.saleable_items = {}
        self.deletable_items = {}

        self.get_all_types_items()

    def get_all_types_items(self):
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

    def get_same_items(self, items: dict[str, int], name: str) -> list[str]:
        output = []
        name = name.lower()
        for item in items.keys():
            if item.lower().startswith(name):
                output.append(item)

        return output

v_list_items = ListItems()
def list_items() -> AbstractListItems:
    return v_list_items


def setup(bot: Bot):
    bot.add_cog(CogConfig(bot))
