--
-- Устанавливаем настройки postgresql
--

SET client_encoding = 'UTF8';
CREATE EXTENSION pg_trgm;

--
-- Удаляем таблицы
--

DROP TABLE IF EXISTS builds CASCADE;
DROP TABLE IF EXISTS builds_needed_for_purchase CASCADE;
DROP TABLE IF EXISTS units CASCADE;
DROP TABLE IF EXISTS units_needed_for_purchase CASCADE;
DROP TABLE IF EXISTS countries CASCADE;
DROP TABLE IF EXISTS inventory_builds CASCADE;
DROP TABLE IF EXISTS inventory_units CASCADE;
DROP TABLE IF EXISTS income_times CASCADE; 


--
-- Создаем таблицы
--

CREATE TABLE builds(
    build_id int GENERATED ALWAYS AS IDENTITY,
    name varchar(128) UNIQUE NOT NULL,
    price int NOT NULL,
    description text DEFAULT '',
    income int DEFAULT 0,

    CONSTRAINT PK_builds_build_id PRIMARY KEY(build_id),
    CONSTRAINT build_price_CHK CHECK(price>0)
);

CREATE TABLE builds_needed_for_purchase(
    build_id int,
    needed_build_id int,
    count int,

    CONSTRAINT FK_build_id FOREIGN KEY(build_id) REFERENCES builds(build_id) ON DELETE CASCADE,
    CONSTRAINT FK_needed_build_id FOREIGN KEY(needed_build_id) REFERENCES builds(build_id) ON DELETE CASCADE,
    CONSTRAINT build_needed_build_CHK CHECK(build_id <> needed_build_id),
    CONSTRAINT PK_build_needed_build PRIMARY KEY(build_id, needed_build_id),
    CONSTRAINT needed_build_count_CHK CHECK(count > 0)
);

CREATE TABLE units(
    unit_id int GENERATED ALWAYS AS IDENTITY,
    name varchar(128) UNIQUE NOT NULL,
    price int NOT NULL,
    description text DEFAULT '',
    features text NOT NULL,

    CONSTRAINT PK_units_unit_id PRIMARY KEY(unit_id),
    CONSTRAINT unit_price_CHK CHECK(price>0)
);

CREATE TABLE units_needed_for_purchase(
    unit_id int,
    needed_build_id int,
    count int,

    CONSTRAINT FK_unit_id FOREIGN KEY(unit_id) REFERENCES units(unit_id) ON DELETE CASCADE,
    CONSTRAINT FK_needed_build_id FOREIGN KEY(needed_build_id) REFERENCES builds(build_id) ON DELETE CASCADE,
    CONSTRAINT PK_unit_needed_build PRIMARY KEY(unit_id, needed_build_id),
    CONSTRAINT needed_build_count_CHK CHECK(count > 0)
);

CREATE TABLE countries(
    country_id int GENERATED ALWAYS AS IDENTITY,
    name varchar(128) UNIQUE NOT NULL,
    money int DEFAULT 0,

    CONSTRAINT PK_countries_country_id PRIMARY KEY(country_id)
);

CREATE TABLE builds_inventory(
    country_id int,
    build_id int,
    count int,

    CONSTRAINT FK_country_id FOREIGN KEY(country_id) REFERENCES countries(country_id) ON DELETE CASCADE,
    CONSTRAINT FK_build_id FOREIGN KEY(build_id) REFERENCES builds(build_id) ON DELETE CASCADE,
    CONSTRAINT PK_country_build PRIMARY KEY(country_id, build_id),
    CONSTRAINT build_count_CHK CHECK(count > 0)
);

CREATE TABLE units_inventory(
    country_id int,
    unit_id int,
    count int,

    CONSTRAINT FK_country_id FOREIGN KEY(country_id) REFERENCES countries(country_id) ON DELETE CASCADE,
    CONSTRAINT FK_unit_id FOREIGN KEY(unit_id) REFERENCES units(unit_id) ON DELETE CASCADE,
    CONSTRAINT PK_country_unit PRIMARY KEY(country_id, unit_id),
    CONSTRAINT unit_count_CHK CHECK(count > 0)
);

CREATE TABLE income_times(
    income_time time UNIQUE NOT NULL
);

-- 
-- Создаем функции
--

CREATE OR REPLACE FUNCTION get_builds_shop() RETURNS TABLE(build_name varchar, price int, description text, income int, needed_build_name varchar, count int) AS $$
    SELECT b.name AS build_name, b.price, b.description, b.income, n.name AS needed_build_name, count
    FROM builds b
    LEFT JOIN builds_needed_for_purchase USING(build_id)
    LEFT JOIN builds n ON builds_needed_for_purchase.needed_build_id = n.build_id; 
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_units_shop() RETURNS TABLE(unit_name varchar, price int, description text, features text, needed_build_name varchar, count int) AS $$
    SELECT u.name AS unit_name, u.price, u.description, u.features, n.name AS needed_build_name, count
    FROM units u
    LEFT JOIN units_needed_for_purchase USING(unit_id)
    LEFT JOIN builds n ON units_needed_for_purchase.needed_build_id = n.build_id;
$$ LANGUAGE SQL;


CREATE OR REPLACE FUNCTION get_builds_inventory(getting_country_id int) RETURNS TABLE(name varchar, count int, description text, income int) AS $$
    SELECT name, count, description, income*count AS income
    FROM builds
    JOIN builds_inventory USING(build_id)
    WHERE country_id = getting_country_id
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_units_inventory(getting_country_id int) RETURNS TABLE(name varchar, count int, description text, features text) AS $$
    SELECT name, count, description, features
    FROM units
    JOIN units_inventory USING(unit_id)
    WHERE country_id = getting_country_id
$$ LANGUAGE SQL;


CREATE OR REPLACE FUNCTION get_income_countries() RETURNS TABLE(country_id int, income int) AS $$
    SELECT country_id, COALESCE(SUM(income*count), 0)
    FROM builds
    JOIN builds_inventory USING(build_id)
    GROUP BY country_id
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_income_country(getting_country_id int) RETURNS int AS $$
    SELECT COALESCE(SUM(income*count), 0)
    FROM builds
    JOIN builds_inventory USING(build_id)
    WHERE country_id = getting_country_id
    GROUP BY country_id
$$ LANGUAGE SQL;


CREATE OR REPLACE FUNCTION get_builds_by_name(build_name varchar) RETURNS TABLE(build_id int, name varchar) AS $$
    SELECT build_id, name
    FROM builds
    WHERE name % build_name
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_units_by_name(unit_name varchar) RETURNS TABLE(unit_id int, name varchar) AS $$
    SELECT unit_id, name
    FROM units
    WHERE name % unit_name
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_needed_builds_for_build(customer_country_id int, buying_build_id int) RETURNS TABLE(needed_build_name varchar, count int) AS $$
    SELECT n.name, COALESCE(i.count, 0)-bn.count
    FROM builds b
    JOIN builds_needed_for_purchase bn USING(build_id)
    LEFT JOIN builds n ON bn.needed_build_id = n.build_id
    LEFT JOIN (SELECT build_id, count
               FROM builds_inventory
               WHERE country_id = customer_country_id) AS i ON n.build_id = i.build_id
    WHERE b.build_id = buying_build_id AND (COALESCE(i.count, 0)-bn.count) < 0;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_needed_builds_for_unit(customer_country_id int, buying_unit_id int) RETURNS TABLE(needed_build_name varchar, count int) AS $$
    SELECT n.name, COALESCE(i.count, 0)-un.count
    FROM units u
    JOIN units_needed_for_purchase un USING(unit_id)
    LEFT JOIN builds n ON un.needed_build_id = n.build_id
    LEFT JOIN (SELECT build_id, count
               FROM builds_inventory
               WHERE country_id = customer_country_id) AS i ON n.build_id = i.build_id
    WHERE u.unit_id = buying_unit_id AND (COALESCE(i.count, 0)-un.count) < 0;
$$ LANGUAGE SQL;


CREATE OR REPLACE FUNCTION get_needed_price_for_build(customer_country_id int, buying_build_id int, count int) RETURNS int AS $$ 
    SELECT (SELECT money 
            FROM countries 
            WHERE country_id = customer_country_id)-price*count AS needed_money
    FROM builds
    WHERE build_id = buying_build_id
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_needed_price_for_unit(customer_country_id int, buying_unit_id int, count int) RETURNS int AS $$
    SELECT (SELECT money 
            FROM countries
            WHERE country_id = customer_country_id)-price*count AS needed_money
    FROM units
    WHERE unit_id = buying_unit_id
$$ LANGUAGE SQL;

--
-- Заполняем данные в таблицы
--

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
('Россия', 1200);

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
