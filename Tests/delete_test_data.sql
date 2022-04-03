DELETE FROM builds
WHERE name IN ('Завод бытовых товаров', 'Мельница', 'Хлебопекарня', 
               'Завод винтовок', 'Казармы');

DELETE FROM units
WHERE name IN ('Пехота', 'Ополчение');

DELETE FROM countries
WHERE name IN ('Германия', 'Россия');
