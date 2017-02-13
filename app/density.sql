/* Density (duac) calculations
Inputs:
    tbl (str): name of input permit table
    year (int): year of permit data
    srid (int): spatial reference of data

Outputs:
    'density<year>': used for density calculations & GROUPing BY permit_number
*/

--ATTACH DATABASE 'I:/WallyG/projects/bp2/data/sde_data.sqlite' AS sde;

BEGIN;

-- Calc duac including total dwellings and total area of parcels intersecting multi-point permits
-- E.g. 1500 S 14TH ST (2014) 62 duac
CREATE TABLE density{year} (
  permit_number TEXT PRIMARY KEY,
  geocode TEXT,
  address TEXT,
  dwellings INTEGER,
  acres REAL,
  duac REAL);
  --condo_proj TEXT);

SELECT AddGeometryColumn("density{year}", "geometry", {srid}, "MULTIPOINT", "XY");

INSERT INTO density{year} SELECT * FROM (
  SELECT 
	permit_number,
    u.geocode AS geocode, 
    p.address AS address,
	dwellings, 
    SUM(Area(u.geometry))/43560.0 AS acres, 
    FLOOR(dwellings/(SUM(Area(u.geometry))/43560.0)) as duac,
	--c.name AS condo_proj,
	p.geometry AS geometry
  FROM (
      SELECT permit_number, address, dwellings, 
        --SUM(dwellings) AS dwellings, 
	    -- Dissolve points
	    ST_Multi(ST_Collect(geometry)) AS geometry 
      FROM {tbl}   
      GROUP BY permit_number) AS p
  JOIN parcels u ON Intersects(p.geometry, u.geometry) 
  --LEFT JOIN condos_dis c ON Intersects(p.geometry, c.geometry) 
  GROUP BY p.permit_number
  ORDER BY p.address);

COMMIT;
--SELECT RecoverGeometryColumn('density{year}', 'geometry', {srid}, 'MULTIPOINT', 2);


/*

-- Make a table to track townhome (th) / condo development activity
CREATE TABLE th_dev{year} (
  name TEXT,
  sum_dwellings INTEGER,
  acres REAL,
  proj_duac REAL);

INSERT INTO th_dev{year} SELECT * FROM (
  SELECT c.name AS name,  
    SUM(sum_dwellings) as sum_dwellings, 
    SUM(Area(c.geometry))/43560.0 AS acres, 
    FLOOR(SUM(sum_dwellings)/(SUM(Area(c.geometry))/43560.0)) AS proj_duac  
  FROM {year} d 
  JOIN condos_dis c 
  ON Intersects(d.geometry, c.geometry) 
  GROUP BY c.name);


-- Change the incorrectly calculated townhome/condo duacs
UPDATE density{year}  
SET duac = (
    SELECT proj_duac
	FROM th_dev{year} t
	JOIN density{year} d ON t.name = d.condo_proj)
WHERE condo_proj IS NOT NULL;

-- Taking the FLOOR of 0.x results in 0.0, when really it should be 1.0
UPDATE density{year} 
SET duac = 1.0 
WHERE duac = 0.0;

UPDATE th_dev{year} 
SET proj_duac = 1.0 
WHERE proj_duac = 0.0;
*/