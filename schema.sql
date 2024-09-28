CREATE TABLE
    allergen_types (
        id int PRIMARY KEY,
        localized_name varchar(50),
        name varchar(50)
    );

CREATE TABLE
    allergens (
        id int PRIMARY KEY,
        name varchar(50),
        localized_name varchar(50),
        type_id int,
        allergenicity int,
        CONSTRAINT fk_allergen_type FOREIGN KEY (type_id) REFERENCES allergen_types (id)
    );

CREATE TABLE
    locations (
        id int PRIMARY KEY,
        name varchar(50),
        longitude decimal(9, 6),
        latitude decimal(9, 6),
        description varchar(100)
    );

CREATE TABLE
    measurements (
        id int PRIMARY KEY,
        date date,
        concentration int,
        location_id int,
        allergen_id int,
        CONSTRAINT fk_location FOREIGN KEY (location_id) REFERENCES locations (id),
        CONSTRAINT fk_allergen FOREIGN KEY (allergen_id) REFERENCES allergens (id)
    );