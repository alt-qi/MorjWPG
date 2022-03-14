CREATE TABLE Build(
    id serial primary key,
    name varchar(255),
    price integer,
    description text,
    income integer,
    saleability boolean
);

CREATE TABLE BuildNeededForPurchase(
    build_id integer references Build(id) on delete cascade,
    needed_build_id integer references Build(id) on delete cascade,
    count integer,
    delete_after_buy boolean
);


CREATE TABLE Unit(
    id serial primary key,
    name varchar(255),
    price integer,
    description text,
    features text,
    saleability boolean
);

CREATE TABLE UnitNeededForPurchase(
    unit_id integer references Unit(id) on delete cascade,
    needed_build_id integer references Build(id) on delete cascade,
    count integer,
    delete_after_buy boolean
);


CREATE TABLE Country(
    id serial primary key,
    name varchar(255),
    money integer,
    income integer
);

CREATE TABLE Balance(
    country_id integer references Country(id) on delete cascade,
    balance integer
);


CREATE TABLE InventoryBuild(
    country_id integer references Country(id) on delete cascade,
    build_id integer references Build(id) on delete cascade,
    count integer
);

CREATE TABLE InventoryUnit(
    country_id integer references Country(id) on delete cascade,
    unit_id integer references Unit(id) on delete cascade,
    count integer
);


CREATE TABLE IncomeTimes(
    times time[]
);