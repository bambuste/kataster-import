#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skript pre vytvorenie davky SQL prikazov z *.DBF suborov ISKN SR, vhodnych pre import do PostgreSQL.
Tato verzia umoznuje aj spracovanie suborov 'PV'. SQL prikazy su generovane na STDOUT (standardny vystup).

Pouzitie:   kt-import_dbf.py <subor.dbf> > subor.sql              - ulozenie vystupu do suboru
            kt-import_dbf.py <subor.dbf> | psql <nazov_databazy>  - priamy import do databazy

Poznamka:	Je potrebne mat nainstalovany modul 'dbf' (https://pypi.python.org/pypi/dbf).
"""

import os, sys
import re
from datetime import datetime
import dbf

t = datetime.now()
cas = t.strftime("%d-%m-%Y  %H:%M:%S")
verzia = "%s.%s.%s" % __import__('katastertools').VERSION[:3]

try:
    dbf_subor_full_path = sys.argv[1]
    dbf_subor = os.path.basename(sys.argv[1])

    typ_dbf = dbf_subor.lower()[:2]
    ku = int(dbf_subor.lower()[-10:-4])

    if not os.path.exists(dbf_subor_full_path) or dbf_subor[-3:].lower() != 'dbf':
        raise Exception
except:
    print(f"-- E: Neplatny subor DBF ({dbf_subor}).\n")
    print(__doc__)
    sys.exit(2)

# Nacitanie DBF suboru
dbfile = dbf.Table(dbf_subor_full_path)
dbfile.open()

# Nacitanie nazvov stlpcov ([:-1] odstranuje stlpec CRC)
zoznam_stlpcov = dbf.get_fields(dbf_subor_full_path)[:-1]

numdata = {
    'bp': ['icp', 'clv', 'pcs', 'bnp', 'cip', 'cib', 'vym', 'pec', 'mss', 'cit', 'men', 'pvz', 'kpv', 'cen', 'oce',
           'crc'],
    'cs': ['ics', 'clv', 'cel', 'cpa', 'pec', 'mss', 'vym', 'ums', 'drs', 'pvz', 'kpv', 'don', 'cen', 'oce', 'zcs',
           'crc'],
    'ep': ['cpa', 'cpu', 'vym', 'kvv', 'drp', 'don', 'pkk', 'mss', 'pec', 'cel', 'clv', 'kpv', 'ump', 'pvz', 'miv',
           'clm',
           'drv', 'ndp', 'prp', 'spn', 'mlm', 'cen', 'oce', 'pcp', 'crc'],
    'lv': ['clv', 'psv', 'rzs', 'kpv', 'rzp', 'pvz', 'pep', 'ppl', 'crc'],
    'pa': ['cpa', 'vym', 'kvv', 'drp', 'don', 'pkk', 'mss', 'pec', 'cel', 'clv', 'kpv', 'ump', 'pvz', 'miv', 'clm',
           'drv',
           'prp', 'spn', 'ndp', 'dn1', 'dn2', 'dn3', 'dn4', 'dn5', 'dn6', 'dn7', 'dn8', 'mlm', 'cen', 'oce', 'crc'],
    'pk': ['ump', 'cpk', 'cpu', 'crc'],
    'pv': ['idc', 'clv', 'pcs', 'idt', 'idn', 'cde', 'drf', 'pvz', 'kpv', 'crc'],
    'uz': ['cel', 'sip', 'sek', 'pks', 'pvz', 'rzp', 'kpv', 'ppe', 'ico', 'crc'],
    'vl': ['clv', 'pcs', 'cit', 'men', 'pvz', 'kpv', 'ico', 'sta', 'rci', 'stb', 'tvl', 'tuc', 'dru', 'tid', 'crc'],
    'nj': ['cel', 'ico', 'pvz', 'sek', 'sip', 'tid', 'crc']
}
nullchar = re.compile('\00')  # invalid null character (can be also replace by sed $ sed -i 's/\x0//g')
nonechar = re.compile('None')

# INSERT
print("-- I: CAS: %s, VYTVORIL: %s, VERZIA: %s" % (cas, os.environ['USER'], verzia))

print('SET client_encoding TO UTF8;')
print('BEGIN;')

for rec in dbfile:
    # if not rec.has_been_deleted:
    if not dbf.is_deleted(rec):
        hodnoty = ''
        for stlpec in zoznam_stlpcov:
            try:
                hodnota = rec[stlpec].encode('UTF-8').strip()
            except:
                hodnota = str(rec[stlpec]).strip()

            # odstranenie retazca 'None' v ciselnych stlpcoch
            if stlpec in numdata[typ_dbf]:
                hodnota = nonechar.sub('0', hodnota)

            hodnoty += "$$" + hodnota + "$$, "

        print(('INSERT INTO kn_%s (ku, %s) VALUES (%s, %s);' % (
            typ_dbf, ', '.join(zoznam_stlpcov), ku, nullchar.sub('', hodnoty.strip(', ')))))

# vytvorenie jedinecneho identifikatora parcely - parckey
if typ_dbf in ('cs', 'pa'):
    print(
        "UPDATE kn_%s SET parckey = (ku::text || '00' || to_char(cpa, 'FM000000000')) WHERE ku = '%s';" % (typ_dbf, ku))

if typ_dbf == 'ep':
    print(
        "UPDATE kn_%s SET parckey = (ku::text || to_char(cpu, 'FM00') || to_char(cpa, 'FM000000000')) WHERE ku = '%s';" % (
            typ_dbf, ku))

print('END;')

# vim: set ts=4 sts=4 sw=4 noet:
