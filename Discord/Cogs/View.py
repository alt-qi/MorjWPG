from typing import Any
from nextcord import Embed, Member, Interaction
from nextcord.ui import View, Button, button, Select, select
from nextcord import ButtonStyle


class Pages(View):
    def __init__(self, user: Member, list: list[Embed], 
                 page_number: int=1, timeout: float=120):
        super().__init__(timeout=timeout)

        self.user = user
        if not list:
            list.append(Embed(title='Пусто'))
        self.list = list
        self.page_number = page_number-1
    
        self.list[self.page_number].set_footer(text=f'Страница {self.page_number+1} из {len(self.list)}')

        if len(self.list) <= 1:
            self.children[0].disabled = True
            self.children[1].disabled = True
        elif self.page_number <= 0:
            self.children[0].disabled = True
            self.children[1].disabled = False
        elif self.page_number >= len(self.list)-1:
            self.children[0].disabled = False
            self.children[1].disabled = True
    
    async def interaction_check(self, interaction: Interaction):
        if self.user != interaction.user:
            return False
        
        return True
    
    async def on_timeout(self):
        embed = self.list[self.page_number]
        embed.set_footer(
                text=(f'Страница {self.page_number+1} из {len(self.list)}'
                       '(взаимодействие заморожено)')
        )

        await self.msg.edit(embed=embed, view=None)


    @button(label='Прошлая страница', style=ButtonStyle.primary)
    async def past_button(self, button: Button, interaction: Interaction):
        if not(self.page_number == 0):
            self.page_number-=1

            if self.page_number <= 0:
                self.children[0].disabled = True
                self.children[1].disabled = False
            else:
                self.children[0].disabled = False
                self.children[1].disabled = False
            
            embed = self.list[self.page_number]
            embed.set_footer(text=f'Страница {self.page_number+1} из {len(self.list)}')

            await interaction.edit(embed=embed, view=self)
    
    @button(label='Следующая страница', style=ButtonStyle.primary)
    async def next_button(self, button: Button, interaction: Interaction):
        if not(self.page_number >= len(self.list)):
            self.page_number+=1
        
            if self.page_number >= len(self.list)-1:
                self.children[0].disabled = False
                self.children[1].disabled = True
            else:
                self.children[0].disabled = False
                self.children[1].disabled = False
        
            embed = self.list[self.page_number]
            embed.set_footer(text=f'Страница {self.page_number+1} из {len(self.list)}')

            await interaction.edit(embed=embed, view=self)


class Confirm(View):
    def __init__(self, user: Member, timeout: float=120):
        super().__init__(timeout=timeout)
        self.user = user
        self.switch_ = False

    async def interaction_check(self, interaction: Interaction):
        if self.user != interaction.user:
            return False
        
        return True
    
    @button(label='Отказ', style=ButtonStyle.red)
    async def canel_button(self, button: Button, interaction: Interaction):
        self.switch_ = False
        self.stop()
    
    @button(label='Согласие', style=ButtonStyle.green)
    async def agree_button(self, button: Button, interaction: Interaction):
        self.switch_ = True
        self.stop()


class Question(View):
    def __init__(self, user: Member, values: dict[str, Any], timeout: float=120):
        super().__init__(timeout=timeout)
        self.user = user
        for i in values:
            self.children[0].add_option(label=i, value=values[i])
        
        self.answer_ = None
    
    async def interaction_check(self, interaction: Interaction):
        if self.user != interaction.user:
            return False
        
        return True
    
    @select()
    async def question_menu(self, select: Select, interaction: Interaction):
        self.answer_ = select.values[0]
        self.stop()
