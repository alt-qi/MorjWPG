from nextcord import Interaction, Member

from Discord.Controller.Lists import get_country_parameters
from Discord.Cogs.Cog import MyCog


async def delete_country(inter: Interaction, cog: MyCog, 
                         user: Member, for_all_countries: bool):
    if country := await get_country_parameters(inter, cog, user, for_all_countries):
        country.delete()
        await cog.send(inter, 'Delete Country', 'Я удалил страну')