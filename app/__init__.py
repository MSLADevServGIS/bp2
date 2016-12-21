#!/usr/bin/env python
# -*- coding: utf-8 -*-

import processing


def spatialize_script(conn, table, srid):
    _c = conn.cursor()
    _c.execute(open("app/spatialize.sql", "r").read().format(
        table=table, srid=srid))
    _c.fetchall()
    #with open("app/spatialize.sql", "r") as content:
    #    script = content.read()
    #script = script.format(table=table, srid=srid)
    #_c.execute(script)
    return

'''
with open("spatialize.sql", "r") as ss:
    spatialize_script = ss.read()

with open("density.sql", "r") as ds:
    density_script = ds.read()

with open("", "r") as rs:
    region_summary_script = rs.read()
del ss, ds, rs
'''
