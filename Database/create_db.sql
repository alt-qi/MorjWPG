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
-- Создаем домены
--

CREATE DOMAIN item_price AS real DEFAULT 0.1 NOT NULL CHECK(VALUE>0);

--
-- Создаем таблицы
--

CREATE TABLE builds(
    build_id int GENERATED ALWAYS AS IDENTITY,
    name varchar(128) UNIQUE NOT NULL,
    price item_price,
    description text DEFAULT '',
    income real DEFAULT 0.0,
    buyability boolean DEFAULT True,
    saleability boolean DEFAULT False,

    CONSTRAINT PK_builds_build_id PRIMARY KEY(build_id)
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
    price item_price,
    description text DEFAULT '',
    features text DEFAULT '',
    buyability boolean DEFAULT True,
    saleability boolean DEFAULT True,

    CONSTRAINT PK_units_unit_id PRIMARY KEY(unit_id)
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
    money real DEFAULT 0,

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

CREATE TABLE config(
    curator_role varchar(32),
    player_role varchar(32),
    publisher_channel varchar(32),
    country_prefix varchar(32)
);

-- 
-- Создаем функции
--

CREATE OR REPLACE FUNCTION get_builds_shop() RETURNS TABLE(build_name varchar, price item_price, description text, income real, buyability boolean, saleability boolean, needed_build_name varchar, count int) AS $$
    WITH default_buyability AS (
        SELECT column_default::boolean
        FROM information_schema.columns
        WHERE (table_schema, table_name, column_name) = ('public', 'builds', 'buyability')
    ),
    default_saleability AS (
        SELECT column_default::boolean
        FROM information_schema.columns
        WHERE (table_schema, table_name, column_name) = ('public', 'builds', 'saleability')
    )
    SELECT b.name AS build_name, b.price, b.description, b.income, 
           CASE
               WHEN b.buyability = (SELECT * FROM default_buyability) THEN NULL
               ELSE b.buyability
           END AS buyability,
           CASE
               WHEN b.saleability = (SELECT * FROM default_saleability) THEN NULL
               ELSE b.saleability
           END AS saleability,
           n.name AS needed_build_name, count
    FROM builds b
    LEFT JOIN builds_needed_for_purchase USING(build_id)
    LEFT JOIN builds n ON builds_needed_for_purchase.needed_build_id = n.build_id
    ORDER BY needed_build_name NULLS FIRST;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_units_shop() RETURNS TABLE(unit_name varchar, price item_price, description text, features text, buyability boolean, saleability boolean, needed_build_name varchar, count int) AS $$
    WITH default_buyability AS (
        SELECT column_default::boolean
        FROM information_schema.columns
        WHERE (table_schema, table_name, column_name) = ('public', 'units', 'buyability')
    ),
    default_saleability AS (
        SELECT column_default::boolean
        FROM information_schema.columns
        WHERE (table_schema, table_name, column_name) = ('public', 'units', 'saleability')
    )
    SELECT u.name AS unit_name, u.price, u.description, u.features, 
           CASE
               WHEN u.buyability = (SELECT * FROM default_buyability) THEN NULL
               ELSE u.buyability
           END AS buyability,
           CASE
               WHEN u.saleability = (SELECT * FROM default_saleability) THEN NULL
               ELSE u.saleability
           END AS saleability,
           n.name AS needed_build_name, count
    FROM units u
    LEFT JOIN units_needed_for_purchase USING(unit_id)
    LEFT JOIN builds n ON units_needed_for_purchase.needed_build_id = n.build_id
    ORDER BY needed_build_name NULLS FIRST;
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


CREATE OR REPLACE FUNCTION get_income_country(getting_country_id int) RETURNS real AS $$
    SELECT COALESCE(SUM(income*count), 0)
    FROM builds
    JOIN builds_inventory USING(build_id)
    WHERE country_id = getting_country_id
    GROUP BY country_id
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION give_out_income() RETURNS void AS $$
    UPDATE countries
    SET money = money + COALESCE(get_income_country(country_id), 0)
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
    WITH inventory AS (
        SELECT build_id, count
        FROM builds_inventory 
        WHERE country_id = customer_country_id
)
    SELECT n.name, ABS(COALESCE(i.count, 0)-bn.count)
    FROM builds b
    JOIN builds_needed_for_purchase bn USING(build_id)
    LEFT JOIN builds n ON bn.needed_build_id = n.build_id
    LEFT JOIN inventory AS i ON n.build_id = i.build_id
    WHERE b.build_id = buying_build_id AND (COALESCE(i.count, 0)-bn.count) < 0;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_needed_builds_for_unit(customer_country_id int, buying_unit_id int) RETURNS TABLE(needed_build_name varchar, count int) AS $$
    WITH inventory AS (
        SELECT build_id, count
        FROM builds_inventory
        WHERE country_id = customer_country_id
)
    SELECT n.name, ABS(COALESCE(i.count, 0)-un.count)
    FROM units u
    JOIN units_needed_for_purchase un USING(unit_id)
    LEFT JOIN builds n ON un.needed_build_id = n.build_id
    LEFT JOIN inventory i ON n.build_id = i.build_id
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


CREATE OR REPLACE FUNCTION get_needed_count_build(seller_country_id int, selling_build_id int, selling_count int) RETURNS int AS $$
    WITH inventory AS (
        SELECT country_id, count
        FROM builds_inventory
        WHERE country_id = seller_country_id AND build_id = selling_build_id
    )
    SELECT COALESCE(count, 0)-selling_count AS needed_count
    FROM countries
    LEFT JOIN inventory USING(country_id)
    WHERE country_id = seller_country_id
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_needed_count_unit(seller_country_id int, selling_unit_id int, selling_count int) RETURNS int AS $$
    WITH inventory AS (
        SELECT country_id, count
        FROM units_inventory
        WHERE country_id = seller_country_id AND unit_id = selling_unit_id
    )
    SELECT COALESCE(count, 0)-selling_count AS needed_count
    FROM countries
    LEFT JOIN inventory USING(country_id)
    WHERE country_id = seller_country_id
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_needed_money(customer_country_id int, price real) RETURNS real AS $$
    SELECT money-price AS needed_money
    FROM countries
    WHERE country_id = customer_country_id
$$ LANGUAGE SQL;


CREATE OR REPLACE FUNCTION get_next_income_time(now time) RETURNS time AS $$
WITH next_today_income_time AS (
    SELECT income_time
    FROM income_times
    WHERE income_time >= now
    ORDER BY income_time 
    LIMIT 1
), next_tomorrow_income_time AS (
    SELECT income_time
    FROM income_times
    ORDER BY income_time
    LIMIT 1
)
SELECT income_time
FROM income_times
WHERE income_time = COALESCE((SELECT income_time FROM next_today_income_time),
                             (SELECT income_time FROM next_tomorrow_income_time))
$$ LANGUAGE SQL;
