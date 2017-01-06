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
    dup INT,
    md INT
);


-- Insert City
INSERT OR IGNORE INTO summary VALUES ('City', 0, 0, 0, 0, 0);


-- Insert County
INSERT OR IGNORE INTO summary VALUES ('County', 0, 0, 0, 0, 0);


-- Update row by jurisdiction field in 'summary' table
UPDATE 
    summary 
SET 
    -- Total Permits
    tot_permits = (
        SELECT COUNT(DISTINCT permit_number)
        FROM {tbl}
        ),
    -- Total Dwellings
    tot_dwellings = (
        SELECT SUM(dwellings) 
        FROM (
          SELECT DISTINCT permit_number, dwellings 
          FROM {tbl})
        ),
    -- Sum Single Dwellings (SDs) 
    sd = (
        SELECT SUM(dwellings) FROM (
          SELECT DISTINCT permit_number, dwellings 
          FROM {tbl}
          GROUP BY permit_number 
          HAVING SUM(dwellings) = 1)
        ),
    -- Sum Duplexes
    dup = (
        SELECT SUM(dwellings) 
        FROM (
            SELECT *
            FROM {tbl}
            GROUP BY permit_number
            HAVING dwellings = 2)
        ),
    -- Sum Multidwellings
    md = (
        SELECT SUM(dwellings) FROM (
          SELECT DISTINCT permit_number, dwellings 
          FROM {tbl}
          GROUP BY permit_number 
          HAVING SUM(dwellings) >= 3)
        )
WHERE jurisdiction = '{juris}';
