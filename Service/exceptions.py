from typing import Any


class NoImportantParameter(Exception):
    pass

class OperationOnlyForOneCountry(Exception):
    pass

class NoItem(Exception):
    pass

class CantTransact(Exception):
    def __init__(self, reasons: dict[str, Any]):
        self.reasons = reasons

    def __str__(self) -> str:
        output = []
        for reason in self.reasons:
            if reason == 'builds':
                builds = []
                for i in self.reasons['builds']:
                    builds.append('{}: {}'.format(i, abs(self.reasons['builds'][reason])))

                output.append('Необходимые Здания: ' + ', '.join(builds))
            elif reason == 'item':
                output.append('Нехватка предмета: {}'.format(abs(self.reasons['item'])))
            elif reason == 'money':
                output.append('Нехватка денег: {}'.format(abs(self.reasons['money'])))
            elif reason == 'buyability':
                output.append('Нельзя купить предмет, его может выдать только куратор')
            elif reason == 'saleability':
                output.append('Нельзя продавать предмет')

        return 'Нельзя совершить транзакцию '+', '.join(output)
