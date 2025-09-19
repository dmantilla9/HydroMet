-- cities
INSERT INTO cities (
    postal_code, 
    commune_code, 
    city_name, 
    country, 
    lat, 
    lon, 
    water_code, 
    timezone, 
    active, 
    inserted_at
)
VALUES 
(
    '95240',
    '95176',
    'Cormeilles-en-Parisis',
    'FR',
    48.973526,
    2.201292,
    '095000386_095',
    'Europe/Paris',
    TRUE,
    '2025-09-18 12:30:55.460494+00'
),
(
    '95220',
    '95306',
    'Herblay-sur-Seine',
    'FR',
    48.990006,
    2.165493,
    '095000386_095',
    'Europe/Paris',
    TRUE,
    '2025-09-18 12:30:55.460494+00'
),
(
    '92130',
    '92040',
    'Issy-les-Moulineaux',
    'FR',
    48.827007,
    2.261073,
    '095000386_095',
    'Europe/Paris',
    TRUE,
    '2025-09-18 15:25:55.460494+00'
);
 -- Water Networks
INSERT INTO water_network (
    water_code,
    water_network_name
)
VALUES 
(
    '075000221_075',
    'PARIS CENTRE'
),
(
    '092000054_092',
    'SEDIF SUD'
),
(
    '095000386_095',
    'SEDIF 95 EAU DE MERY/OISE'
);

