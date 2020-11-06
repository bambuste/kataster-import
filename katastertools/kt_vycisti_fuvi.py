#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pomocny skript pre vycistenie zaznamov v subore *.FPU. Vykona prekodovanie do UTF8, odstranenie neplatnych znakov,
spojenie zaznamov nachadzajucich sa na viacerych riadkoch Vysledny subor je generovany na STDOUT (standardny vystup).

Pouzitie: kt_vycisti_fuvi.py subor.fpu [kodovanie] > opraveny_subor.fpu
"""

import re
import sys
import codecs
from pathlib import Path
from typing import List

uplnost_riadku = True
spajac_zaznamov = []


def neplatnost_znakov(znak):
    ordznak = ord(znak)
    if ordznak < 31 or (127 <= ordznak <= 159):
        return False

    try:
        znak.encode('latin2')
    except Exception:
        return False
    return True


def vycisti_fuvi(fpusubor: Path, kodovanie='IBM852') -> List[str]:
    uplnost_riadku = False
    spajac_zaznamov = []
    lines = []

    # sub = codecs.open(fpusubor, "r", encoding=kodovanie)
    sub = open(fpusubor, "r", encoding=kodovanie)

    line: str = sub.readline()
    reg1 = re.compile(r"^\.")
    reg2 = re.compile(r"^$")
    reg3 = re.compile(r";$")
    while line:
        line = ''.join([c for c in line.rstrip() if neplatnost_znakov(c)])
        if reg1.match(line):
            lines.append(line.rstrip())
        elif reg2.match(line):
            lines.append(line.rstrip())
        else:
            if reg3.search(line) and uplnost_riadku is True:
                lines.append(line.rstrip())

            elif reg3.search(line) and uplnost_riadku is False:
                spojeny_zaznam = ''.join(spajac_zaznamov)
                lines.append(spojeny_zaznam.rstrip() + line.rstrip())
                uplnost_riadku = True
                spajac_zaznamov = []
            else:
                spajac_zaznamov.append(line.rstrip())
                uplnost_riadku = False

        line = sub.readline()

    return lines


def main():
    # nazov suboru
    try:
        fpusubor = sys.argv[1]
    except IndexError:
        print(__doc__)
        sys.exit(2)

    # kodovanie
    try:
        kodovanie = sys.argv[2]
    except IndexError:
        print(__doc__)
        sys.exit(2)

    vycisti_fuvi(Path(fpusubor), kodovanie)


if __name__ == '__main__':
    main()
