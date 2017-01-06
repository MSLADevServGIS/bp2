#!/usr/bin/env python
# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
permits.py -- Building Permit Database Script
Author: Garin Wally; April-July 2016

--NEW--
"""

import os
from glob import glob


import defopt

import aside
import dslw
import dslw.arcio

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


def update_base(replace=False):
    """Updates the sde_data.sqlite database from various data.

    ::

        $python permits2.py update_base --replace True
        None

    Keyword Arguments:
        replace (bool): option to delete and recreate the existing db.
    """
    if replace:
        aside.nix.write("Replacing database...")
        os.remove(SDE_DATA)
        aside.nix.ok()
    conn = dslw.SpatialDB(SDE_DATA, verbose=False)
    print("Getting data...")
    print("This will take a long time!")
    for fc in data:
        if fc["name"] not in conn.get_tables():
            aside.nix.write(fc["name"])
            dslw.arcio.arc2lite(conn, fc["path"], fc["name"], t_srid=SRID)
            aside.nix.ok()
    conn.close()
    print("Done")
    return


def process_city(year):
    """Get report by year, process, load into SQLite db.

    Args:
        year (int): the year to process.
    """
    # Set base directory
    base_dir = "data/{year}".format(year=year)
    # Get report file path
    city_rpts = [os.path.abspath(f).replace("\\", "/") for f in
                 glob("{base}/city_{year}.xlsx".format(
                     base=base_dir, year=year))]
    #rpt_name = os.path.basename(city_rpts[0]).split(".")[0]
    # Process; returns output path
    aside.nix.write("Process XLSX")
    out_csv = app.processing.city(city_rpts[0])
    aside.nix.ok()
    # Get name (e.g. 'city_2016_processed')
    table_name = os.path.basename(out_csv).split(".")[0]
    aside.nix.info("Table: " + table_name)
    # Set db path
    db = os.path.join(base_dir, "bp{year}.sqlite".format(year=year))
    # Create db
    aside.nix.write("Create db")
    conn = dslw.SpatialDB(db, verbose=False)
    cur = conn.cursor()
    aside.nix.ok()
    # Load csv to db
    aside.nix.write("Insert CSV")
    dslw.csv2lite(conn, out_csv)#, rpt_name)
    aside.nix.ok()
    # Add notes column
    aside.nix.write("Spatialize permits")
    cur.execute("ALTER TABLE {} ADD COLUMN notes TEXT".format(table_name))
    # Backup
    cur.execute("SELECT CloneTable('main', '{0}', '{0}_bk', 1)".format(
        table_name))
    # Attach spatial db
    cur.execute("ATTACH DATABASE '{}' AS sde_data;".format(
        SDE_DATA))
    # Spatialize
    app.spatialize_script(conn, table_name, SRID)
    aside.nix.ok()
    # Summarize
    aside.nix.write("Summary tables")
    with open("app/summarize.sql", "r") as script:
        summarize_sql = script.read()
        summarize = summarize_sql.format(tbl=table_name, juris="City")
    cur.execute(summarize)
    aside.nix.ok()

    aside.status.custom("COMPLETE", "cyan")
    return


if __name__ == "__main__":
    # Arg Parser stuff
    defopt.run(update_base, process_city)
