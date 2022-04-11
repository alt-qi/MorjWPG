from nextcord import Member


class NoAnswer(Exception):
    pass


class IsntAdministrator(Exception):
    pass

class IsntCurator(Exception):
    pass

class IsntRuler(Exception):
    def __init__(self, user: Member):
        self.user = user

    def __str__(self) -> str:
        return f'{self.user.mention} не правитель'