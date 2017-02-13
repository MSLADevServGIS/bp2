"""
permits.py -- Building Permit Database Script
Author: Garin Wally; April-July 2016

--NEW--
"""

import os
from glob import glob


import defopt
from usaddress import parse as addrparse

import aside
import dslw
import dslw.arcio

os.chdir(r"I:\WallyG\projects\bp2")
import app


# =============================================================================
# DATA PATHS

parcels = r"Database Connections\gisrep.sde\gisrep.SDE.Parcels\gisrep.SDE.Parcels"
condos = r"Database Connections\gisrep.sde\gisrep.SDE.Parcels\gisrep.SDE.All_Condos"
annex = r"Database Connections\gisrep.sde\gisrep.SDE.AdministrativeArea\gisrep.SDE.Annexations"
nhoods = r"Database Connections\gisrep.sde\gisrep.SDE.AdministrativeArea\gisrep.SDE.NH_Council_Boundaries"
ufda = r"I:\ArcExplorer\Data\Planning_to_sde.gdb\Mt_St_Plane\UFDA_regions"
addrs = r"I:\ArcExplorer\Data\Structures\Address.gdb\AddrsFt"


# =============================================================================
# DATA (No touching)

# Path to database for storing copies from SDE, etc.
SDE_DATA = "data/sde_data.sqlite"

# Global srid to reproject to; QGIS-friendly
SRID = 2256
data = [
    {"path": parcels, "name": "parcels"},
    {"path": condos, "name": "condos"},  # TODO: dissolve?
    {"path": annex, "name": "annexations"},
    {"path": nhoods, "name": "nhoods"},
    {"path": ufda, "name": "ufda_regions"},
    {"path": addrs, "name": "addrs"}
    ]
# Names correlate with table names in .sql scripts


class Processor(object):
    def __init__(self, year):
        self.year = year
        # Set base directory
        self.base_dir = "data/{year}".format(year=year)
        # Get report file path
        self.city_rpts = [os.path.abspath(f).replace("\\", "/") for f in
                          glob("{base}/city_{year}.xlsx".format(
                               base=self.base_dir, year=self.year))]
        # Set db path
        self.db = os.path.join(self.base_dir, "bp{year}.sqlite".format(
            year=self.year))
        # Create db
        aside.nix.write("Create/Connect to db")
        self.conn = dslw.SpatialDB(self.db, verbose=False)
        self.cur = self.conn.cursor()
        aside.nix.ok()

    def prepare_city(self):
        """Get report by year, process, load into SQLite db.

        Args:
            year (int): the year to process.
        """
        self.juris = "City"
        # Process; returns output path
        aside.nix.write("Process XLSX")
        self.out_csv = app.processing.city(self.city_rpts[0])
        aside.nix.ok()
        # Get name (e.g. 'city_2016_processed')
        self.table_name = os.path.basename(self.out_csv).split(".")[0]
        aside.nix.info("Table: " + self.table_name)

        # Load csv to db
        aside.nix.write("Insert CSV")
        dslw.csv2lite(self.conn, self.out_csv)
        aside.nix.ok()

    def spatialize(self):
        # Add notes column
        aside.nix.write("Spatialize permits")
        self.cur.execute("ALTER TABLE {} ADD COLUMN notes TEXT".format(
            self.table_name))
        # Backup
        clone_q = "SELECT CloneTable('main', '{0}', '{0}_bk', 1)"
        self.cur.execute(clone_q.format(self.table_name))
        # Attach spatial db
        self.cur.execute("ATTACH DATABASE '{}' AS sde_data;".format(
            SDE_DATA))
        # Spatialize
        app.spatialize_script(self.conn, self.table_name, SRID)

        # Special detail for Townhome/Condo points or for when the parcel data
        # or address data hasn't been updated just yet.
        null_qry = "SELECT address, geocode FROM {tbl} WHERE geometry IS NULL"
        null_qry = null_qry.format(tbl=self.table_name)
        update_q = ("UPDATE {tbl} "
                    "SET notes = 'TH/C', "
                    "geometry = ("
                    "  SELECT ST_Multi(geometry) "
                    "  FROM addrs a "
                    "  WHERE a.addnum = {addrnum} AND a.roadname = '{road}') "
                    "WHERE geometry IS NULL AND geocode = '{geocode}'")
        nulls = self.cur.execute(null_qry).fetchall()
        # Process only if the query returns non-None values
        if any([r[0] for r in nulls]):
            for row in nulls:
                # Parse each address into a tuple
                parsed = addrparse(row[0])
                # Convert the tuple into a dictionary (reverse)
                d = {v: k for k, v in dict(parsed).iteritems()}
                # Format the update statement using the parsed information
                update = update_q.format(
                    tbl=self.table_name, addrnum=d["AddressNumber"],
                    road=d["StreetName"], geocode=row[1])
                # Execute the update statement
                self.cur.execute(update)
        # Check again for NULL geometries
        nulls = self.cur.execute(null_qry).fetchall()
        null_df = dslw.utils.Fetch(self.cur).as_dataframe()
        if len(null_df) > 0:
            aside.nix.fail()
            print("\n{} geometries are NULL".format(len(null_df)))
            print(null_df)
            print("\nSee README about overriding values")
        else:
            aside.nix.ok()

    def calc_density(self):
        # Density
        self.density_table = "density{}".format(self.year)
        aside.nix.write("Calculate 'density<year>' table")
        with open("app/density.sql", "r") as script:
            density_sql = script.read()
            density = density_sql.format(
                tbl=self.table_name, year=self.year, srid=SRID)
        self.cur.execute(density).fetchall()
        aside.nix.ok()

    def summarize(self):
        # Summarize
        aside.nix.write("Create 'summary' table")
        with open("app/summarize.sql", "r") as script:
            summarize_sql = script.read()
            summarize = summarize_sql.format(
                tbl=self.density_table, juris=self.juris)
        self.cur.execute(summarize).fetchall()
        aside.nix.ok()

        print("")
        check_sum = ("SELECT jurisdiction, tot_dwellings, sd, dup_units, md_units "
                     "FROM summary")
        df = dslw.utils.Fetch(self.cur.execute(check_sum)).as_dataframe()
        print(df)
        print("")
        total = sum([df["sd"].ix[0],
                     df["dup_units"].ix[0],
                     df["md_units"].ix[0]])
        if df["tot_dwellings"].ix[0] != total:
            aside.nix.warn("Total does not match")
        aside.status.custom("COMPLETE", "cyan")

    def process_city(self):
        self.prepare_city()
        self.spatialize()
        self.calc_density()
        self.summarize()


def process_city(year):
    """Get report by year, process, load into SQLite db.

    Args:
        year (int): the year to process.
    """
    p = Processor(year)
    p.process_city()
    return

if __name__ == "__main__":
    y = int(raw_input("What year of permit data? "))
    process_city(y)
