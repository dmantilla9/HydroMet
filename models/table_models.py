from sqlalchemy import Column, String, Text, Numeric, Float, DateTime, Boolean
from sqlalchemy.sql import func
from connection_supabase import Base


class water_network(Base):
    __tablename__ = "dim_water_network"
    __table_args__ = {"schema": "public"}

    code_commune = Column(String, primary_key = True)
    nom_commune = Column(String(120), Nullable = False)
    code_reseau = Column(String(15), Nullable = False)
    nom_reseau = Column(String(100), Nullable = False)
    date_creation = Column(DateTime(timezone = True), server_default=func.now())

class communes(Base):
    __tablename__ = "dim_geo_communes"
    __table_args__ = {"schema": "public"}

    code_insee = Column(String(5), primary_key = True)
    nom_standard = Column(String(200), Nullable = True)
    nom_sans_pronom = Column(String(200), Nullable = True)
    nom_a = Column(String(200), Nullable = True)
    nom_de = Column(String(200), Nullable = True)
    nom_sans_accent = Column(String(200), Nullable = True)
    nom_standard_majuscule = Column(String(200), Nullable = True)
    typecom = Column(String(3), Nullable = True)
    typecom_texte = Column(String(50), Nullable = True)
    reg_code = Column(String(2), Nullable = True)
    reg_nom = Column(String(100), Nullable = True)
    dep_code = Column(String(3), Nullable = True)
    dep_nom = Column(String(100), Nullable = True)
    canton_code = Column(String(5), Nullable = True)
    canton_nom = Column(String(100), Nullable = True)
    epci_code = Column(String(20), Nullable = True)
    epci_nom = Column(String(200), Nullable = True)
    academie_code = Column(String(5), Nullable = True)
    academie_nom = Column(String(100), Nullable = True)
    code_postal = Column(String(5), Nullable = True)
    codes_postaux = Column(String(1048), Nullable = True)
    zone_emploi = Column(String(5), Nullable = True)
    code_insee_centre_zone_emploi = Column(String(5), Nullable = True)
    code_unite_urbaine = Column(String(5), Nullable = True)
    nom_unite_urbaine = Column(String(150), Nullable = True)
    taille_unite_urbaine = Column(Float, Nullable = True)
    type_commune_unite_urbaine = Column(String(20), Nullable = True)
    statut_commune_unite_urbaine = Column(String(100), Nullable = True)
    population = Column(Float, Nullable = True)
    superficie_hectare = Column(Float, Nullable = True)
    superficie_km2 = Column(Numeric(10, 2), Nullable = True)
    densite = Column(Float, Nullable = True)
    altitude_moyenne = Column(Float, Nullable = True)
    altitude_minimale = Column(Float, Nullable = True)
    altitude_maximale = Column(Float, Nullable = True)
    latitude_mairie = Column(Numeric(9, 6), Nullable = True)
    longitude_mairie = Column(Numeric(9, 6), Nullable = True)
    latitude_centre = Column(Numeric(9, 6), Nullable = True)
    longitude_centre = Column(Numeric(9, 6), Nullable = True)
    grille_densite = Column(Float, Nullable = True)
    grille_densite_texte = Column(String(100), Nullable = True)
    niveau_equipements_services = Column(Float, Nullable = True)
    niveau_equipements_services_texte = Column(String(150), Nullable = True)
    gentile = Column(String(150), Nullable = True)
    url_wikipedia = Column(Text, Nullable = True)
    url_villedereve = Column(Text, nullable = True)
    date_creation = Column(DateTime(timezone = True), server_default=func.now()) 

class cities(Base):
    __tablename__ = "fait_cities"
    __table_args__ = {"schema": "Hydromet"}

    postal_code = Column(String(20), primary_key = True) 
    commune_code = Column(String(20), Nullable = False) 
    city_name = Column(String(200), Nullable = False) 
    country = Column(String(3), Nullable = False, default = 'FR') # ISO 3166-1 alpha-2
    latitud = Column(Numeric(9, 6), Nullable = False) 
    longitud = Column(Numeric(9, 6), Nullable = False) 
    water_code = Column(String(15), Nullable = False) 
    timezone = Column(String(50), Nullable = False, default = 'Europe/Paris') 
    active = Column(Boolean, Nullable = False, server_default = True) 
    inserted_at = Column(DateTime(timezone = True), server_default=func.now())
