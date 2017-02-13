/*
summarize.sql -- Creates and enters building permit summary data into a new
table 'summary'.

Formatting Parameters:
{tbl}: table to summarize
{juris}: jurisdiction of summarzing table
*/

-- Create summary table
CREATE TABLE IF NOT EXISTS summary (
    jurisdiction TEXT PRIMARY KEY,
    tot_permits INT,
    tot_dwellings INT,
    sd INT,
    dup_units INT,
    dup_permits INT,
    md_units INT,
    md_permits INT
);


-- Insert City
INSERT OR IGNORE INTO summary VALUES ('city', 0, 0, 0, 0, 0, 0, 0);


-- Insert County
INSERT OR IGNORE INTO summary VALUES ('county', 0, 0, 0, 0, 0, 0, 0);


-- Update row by jurisdiction field in 'summary' table
UPDATE 
    summary 
SET 
    -- Total Permits
    tot_permits = (
        SELECT COUNT(DISTINCT permit_number)
        FROM {tbl}),
    -- Total Dwellings
    tot_dwellings = (
        SELECT SUM(dwellings) FROM (
            SELECT dwellings
            FROM {tbl}
            GROUP BY permit_number)
        ),
    -- Sum Single Dwellings (SDs) 
    sd = (
        SELECT SUM(dwellings) FROM (
            SELECT dwellings
            FROM {tbl}
            GROUP BY permit_number
            HAVING SUM(dwellings) = 1)
        ),
    -- Sum Duplexes
    dup_units = (
        SELECT SUM(dwellings) 
        FROM (
            SELECT *
            FROM {tbl}
            GROUP BY permit_number
            HAVING dwellings = 2)
        ),
    -- Number of Dup permits
    dup_permits = (
        SELECT COUNT(permit_number)
        FROM (
            SELECT *
            FROM {tbl}
            GROUP BY permit_number
            HAVING dwellings = 2)),
    -- Sum Multidwellings
    md_units = (
        SELECT SUM(dwellings) FROM (
            SELECT dwellings
            FROM {tbl}
            GROUP BY permit_number
            HAVING SUM(dwellings) >= 3)
        ),
    -- Number of MD permits
    md_permits = (
        SELECT COUNT(permit_number) FROM (
            SELECT *
            FROM {tbl}
            GROUP BY permit_number
            HAVING dwellings >= 3))
WHERE jurisdiction = LOWER('{juris}');
