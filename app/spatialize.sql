/* spatialize.sql: spatializes permits by various methods.
Author: Garin Wally; Aug 2016

This script gives the non-spatial permit table points derrived from either
the ufda_addr features or the ufda_parcels 'PointsOnSurface' (the Centroid isn't
always confined within the parcel).

Any permit that is not spatialized, i.e.
SELECT * FROM <permit_table> WHERE geometry IS NULL;
will need to be delt with manually. Bummer, I know.
*/

BEGIN;

-- Add geometry column
SELECT AddGeometryColumn('{table}', 'geometry', {srid}, 'MULTIPOINT', 'XY');

-- Add a condo_project column
ALTER TABLE {table} ADD COLUMN condo_project TEXT;

-- Ensure 'dwellings' values are INT
UPDATE {table} SET dwellings = CAST(dwellings AS INT);

/*
-- Apply overrides to permit table
UPDATE {table}
SET 
    geocode = (
        SELECT geocode 
        FROM overrides 
        WHERE overrides.permit_number = {table}.permit_number),
    address = (
        SELECT address 
        FROM overrides 
        WHERE overrides.permit_number = {table}.permit_number)
WHERE permit_number IN (
    SELECT o.permit_number 
    FROM overrides o
    WHERE o.permit_number = {table}.permit_number);
DELETE FROM {table}
  WHERE geocode = 'REMOVE';
*/

-- Join on parcel geocode
UPDATE {table} -- permit table
SET
	notes = 'geocode',
	geometry = (
		SELECT ST_Multi(PointOnSurface(geometry))
		FROM parcels u
		WHERE u.parcelid={table}.geocode)
WHERE geometry IS NULL;


-- Join on full address (exact match)
-- These addresses do not align perfectly with the city's shifted parcels, fix???
UPDATE
	{table} -- permit table
SET
	notes = 'fulladdr',
	geometry = (
		SELECT ST_Multi(geometry)
		FROM addrs a
		WHERE a.fulladdress={table}.address)
WHERE geometry IS NULL;


-- Join on address geocode
/* This unintentionally joins permits with all addresses on a parcel giving the permit more geometry
than it truely deserves, fix???
*/
UPDATE
	{table} -- permit table
SET
	notes = 'a.parcelid',
	geometry = (
		SELECT ST_Multi(geometry)
		FROM addrs a
		WHERE a.parcelid={table}.geocode)
WHERE geometry IS NULL;



SELECT CreateSpatialIndex('{table}', 'geometry');

COMMIT;

