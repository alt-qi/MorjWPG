from typing import Any

from nextcord import Interaction, Embed, Member
from nextcord.ext.commands import Bot, Cog

from Discord.Cogs.View import Question, Pages, Confirm
from Discord.Cogs.exceptions import IsntCurator, IsntRuler, NoAnswer
from Discord.Cogs.Config import Config


class MyCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def curators_perf(inter: Interaction):
        return MyCog.check_curator(inter.user)
    
    @staticmethod
    def players_perf(inter: Interaction):
        return MyCog.check_player(inter.user)
    
    @staticmethod
    async def curators_players_perf(inter: Interaction):
        if any((Config().curator_role, Config().player_role)):
            return True
        else:
            await inter.send(':x: Вы не куратор или не правитель')


    async def send(self, inter: Interaction, title: str, message: str, user: Member=None):
        if not user:
            user = self.bot.user

        embed = Embed(title=title,
                      description=message,
                      color=0x8cd1ff)
        embed.set_author(name=user.name, 
                         icon_url=user.avatar)

        await inter.send(embed=embed)

    async def question(self, inter: Interaction, 
                       question: str, values: dict[str, Any]):
        embed = Embed(title='Question',
                      description=question,
                      color=0x8cd1ff)
        view = Question(inter.user, values)
        await inter.send(embed=embed, view=view)

        await view.wait()
        if view.answer_ == None: raise NoAnswer
        else: return view.answer

    async def page(self, inter: Interaction, title: str, user: Member,
                   list: list[str], page_number: int=1):
        embeds = []
        for i in list:
            embed = Embed(
                title=title,
                description=i,
                color=0x8cd1ff
            )
            embed.set_author(name=user.name, icon_url=user.avatar)
            embeds.append(embed)
            
        view = Pages(inter.user, embeds, inter, page_number)
        
        page_number -= 1
        await inter.response.send_message(embed=embeds[page_number], view=view)
        view.msg = await inter.original_message()
    
    async def confirm(self, inter: Interaction, user: Member, 
                      message: str) -> bool:
        view = Confirm(user)

        await inter.send(message, view=view)
        
        await view.wait()
        if view.switch_ == None: raise NoAnswer
        else: return view.switch_


    @staticmethod
    def check_curator(user: Member) -> bool:
        print(Config().curator_role)
        if user.get_role(Config().curator_role):
            return True
        else:
            raise IsntCurator

    @staticmethod
    def check_player(user: Member) -> bool:
        if user.get_role(Config().player_role):
            return True
        else:
            raise IsntRuler(user)

    @staticmethod
    def get_country_name(user: Member) -> str:
        for i in user.roles:
            if i.name.startswith(Config().country_prefix):
                return i.name.replace(Config().country_prefix, '')

    @staticmethod
    async def get_player(inter: Interaction, player: Member):
        try:
            check_player = MyCog.check_player(inter.user)
        except IsntRuler:
            pass

        if player == None and check_player:
            return inter.user
        elif player == None and not check_player:
            raise IsntRuler(inter.user)

        if MyCog.check_curator(inter.user) and MyCog.check_player(player):
           return player