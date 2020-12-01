#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import logging
import datetime
from pathlib import Path
from typing import Optional, IO

from katastertools.VgiShp import io
from katastertools.VgiShp import data

KNOWN_LAYERS = {
    'b': ('BPEJ', u'hranice areálov bonitovaných pôdno-ekologických jednotiek'),
    't': ('KATUZ', u'hranica katastrálneho územia'),
    'k': ('KLADPAR', u'hranice a čísla parciel registra C, symboly druhov pozemkov'),
    'l': ('LINIE', u'ďalšie prvky polohopisu (inžinierske siete, hranica CHKO ...)'),
    'p': ('POPIS', u'sídelné a nesídelné názvy'),
    'u': ('UOV', u'hranice a čísla parciel registra E'),
    'r': ('ZAPPAR', u'hranica druhov pozemkov, ktoré nie sú v KLADPAR'),
    'n': ('ZNACKY', u'mapové značky okrem značiek druhov pozemkov'),
    'z': ('ZUOB', u'hranica zastavaného územia obce'),
}


class ConsoleHandler(logging.StreamHandler):
    """A handler that logs to sys.stdout by default with only error
    (logging.ERROR and above) messages going to sys.stderr."""

    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.stream: Optional[IO] = None  # reset it; we are not going to use it anyway

    def emit(self, record):
        if record.levelno >= logging.ERROR:
            self.__emit(record, sys.stderr)
        else:
            self.__emit(record, sys.stdout)

    def __emit(self, record, strm):
        self.stream = strm
        logging.StreamHandler.emit(self, record)

    def flush(self):
        # Workaround a bug in logging module
        # See:
        #   http://bugs.python.org/issue6333
        if self.stream and hasattr(self.stream, 'flush') and not self.stream.closed:
            logging.StreamHandler.flush(self)


def objekt_vrstvy(meno_vrstvy, atributy):
    if meno_vrstvy == "KLADPAR":
        return data.KLADPAR(atributy)
    elif meno_vrstvy == "ZAPPAR":
        return data.ZAPPAR(atributy)
    elif meno_vrstvy == "KATUZ":
        return data.KATUZ(atributy)
    elif meno_vrstvy == "LINIE":
        return data.LINIE(atributy)
    elif meno_vrstvy == "POPIS":
        return data.POPIS(atributy)
    elif meno_vrstvy == "ZNACKY":
        return data.ZNACKY(atributy)
    elif meno_vrstvy == "ZUOB":
        return data.ZUOB(atributy)
    elif meno_vrstvy == "UOV":
        return data.UOV(atributy)
    elif meno_vrstvy == "BPEJ":
        return data.BPEJ(atributy)
    else:
        raise KeyError(meno_vrstvy)


def process_files(file_path: Path, layers: dict, output_directory: Path, output_format: str = 'sql-copy',
                  layer_config: str = '', process_unknown_layers: bool = False, debug: bool = False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    handler = ConsoleHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.handlers = []
    logger.addHandler(handler)

    logging.info("**************** ZACIATOK KONVERZIE ***********************")
    logging.info(f'CAS {time.strftime("%a, %d %b %Y %H:%M:%S")}')

    # otvor vstupny subor
    logging.info(f'NAZOV SUBORU: {str(file_path)}')
    try:
        vstup = io.Citac(file_path)
    except io.MedzeraVNazveSuboru as vstupny_subor:
        logging.error(f"Vstup {vstupny_subor} obsahuje medzeru v nazve suboru")
        sys.exit(2)
    except io.NieJeSubor as vstupny_subor:
        logging.error(f"Vstup {vstupny_subor} nie je subor")
        sys.exit(2)
    except io.ZlyTypSuboru as vstupny_subor:
        logging.error(f"Vstup {vstupny_subor} nie je vgi subor")
        sys.exit(2)

    if output_directory.is_file():
        logging.error(f"'{str(output_directory)}' nie je platnym adresarom")
        sys.exit(2)
    else:
        output_directory.mkdir(parents=True, exist_ok=True)

    # ktore vrstvy v ktorom type nas zaujimaju
    objects_selection = {'KN': ('KATUZ', 'KLADPAR', 'LINIE', 'POPIS', 'ZAPPAR', 'ZUOB', 'ZNACKY'),
                         'UO': ('KATUZ', 'ZAPPAR', 'UOV', 'ZUOB'),
                         'BJ': ('KATUZ', 'BPEJ')}
    podporovane_objekty = []
    for vrstvy in objects_selection.values():
        podporovane_objekty.extend(vrstvy)

    atributy = {'SUBOR': file_path.name}

    try:
        # nacitaj hlavicku
        for row in vstup:
            typ = row[:2]
            if typ in ('&V', '&R', '&B'):
                logging.info(row[1:])
                if typ == '&B':
                    atrib = row[3:].split('=')
                    atributy[atrib[0]] = atrib[1]

                elif typ == '&V':
                    row = row.split(' ')
                    atributy['NAZOV'] = row[1]
                    atributy['TYP'] = row[1][0:2].upper()
                    atributy['KU'] = row[1][2:9]
                    atributy['redukciaY'] = row[4]
                    atributy['redukciaX'] = row[5]

                    if atributy.get('TYP') not in objects_selection:
                        if process_unknown_layers:
                            logging.warning(f"Neznamy typ suboru {atributy.get('TYP')}")
                        else:
                            logging.error(f"Neznamy typ suboru {atributy.get('TYP')}")
                            sys.exit(2)

                    try:
                        if int(atributy['KU']) < 800000 or int(atributy['KU']) > 999999:
                            raise io.NeplatneKU
                    except(ValueError, io.NeplatneKU):
                        logging.error(f"Neplatne KU {atributy.get('KU')}")
            else:
                vstup.spat(1)
                break

        # konverzia datumu z textovej hodnoty atributu AKTUAL na hodnotu pouzitelnu pre datovy typ OFTDateTime
        try:
            aktual = datetime.datetime.strptime(atributy.get('AKTUAL'), "%d.%m.%Y %H:%M:%S")
            # 104=GMT+1
            atributy['AKTUAL'] = (aktual.year, aktual.month, aktual.day, aktual.hour, aktual.minute, aktual.second, 104)
        except Exception:
            atributy['AKTUAL'] = (1970, 1, 1, 0, 0, 0, 0)

        # citaj subor
        nazov_suboru = file_path.stem
        zapisovac = data.Zapisovac(nazov_suboru, str(output_directory), output_format, nazvy_vrstiev=layers,
                                   nastavenia_vrstvy=layer_config)
        poc_objektov = 0

        bodove_objekty = set()
        liniove_objekty = set()
        raw_objekty = io.CitacObjektov(vstup)
        for idx, raw_objekt in enumerate(raw_objekty):
            # rozhodnem sa ci objekt spracovavam alebo nie
            while not raw_objekt['riadky'][0].startswith('&'): # this was not here...
                raw_objekt['riadky'].pop(0)
            objekt_id = raw_objekt['riadky'][0].split(' ')[2]
            nazov_vrstvy = raw_objekt["meno_vrstvy"]

            if nazov_vrstvy in layers.values() and nazov_vrstvy in objects_selection.get(atributy.get('TYP'), ()):
                logging.debug(f"Spracuvavam objekt {nazov_vrstvy} {objekt_id}")
                objekt = objekt_vrstvy(nazov_vrstvy, atributy)
                for row in raw_objekt["riadky"]:
                    try:
                        objekt.pridaj_riadok(row)
                    except data.NepodporovanaVeta:
                        logging.warning(f"Nespracovany riadok: {row}")
                objekt_data = objekt.data()

                if objekt_data.get("pocet_uzatvoreni", 0) > 0:
                    logging.debug("Skusam otocit objekt")
                    otoceny_objekt = objekt_vrstvy(nazov_vrstvy, atributy)
                    for row in raw_objekty.posun_skoky():
                        otoceny_objekt.pridaj_riadok(row)
                    otoceny_objekt_data = otoceny_objekt.data()

                    if otoceny_objekt_data["pocet_uzatvoreni"] < objekt_data["pocet_uzatvoreni"]:
                        logging.debug("Vyberam otoceny objekt")
                        objekt_data = otoceny_objekt_data

            elif process_unknown_layers and nazov_vrstvy not in podporovane_objekty:
                logging.debug(f"Spracuvavam objekt {nazov_vrstvy} {objekt_id}")
                if nazov_vrstvy in liniove_objekty:
                    objekt = data.INE_LINIE(atributy, nazov_vrstvy)
                else:
                    objekt = data.INE_BODY(atributy, nazov_vrstvy)

                for row in raw_objekt["riadky"]:
                    try:
                        objekt.pridaj_riadok(row)
                    except data.NepodporovanaVeta:
                        if isinstance(objekt, data.INE_LINIE):
                            logging.warning(f"Nespracovany riadok: {row}")
                        else:
                            objekt = data.INE_LINIE(atributy, nazov_vrstvy)
                            for row in raw_objekt["riadky"]:
                                try:
                                    objekt.pridaj_riadok(row)
                                except data.NepodporovanaVeta:
                                    logging.warning(f"Nespracovany riadok: {row}")
                            break
                if isinstance(objekt, data.INE_LINIE):
                    liniove_objekty.add(nazov_vrstvy)
                else:
                    bodove_objekty.add(nazov_vrstvy)
                objekt_data = objekt.data()
            else:
                logging.debug(f"Vynechavam objekt {nazov_vrstvy} {objekt_id}\n")
                continue

            for bodovy_objekt in bodove_objekty:
                if bodovy_objekt in liniove_objekty:
                    logging.error("Niektore bodove objekty boli ulozene ako liniove.\n")
                    sys.exit(2)

            for sprava in objekt_data['spravy']:
                logging.info(sprava)

            if objekt_data.get('geometricke_objekty'):
                logging.debug("Ukladam objekt\n")
                zapisovac.uloz(objekt_data)
                poc_objektov = poc_objektov + 1
            else:
                logging.warning(f"Objekt {objekt_id} neobsahuje platnu geometriu, vynechavam jeho ulozenie")

        # vypis pocet objektov v spracovavanej vrstve VGI suboru
        if poc_objektov > 0:
            logging.info(f"POCET OBJEKTOV: {poc_objektov:d}")
        else:
            logging.error("POCET OBJEKTOV: 0")

    except io.ChybaKoncovaVeta:
        logging.error("Chyba koncova veta")
        sys.exit(2)
    logging.info("***************** KONIEC KONVERZIE ************************")


def main():
    # spracuj prepinace
    volby = {
        'file_path': None,
        'layers': {k: v[0] for k, v in KNOWN_LAYERS.items() if k in ('t', 'k', 'l', 'p', 'r', 'n', 'z',)},
        'output_directory': Path(__file__).parents[1] / 'data' / 'sql_g',
        'output_format': 'sql-copy',
        'layer_config': '',
        'process_unknown_layers': False,
        'debug': False,
    }

    for f in (Path(__file__).parents[1] / 'data' / 'vgi').rglob('KN*.vgi'):
        volby['file_path'] = f
        process_files(**volby)


if __name__ == "__main__":
    main()
