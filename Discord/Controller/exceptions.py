class NoItemsThatName(Exception):
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return 'Предмета с именем {} нет'.format(self.name)

class WrongFormParameter(Exception):
    def __init__(self, parameter: str):
        self.parameter = parameter
    
    def __str__(self) -> str:
        return 'Неправильно задана форма в параметре {}' \
                .format(self.parameter)