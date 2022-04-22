--
-- Устанавливаем настройки postgresql
--

SET client_encoding = 'UTF8';
CREATE EXTENSION pg_trgm;

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
    build_needed_for_purchase_id int GENERATED ALWAYS AS IDENTITY,
    build_id int,
    needed_build_id int,
    proportionally_items boolean DEFAULT False,
    should_not_be boolean DEFAULT False,
    count float DEFAULT 1.0,

    CONSTRAINT PK_build_needed_for_purchase_id PRIMARY KEY(build_needed_for_purchase_id),
    CONSTRAINT FK_build_id FOREIGN KEY(build_id) REFERENCES builds(build_id) ON DELETE CASCADE,
    CONSTRAINT FK_build_needed_build_id FOREIGN KEY(needed_build_id) REFERENCES builds(build_id) ON DELETE CASCADE,
    CONSTRAINT needed_build_count_CHK CHECK(count > 0)
);

CREATE TYPE group_type AS ENUM ('All', 'Any');

CREATE TABLE builds_groups_needed_for_purchase(
    build_group_id int GENERATED ALWAYS AS IDENTITY,
    build_id int,
    type group_type DEFAULT 'All',
    should_not_be boolean DEFAULT False,

    CONSTRAINT PK_builds_any_groups_build_any_group_id PRIMARY KEY(build_group_id),
    CONSTRAINT FK_builds_groups_build_id FOREIGN KEY(build_id) 
    REFERENCES builds(build_id) ON DELETE CASCADE
);

CREATE TABLE builds_groups_groups(
    build_group_id int,
    included_build_group_id int,

    CONSTRAINT FK_builds_gg_build_group_id FOREIGN KEY(build_group_id)
    REFERENCES builds_groups_needed_for_purchase(build_group_id)
    ON DELETE CASCADE,
    CONSTRAINT FK_builds_gg_included_build_group_id 
    FOREIGN KEY(included_build_group_id)
    REFERENCES builds_groups_needed_for_purchase(build_group_id)
    ON DELETE CASCADE,
    CONSTRAINT PK_builds_gg 
    PRIMARY KEY(build_group_id, included_build_group_id)
);

CREATE TABLE builds_needed_for_purchase_groups(
    build_group_id int,
    build_needed_for_purchase_id int,

    CONSTRAINT FK_builds_nfpg_build_group_id 
    FOREIGN KEY(build_group_id) 
    REFERENCES builds_groups_needed_for_purchase(build_group_id)
    ON DELETE CASCADE,
    CONSTRAINT FK_builds_nfpg_build_needed_for_purchase_id 
    FOREIGN KEY(build_needed_for_purchase_id)
    REFERENCES builds_needed_for_purchase(build_needed_for_purchase_id)
    ON DELETE CASCADE,
    CONSTRAINT PK_builds_nfpg 
    PRIMARY KEY(build_group_id, build_needed_for_purchase_id)
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
    unit_needed_for_purchase_id int GENERATED ALWAYS AS IDENTITY,
    unit_id int,
    needed_build_id int,
    proportionally_items boolean DEFAULT False,
    should_not_be boolean DEFAULT False,
    count float DEFAULT 1.0,

    CONSTRAINT PK_unit_needed_for_purchase_id PRIMARY KEY(unit_needed_for_purchase_id),
    CONSTRAINT FK_unit_id FOREIGN KEY(unit_id) REFERENCES units(unit_id) ON DELETE CASCADE,
    CONSTRAINT FK_unit_needed_build_id FOREIGN KEY(needed_build_id) REFERENCES builds(build_id) ON DELETE CASCADE,
    CONSTRAINT needed_unit_count_CHK CHECK(count > 0)
);

CREATE TABLE units_groups_needed_for_purchase(
    unit_group_id int GENERATED ALWAYS AS IDENTITY,
    unit_id int,
    type group_type DEFAULT 'All',
    should_not_be boolean DEFAULT False,

    CONSTRAINT PK_units_any_groups_unit_any_group_id PRIMARY KEY(unit_group_id),
    CONSTRAINT FK_units_groups_unit_id FOREIGN KEY(unit_id) 
    REFERENCES units(unit_id) ON DELETE CASCADE
);

CREATE TABLE units_groups_groups(
    unit_group_id int,
    included_unit_group_id int,

    CONSTRAINT FK_units_gg_unit_group_id FOREIGN KEY(unit_group_id)
    REFERENCES units_groups_needed_for_purchase(unit_group_id)
    ON DELETE CASCADE,
    CONSTRAINT FK_units_gg_included_unit_group_id 
    FOREIGN KEY(included_unit_group_id)
    REFERENCES units_groups_needed_for_purchase(unit_group_id)
    ON DELETE CASCADE,
    CONSTRAINT PK_units_gg 
    PRIMARY KEY(unit_group_id, included_unit_group_id)
);

CREATE TABLE units_needed_for_purchase_groups(
    unit_group_id int,
    unit_needed_for_purchase_id int,

    CONSTRAINT FK_units_nfpg_unit_group_id 
    FOREIGN KEY(unit_group_id) 
    REFERENCES units_groups_needed_for_purchase(unit_group_id)
    ON DELETE CASCADE,
    CONSTRAINT FK_units_nfpg_unit_needed_for_purchase_id 
    FOREIGN KEY(unit_needed_for_purchase_id)
    REFERENCES units_needed_for_purchase(unit_needed_for_purchase_id)
    ON DELETE CASCADE,
    CONSTRAINT PK_units_nfpg 
    PRIMARY KEY(unit_group_id, unit_needed_for_purchase_id)
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

CREATE OR REPLACE FUNCTION get_build_group_needed_for_purchase(group_id int) RETURNS varchar AS $$
    DECLARE i varchar;
    DECLARE output varchar;
    BEGIN
        output = '';
        FOR i IN (
            SELECT CASE 
                        WHEN bnfp.should_not_be THEN 'Не должно быть ' 
                        ELSE '' 
                   END || b.name || ': ' ||
                   CASE 
                        WHEN proportionally_items THEN 'количество имеющихся предметов\*' 
                        ELSE '' 
                   END || count || ', '
            FROM builds_groups_needed_for_purchase bgnfp
            JOIN builds_needed_for_purchase_groups bnfpg USING(build_group_id)
            JOIN builds_needed_for_purchase bnfp ON bnfpg.build_needed_for_purchase_id = bnfp.build_needed_for_purchase_id
            JOIN builds b ON b.build_id = bnfp.needed_build_id
            WHERE build_group_id = group_id
        ) LOOP
            output = output || i;
        END LOOP;

        RETURN output;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_group_build_needed_for_purchase(group_id int) RETURNS varchar AS $$
    DECLARE needed_for_purchase varchar;
    DECLARE i int;
    DECLARE groups varchar;
    BEGIN
        needed_for_purchase = get_build_group_needed_for_purchase(group_id);
        groups = '';
        FOR i IN SELECT included_build_group_id FROM builds_groups_groups WHERE build_group_id = group_id LOOP
            groups = groups || get_group_build_needed_for_purchase(i);
        END LOOP;

        RETURN
            CASE (SELECT should_not_be FROM builds_groups_needed_for_purchase WHERE build_group_id = group_id)
                WHEN True THEN 'Нет '
                ELSE ''
            END ||
            CASE (SELECT type FROM builds_groups_needed_for_purchase WHERE build_group_id = group_id)
                WHEN 'All' THEN 'Все из этого: '
                WHEN 'Any' THEN 'Что либо из этого: '
            END || needed_for_purchase || groups;
    END;
$$ LANGUAGE plpgsql;    

CREATE OR REPLACE FUNCTION get_build_needed_for_purchase(getting_build_id int) RETURNS varchar AS $$
    WITH group_id AS (
        SELECT build_group_id
        FROM builds_groups_needed_for_purchase
        WHERE build_id = getting_build_id
        LIMIT 1
    )
    SELECT get_group_build_needed_for_purchase((SELECT build_group_id FROM group_id))
$$ LANGUAGE SQL;


CREATE OR REPLACE FUNCTION get_builds_shop() RETURNS TABLE(build_name varchar, price item_price, description text, income real, buyability boolean, saleability boolean, needed_for_purchase varchar) AS $$
    WITH default_buyability AS (
        SELECT column_default::boolean
        FROM information_schema.columns
        WHERE (table_schema, table_name, column_name) = ('public', 'builds', 'buyability')
    ),
    default_saleability AS (
        SELECT column_default::boolean
        FROM information_schema.columns
        WHERE (table_schema, table_name, column_name) = ('public', 'builds', 'saleability')
    ),
    needed_for_purchase AS (
        SELECT DISTINCT(build_id), build_group_id
        FROM builds_groups_needed_for_purchase
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
           get_build_needed_for_purchase(b.build_id) AS needed_for_purchase
    FROM builds b
    ORDER BY needed_for_purchase;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_unit_group_needed_for_purchase(group_id int) RETURNS varchar AS $$
    DECLARE i varchar;
    DECLARE output varchar;
    BEGIN
        output = '';
        FOR i IN (
            SELECT CASE 
                        WHEN unfp.should_not_be THEN 'Не должно быть ' 
                        ELSE '' 
                   END || b.name || ': ' ||
                   CASE 
                        WHEN proportionally_items THEN 'количество имеющихся предметов\*' 
                        ELSE '' 
                   END || count || ', '
            FROM units_groups_needed_for_purchase ugnfp
            JOIN units_needed_for_purchase_groups unfpg USING(unit_group_id)
            JOIN units_needed_for_purchase unfp ON unfpg.unit_needed_for_purchase_id = unfp.unit_needed_for_purchase_id
            JOIN builds b ON b.build_id = unfp.needed_build_id
            WHERE unit_group_id = group_id
        ) LOOP
            output = output || i;
        END LOOP;

        RETURN output;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_group_unit_needed_for_purchase(group_id int) RETURNS varchar AS $$
    DECLARE needed_for_purchase varchar;
    DECLARE i int;
    DECLARE groups varchar;
    BEGIN
        needed_for_purchase = get_unit_group_needed_for_purchase(group_id);
        groups = '';
        FOR i IN SELECT included_unit_group_id FROM units_groups_groups WHERE unit_group_id = group_id LOOP
            groups = groups || get_group_unit_needed_for_purchase(i);
        END LOOP;

        RETURN
            CASE (SELECT should_not_be FROM units_groups_needed_for_purchase WHERE unit_group_id = group_id)
                WHEN True THEN 'Нет '
                ELSE ''
            END ||
            CASE (SELECT type FROM units_groups_needed_for_purchase WHERE unit_group_id = group_id)
                WHEN 'All' THEN 'Все из этого: '
                WHEN 'Any' THEN 'Что либо из этого: '
            END || needed_for_purchase || groups;
    END;
$$ LANGUAGE plpgsql;    

CREATE OR REPLACE FUNCTION get_unit_needed_for_purchase(getting_unit_id int) RETURNS varchar AS $$
    WITH group_id AS (
        SELECT unit_group_id
        FROM units_groups_needed_for_purchase
        WHERE unit_id = getting_unit_id
        LIMIT 1
    )
    SELECT get_group_unit_needed_for_purchase((SELECT unit_group_id FROM group_id))
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_units_shop() RETURNS TABLE(unit_name varchar, price item_price, description text, features text, buyability boolean, saleability boolean, needed_for_purchase varchar) AS $$
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
           get_unit_needed_for_purchase(u.unit_id) AS needed_for_purchase
        FROM units u
    LEFT JOIN units_needed_for_purchase USING(unit_id)
    ORDER BY needed_for_purchase;
$$ LANGUAGE SQL;


CREATE OR REPLACE FUNCTION get_builds_inventory(getting_country_id int) RETURNS TABLE(name varchar, count int, description text, income real) AS $$
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


CREATE OR REPLACE FUNCTION get_needed_price_for_build(customer_country_id int, buying_build_id int, count int) RETURNS float AS $$ 
    SELECT (SELECT money 
            FROM countries 
            WHERE country_id = customer_country_id)-price*count AS needed_money
    FROM builds
    WHERE build_id = buying_build_id
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_needed_price_for_unit(customer_country_id int, buying_unit_id int, count int) RETURNS float AS $$
    SELECT (SELECT money 
            FROM countries
            WHERE country_id = customer_country_id)-price*count AS needed_money
    FROM units
    WHERE unit_id = buying_unit_id
$$ LANGUAGE SQL;


CREATE OR REPLACE FUNCTION get_needed_count_build(seller_country_id int, selling_build_id int, selling_count float) RETURNS int AS $$
    WITH inventory AS (
        SELECT country_id, count
        FROM builds_inventory
        WHERE country_id = seller_country_id AND build_id = selling_build_id
    )
    SELECT COALESCE(count, 0)-selling_count AS needed_count
    FROM countries
    LEFT JOIN inventory USING(country_id)
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_needed_count_unit(seller_country_id int, selling_unit_id int, selling_count float) RETURNS int AS $$
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

CREATE OR REPLACE FUNCTION get_build_id_by_name(build_name varchar) RETURNS TABLE(name varchar, id int) AS $$
    SELECT name, build_id
    FROM builds
    WHERE name % build_name
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_unit_id_by_name(unit_name varchar) RETURNS TABLE(name varchar, id int) AS $$
    SELECT name, unit_id
    FROM units
    WHERE name % unit_name
$$ LANGUAGE SQL;
