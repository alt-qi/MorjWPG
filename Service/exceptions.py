from typing import Any


class NoImportantParameter(Exception):
    pass

class OperationOnlyForOneCountry(Exception):
    pass

class NoItem(Exception):
    pass

class CantTransact(Exception):
    def __init__(self, reason: dict[str, Any]):
        self.reason = reason

    def __str__(self) -> str:
        output = []
        for i in self.reason:
            if i == 'builds':
                builds = []
                for j in self.reason['builds']:
                    builds.append('{}: {}'.format(j, abs(self.reason['builds'][j])))

                output.append('Необходимые Здания: ' + ', '.join(builds))
            elif i == 'item':
                output.append('Нехватка предмета: {}'.format(abs(self.reason['item'])))
            elif i == 'money':
                output.append('Нехватка денег: {}'.format(abs(self.reason['money'])))

        return 'Нельзя совершить транзакцию '+', '.join(output)
