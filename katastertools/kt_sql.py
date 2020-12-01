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
from katastertools.kt_vgi2shp import KNOWN_LAYERS, process_files


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


def process_descriptive_files(directory: Path):
    # clean FPU files
    print('* Converting FPU into SQL...')
    for f in (directory / 'fpu').glob('*.FPU'):
        print(f'* Cleaning FPU "{str(f)}"...')
        cleared_lines = vycisti_fuvi(f)

        print(f'* Converting FPU into SQL "{str(f)}"...')
        result = import_fuvi(cleared_lines)

        with open(directory / 'sql_p' / f'{f.stem}.sql', 'w') as f_sql:
            for line in result:
                f_sql.write(f'{line}\n')


def process_geometry_files(directory: Path, choices: dict, export_format: str):
    if export_format == 'sql':
        generate_sql(directory, choices)
    elif export_format == 'shp':
        generate_shp(directory, choices)


def generate_sql(directory: Path, choices: dict):
    choices['output_format'] = 'sql-copy'
    choices['output_directory'] = directory / 'sql_g'

    print('* Converting KN into SQL (KATUZ, KLADPAR, LINIE, POPIS, ZAPPAR, ZNACKY, ZUOB)...')
    choices['layers'] = {k: v[0] for k, v in KNOWN_LAYERS.items() if k in ('t', 'k', 'l', 'p', 'r', 'n', 'z',)}
    for f in (directory / 'vgi').rglob('KN*.vgi'):
        choices['file_path'] = f
        process_files(**choices)

    print("* Converting UO into SQL (UOV)...")
    choices['layers'] = {k: v[0] for k, v in KNOWN_LAYERS.items() if k in ('u',)}
    for f in (directory / 'vgi').rglob('UO*.vgi'):
        choices['file_path'] = f
        process_files(**choices)


def generate_shp(directory: Path, choices: dict):
    print("* Converting KN into SHP (all found layers)...")
    choices['output_format'] = 'shp'
    choices['output_directory'] = directory / 'shp'
    for f in (directory / 'vgi').rglob('KN*.vgi'):
        choices['file_path'] = f
        process_files(**choices)

    print("* Converting uo into SHP (all found layers)...")
    choices['output_format'] = 'shp'
    choices['output_directory'] = directory / 'shp'
    for f in (directory / 'vgi').rglob('UO*.vgi'):
        choices['file_path'] = f
        process_files(**choices)


@click.command()
@click.option("--directory", help="Path to the directory with files", type=click.Path(exists=True, file_okay=False),
              required=True)
@click.option("--export-format", help="Format for the exported files", type=str, default='sql', required=True)
@click.pass_context
def main(ctx, directory: Path, export_format: str):
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

    # Descriptive files
    process_descriptive_files(directory)

    # Geometry files
    choices = {
        'file_path': None,
        'layers': {},
        'output_directory': None,
        'output_format': None,
        'layer_config': '',
        'process_unknown_layers': False,
        'debug': False,
    }

    process_geometry_files(directory, choices, export_format)


def start():
    main(obj={})


if __name__ == "__main__":
    start()
