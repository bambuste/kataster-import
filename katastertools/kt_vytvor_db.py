#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skript pre vytvorenie SQL prikazov pre vytvorenie databazy pre data Katastra.
Vysledny SQL skript je generovany na STDOUT (standardny vystup). Cielova
databaza musi obsahovat instalaciu PostGISu.

Pouzitie:
    $ createdb -T template_postgis <nazov_databazy>
    $ kt_vytvor_db.py | psql <nazov_databazy>
"""
import os
from pathlib import Path

from katastertools import VgiShp


def main():
    sql_subory = (
        Path(__file__).parent / 'sql' / 'popisne-data.sql',
        Path(__file__).parent / 'sql' / 'graficke-data.sql',
    )

    # vytvorenie schem
    print('CREATE SCHEMA kataster;')
    print('SET search_path TO kataster,public;')

    # vytvorenie tabuliek
    for sql_subor in sql_subory:
        with sql_subor.open('r') as f:
            print(f.read())

    print('VACUUM ANALYZE;')


if __name__ == '__main__':
    main()
