INSERT INTO builds(name, price, description, income)
VALUES
('Завод бытовых товаров', 100, 'Продает бытовые товары и продает их', 20),
('Мельница', 80, 'Молет муку и продает ее', 15),
('Хлебопекарня', 100, 'Готовит из муки хлеб и продает его', 50),
('Завод винтовок', 200, 'Создает винтовки', 0),
('Казармы', 150, 'Здесь учат солдат', 0);

INSERT INTO builds_needed_for_purchase(build_id, needed_build_id, count)
VALUES
(3, 2, 1),
(5, 4, 2);

INSERT INTO units(name, price, description, features)
VALUES
('Пехота', 3, 'Обычная пехота', 'Атака: 1, Защита: 1, Скорость: 1'),
('Ополчение', 1, 'Набранное ополчение', 'Атака: 0.5, Защита: 0.5, Скорость: 0.2');

INSERT INTO units_needed_for_purchase(unit_id, needed_build_id, count)
VALUES
(1, 5, 1);

INSERT INTO countries(name, money)
VALUES
('Германия', 600),
('Россия', 1200),
('Казахстан', 0);

INSERT INTO builds_inventory(country_id, build_id, count)
VALUES
(1, 1, 3),
(1, 4, 2),
(1, 5, 2);

INSERT INTO units_inventory(country_id, unit_id, count)
VALUES
(1, 1, 1000),
(1, 2, 3000),
(2, 1, 5000),
(2, 2, 10000);
