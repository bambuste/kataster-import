#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import stat
from pathlib import Path


class Citac:
    """Trieda starajuca sa o citanie vstupneho suboru. Citanie prebieha po riadkoch. Dokaze sa
    posuvat aj dozadu"""

    def __init__(self, file_path: Path):
        try:
            mode = os.stat(str(file_path))[stat.ST_MODE]
            if stat.S_ISREG(mode):
                self._file = open(str(file_path), "r", encoding='cp1250')

                if ' ' in str(file_path):
                    raise MedzeraVNazveSuboru(str(file_path))
                if self._file.read(2) != "&V":
                    raise ZlyTypSuboru(str(file_path))
            else:
                raise NieJeSubor(str(file_path))
        except OSError as e:
            raise NieJeSubor(e)

        self._file.seek(0)
        self._precitane_bajty = 0
        self._dlzka_riadkov = []
        self._precitany_riadok = self._file.readline()

    def __del__(self):
        self.zavriet()

    def __getitem__(self, index):
        riadok = self._precitany_riadok
        self._dlzka_riadkov.append(len(riadok))
        self._precitane_bajty += len(riadok)

        if riadok == "":
            self.zavriet()
            raise ChybaKoncovaVeta
        elif riadok[:2] == '&K':
            self.zavriet()
            raise IndexError
        else:
            self._precitany_riadok = self._file.readline()
            # ak veta pokracuje na dalsom riadku vo vstupnom subore, spoj ju do jedneho riadku
            if self._precitany_riadok.startswith("\t"):
                self._precitane_bajty += len(self._precitany_riadok)
                self._dlzka_riadkov[-1] += len(self._precitany_riadok)
                riadok = riadok.rstrip() + ' ' + self._precitany_riadok.lstrip()
                self._precitany_riadok = self._file.readline()
            return riadok.strip()

    def spat(self, index: int):  # posunie sa spat o dany pocet riadkov
        z = 0
        for x in self._dlzka_riadkov[-index:]:
            z += x
        self._precitane_bajty -= z
        self._file.seek(self._precitane_bajty)
        self._precitany_riadok = self._file.readline()
        self._precitany_riadok = self._file.readline()

    def zavriet(self):
        if self._file:
            self._file.close()
            self._file = None

    def je_koniec_suboru(self):
        return self._file is None


class CitacObjektov:
    """Trieda pomocou Citaca cita subor. Citanie prebieha po objektoch. V pripade potreby dokaze otocit poradie
    riadkov v objekte"""

    def __init__(self, citac: Citac):
        self.__citac: Citac = citac
        self.__koniec_suboru = False

    def __nacitaj_dalsi_objekt(self):
        self.__objekt = []
        self.__meno_vrstvy = ""
        prvy = False
        try:
            for riadok in self.__citac:
                if riadok[:2] == "&O" and not prvy:
                    prvy = True
                    self.__meno_vrstvy = riadok.split(' ')[1].upper()
                    self.__objekt.append(riadok)
                elif riadok[:2] == "&O" and prvy:
                    self.__citac.spat(1)
                    return
                elif riadok[:2] == "&*":
                    pass
                else:
                    self.__objekt.append(riadok)
        except ChybaKoncovaVeta:
            sys.stderr.write("[ERROR]: Chyba koncova veta\n")
            return

    def __getitem__(self, index):
        if not self.__citac.je_koniec_suboru():
            self.__nacitaj_dalsi_objekt()
            return {
                "meno_vrstvy": self.__meno_vrstvy,
                "riadky": self.__objekt,
            }
        else:
            raise IndexError

    def posun_skoky(self):
        hranice = []
        zaciatok = False
        skok = False
        i = 0
        for riadok in self.__objekt:
            if riadok[:4] == "&L P" and "S=" not in riadok:
                if zaciatok:
                    if skok:
                        hranice.append((zaciatok, i))
                    zaciatok = i
                    skok = False
                else:
                    zaciatok = i
            elif riadok[:1] == "&" and zaciatok:
                if skok:
                    hranice.append((zaciatok, i))
                zaciatok = False
                skok = False
            elif riadok[:2] in ("NL", "NR", "NC"):
                skok = True
            i += 1

        if zaciatok and skok:
            hranice.append((zaciatok, i))

        if hranice:
            ret = self.__objekt[:hranice[0][0]]
            for hranica in hranice:
                o = self.__objekt[hranica[0]:hranica[1]]
                upravene_o = []
                skocil = False
                for riadok_o in o:
                    if riadok_o[:2] in ("NL", "NR", "NC"):
                        if skocil:
                            upravene_o.append(riadok_o)
                        else:
                            skocil = True
                            upravene_o.append(riadok_o[1:])
                    else:
                        if skocil:
                            upravene_o.append(f"N{riadok_o}")
                            skocil = False
                        else:
                            upravene_o.append(riadok_o)

                ret += upravene_o
            if hranice[-1][1] < len(self.__objekt):
                ret += self.__objekt[hranice[-1][1]:]
            return ret
        else:
            return self.__objekt


class NieJeSubor(Exception):
    pass


class ZlyTypSuboru(Exception):
    pass


class ChybaKoncovaVeta(Exception):
    pass


class NeplatneKU(Exception):
    pass


class MedzeraVNazveSuboru(Exception):
    pass

# vim: set ts=4 sts=4 sw=4 noet:
