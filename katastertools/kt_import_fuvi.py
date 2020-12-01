#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skript pre vytvorenie davky SQL prikazov z FPU/FUVI suborov ISKN SR, vhodnych pre import do PostgreSQL.
SQL prikazy su generovane na STDOUT (standardny vystup).

Pouzitie: 	kt_import_fuvi.py.py <subor.fpu> > subor.sql 		- ulozenie vystupu do suboru
            kt_import_fuvi.py.py <subor.fpu> | psql <nazov_databazy>	- priamy import do databazy

POZNAMKA: Pred spustenim skriptu je potrebne vycistit FPU pomocou skriptu 'kt_vycisti_fuvi.py.py'
"""

import sys
import re
import os
import _io
from datetime import datetime
from pathlib import Path
from typing import List, Union

from katastertools import __VERSION__


def process_line(riadok: str, kluce: dict, zoznam_ku: list, result: list):
    if re.match(r"^\.", riadok):
        prem = riadok.strip(".").split()[0]

        try:
            hodn_prem = riadok.strip(".").split()[1]
        except:
            hodn_prem = ""

        kluce[prem] = hodn_prem

        # pridanie konvertovaneho KU do zoznamu
        if prem == 'KATASTRALNE_UZEMIE':
            zoznam_ku.append(hodn_prem)

    elif re.match(r"^$", riadok):
        pass
    else:
        # ziskanie cisla KU
        sql_ku = kluce['KATASTRALNE_UZEMIE']

        # ziskavanie nazvov stlpcov
        pol = kluce['POLOZKY'].split(";")
        pol2 = '\"' + '\",\"'.join(pol)
        sql_stlpce = "\"ku\"," + pol2.replace("KN-", "")[:-2].lower()

        # ziskanie nazvu db tabulky
        sql_tab = kluce['SKUPINA'].replace("KN-", "").lower()

        # ziskanie hodnot
        kn_hodn = riadok.split(";")
        sql_hodn = f"$${sql_ku}$$, $${'$$, $$'.join(kn_hodn)[:-5]}$"

        # vytvorenie SQL prikazu
        result.append(f"INSERT INTO kn_{sql_tab} ({sql_stlpce}) VALUES ({sql_hodn});")


def process_list(data: List[str]) -> tuple:
    t = datetime.now()
    cas = t.strftime("%d-%m-%Y  %H:%M:%S")

    kluce = {}
    zoznam_ku = []
    result = [f"-- I: CAS: {cas}, VYTVORIL: {os.environ['USER']}, VERZIA: {__VERSION__}",
              'SET client_encoding TO UTF8;',
              "BEGIN;"]

    for item in data:
        process_line(item, kluce, zoznam_ku, result)

    return result, zoznam_ku


def process_file(sub) -> tuple:
    t = datetime.now()
    cas = t.strftime("%d-%m-%Y  %H:%M:%S")

    kluce = {}
    zoznam_ku = []
    result = [f"-- I: CAS: {cas}, VYTVORIL: {os.environ['USER']}, VERZIA: {__VERSION__}",
              'SET client_encoding TO UTF8;',
              "BEGIN;"]

    riadok = sub.readline()
    while riadok:
        process_line(riadok, kluce, zoznam_ku, result)
        riadok = sub.readline()

    return result, zoznam_ku


def import_fuvi(data: Union[Path, _io.BufferedRandom, list]) -> List[str]:
    if isinstance(data, Path):
        sub = open(data, "r")
        result, zoznam_ku = process_file(sub)
    elif isinstance(data, _io.BufferedRandom):
        result, zoznam_ku = process_file(data)
    elif isinstance(data, list):
        result, zoznam_ku = process_list(data)
    else:
        raise Exception(f'Wrong input for {data}')

    # vytvorenie jedinecneho identifikatora parcely - parckey
    for u in zoznam_ku:
        result.append(f"UPDATE kn_cs SET parckey = ku::text || '00' || to_char(cpa, 'FM000000000') WHERE ku = '{u}';")
        result.append(
            f"UPDATE kn_ep SET parckey = ku::text || to_char(cpu, 'FM00') || to_char(cpa, 'FM000000000') WHERE ku = '{u}';")
        result.append(f"UPDATE kn_pa SET parckey = ku::text || '00' || to_char(cpa, 'FM000000000') WHERE ku = '{u}';")

    result.append("END;")
    return result


def main():
    try:
        f = sys.argv[1]
        f = Path(f)
    except IndexError:
        print(__doc__)
        sys.exit(2)

    if not f.exists():
        raise FileExistsError(f'{str(f)}')

    import_fuvi(f)


if __name__ == '__main__':
    main()
