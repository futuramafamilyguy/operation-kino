import os
from pathlib import Path
import shutil
import subprocess
import zipfile


BASE_DIR = Path(__file__).parent.resolve()
SRC_DIR = BASE_DIR / 'src'
BUILD_DIR = BASE_DIR / 'build'

SCRAPER_LAMBDAS = ['scrape_cinemas', 'scrape_sessions']


def package_scraper_lambdas():
    temp_dir = BASE_DIR / '.build_temp'
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    # packaging deps and shared modules separately from lambda handlers because they are shared across scrapers

    print('packaging scraper common')

    requirements = BASE_DIR / 'requirements.txt'
    install_dependencies(requirements, temp_dir)

    to_copy = [
        (SRC_DIR / 'common', temp_dir / 'common'),
        (SRC_DIR / 'models', temp_dir / 'models'),
        (SRC_DIR / 'repositories', temp_dir / 'repositories'),
        (SRC_DIR / 'exceptions.py', temp_dir / 'exceptions.py'),
    ]
    for src, dest in to_copy:
        if os.path.isdir(src):
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns('__pycache__'))
        else:
            shutil.copy(src, temp_dir)

    # packaging individual scraper lambdas

    for _lambda in SCRAPER_LAMBDAS:
        clear_scraper_modules(temp_dir)

        print(f'packaging {_lambda}')

        lambda_src = SRC_DIR / _lambda
        lambda_dest = temp_dir / _lambda
        lambda_dest.mkdir(parents=True)
        shutil.copy(lambda_src / 'scraper.py', lambda_dest / 'scraper.py')
        shutil.copy(lambda_src / 'handler.py', temp_dir / 'handler.py')

        BUILD_DIR.mkdir(exist_ok=True)
        zip_path = BUILD_DIR / f'{_lambda}.zip'
        zip_directory(temp_dir, zip_path)
        print(f'created {zip_path}')

    shutil.rmtree(temp_dir)


def package_get_sessions_lambda():
    _lambda = 'get_sessions'
    temp_dir = BASE_DIR / '.build_temp'
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    print(f'installing dependencies for {_lambda}')

    requirements = SRC_DIR / _lambda / 'requirements.txt'
    install_dependencies(requirements, temp_dir)

    print(f'packaging {_lambda}')

    files_to_copy = [
        (
            SRC_DIR / 'repositories' / 'movie_repository.py',
            temp_dir / 'repositories' / 'movie_repository.py',
        ),
        (SRC_DIR / 'models' / 'movie.py', temp_dir / 'models' / 'movie.py'),
        (SRC_DIR / 'models' / 'cinema.py', temp_dir / 'models' / 'cinema.py'),
    ]
    for src, dest in files_to_copy:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)

    lambda_src = SRC_DIR / _lambda
    shutil.copy(lambda_src / 'handler.py', temp_dir / 'handler.py')
    BUILD_DIR.mkdir(exist_ok=True)
    zip_path = BUILD_DIR / f'{_lambda}.zip'
    zip_directory(temp_dir, zip_path)

    print(f'created {zip_path}')

    shutil.rmtree(temp_dir)


def install_dependencies(requirements: str, dest: str):
    subprocess.run(
        [
            'pip',
            'install',
            '-r',
            str(requirements),
            '-t',
            str(dest),
            '--platform',
            'manylinux2014_x86_64',
            '--only-binary=:all:',
        ],
        check=True,
    )


def zip_directory(source_dir: Path, zip_path: Path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(source_dir)
                zf.write(file_path, arcname)


def clear_scraper_modules(temp_dir):
    for _lambda in SCRAPER_LAMBDAS:
        lambda_path = Path(temp_dir / _lambda)
        if lambda_path.exists() and lambda_path.is_dir():
            shutil.rmtree(lambda_path)


def main():
    package_scraper_lambdas()
    package_get_sessions_lambda()


if __name__ == '__main__':
    main()
