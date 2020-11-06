"""
Vykona konverziu dat Katastra do SQL, ESRI Shapefile a Microstation DGN 7.
Pouzitie: kt_sql <kataster_dir>

Struktura adresara <kataster_dir>:
 * adresar 'vgi'             - subory VGI
 * adresar 'dbf' alebo 'fpu' - subory DBF resp. FPU+FPT
V pripade, ze existuje adresar 'dbf' aj 'fpu', na konverziu sa pouziju data vo formate FPU.
"""
import sys
import click
import tempfile
import shutil
from pathlib import Path

from katastertools.kt_vycisti_fuvi import vycisti_fuvi
from katastertools.kt_import_fuvi import import_fuvi


def create_temporary_copy(src: Path) -> tempfile.TemporaryFile:
    tf = tempfile.TemporaryFile(mode='r+b', prefix='__', suffix='.tmp')
    with open(src, 'r+b') as f:
        shutil.copyfileobj(f, tf)
    tf.seek(0)
    return tf


def delete_folder(path: Path, only_content: bool = False):
    if not path.is_dir():
        return

    for sub in path.iterdir():
        if sub.is_dir():
            delete_folder(sub)
        else:
            sub.unlink()

    if not only_content:
        path.rmdir()


@click.command()
@click.option("--directory", help="Path to the directory with files", type=click.Path(exists=True, file_okay=False),
              required=True)
@click.pass_context
def main(ctx, directory: Path):
    f"""{__doc__}"""
    directory = Path(directory).resolve()

    if not (directory / 'vgi').exists():
        sys.stderr.write(f'Directory {str(directory / "vgi")} does not exist!\n')

    if not ((directory / 'fpu').exists() or (directory / 'dbf').exists()):
        sys.stderr.write(f'Non of directory {str(directory / "fpu")} {str(directory / "fpu")} does not exist!\n')

    # clean directories
    for d in ('sql', 'sql_p', 'sql_g', 'shp', 'dgn', 'log'):
        delete_folder(directory / d)
        (directory / d).mkdir(parents=True)

    # clean FPU files
    print('* Konverze FPU do SQL ...')
    for f in (directory / 'fpu').glob('*.FPU'):
        print(f'* Cisteni FPU "{str(f)}" ...')
        cleared_lines = vycisti_fuvi(f)

        print(f'* Konverze FPU do SQL "{str(f)}" ...')
        result = import_fuvi(cleared_lines)

        with open(directory / 'sql_p' / f'{f.stem}.sql', 'w') as f_sql:
            for line in result:
                f_sql.write(f'{line}\n')


def start():
    main(obj={})


if __name__ == "__main__":
    start()
