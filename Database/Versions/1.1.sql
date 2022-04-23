ALTER TABLE builds
ADD COLUMN group_item varchar(128);

ALTER TABLE units
ADD COLUMN group_item varchar(128);

DROP FUNCTION get_builds_shop;
DROP FUNCTION get_units_shop;
DROP FUNCTION get_builds_inventory;
DROP FUNCTION get_units_inventory;

CREATE OR REPLACE FUNCTION get_builds_shop() RETURNS TABLE(build_name varchar, group_item varchar, price item_price, description text, income real, buyability boolean, saleability boolean, needed_for_purchase varchar) AS $$
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
    SELECT b.name AS build_name, b.group_item, b.price, b.description, b.income, 
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
    ORDER BY group_item NULLS FIRST;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_units_shop() RETURNS TABLE(unit_name varchar, group_item varchar, price item_price, description text, features text, buyability boolean, saleability boolean, needed_for_purchase varchar) AS $$
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
    SELECT u.name AS unit_name, u.group_item, u.price, u.description, u.features, 
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
    ORDER BY group_item NULLS FIRST;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_builds_inventory(getting_country_id int) RETURNS TABLE(name varchar, group_item varchar, count int, description text, income real) AS $$
    SELECT name, group_item, count, description, income*count AS income
    FROM builds
    JOIN builds_inventory USING(build_id)
    WHERE country_id = getting_country_id
    ORDER BY group_item NULLS FIRST
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_units_inventory(getting_country_id int) RETURNS TABLE(name varchar, group_item varchar, count int, description text, features text) AS $$
    SELECT name, group_item, count, description, features
    FROM units
    JOIN units_inventory USING(unit_id)
    WHERE country_id = getting_country_id
    ORDER BY group_item NULLS FIRST
$$ LANGUAGE SQL;
