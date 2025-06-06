import os
from pathlib import Path
import shutil
import subprocess
import zipfile


BASE_DIR = Path(__file__).parent.resolve()
SRC_DIR = BASE_DIR / 'src'
BUILD_DIR = BASE_DIR / 'build'

SCRAPER_LAMBDAS = ['cinema_scraper', 'session_scraper']


def package_scraper_lambdas():
    temp_dir = BASE_DIR / '.build_temp'
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    # packaging deps and shared modules separately from lambda handlers because they are shared across scrapers

    print('packaging scraper common')

    requirements = BASE_DIR / 'requirements.txt'
    subprocess.run(
        [
            'pip',
            'install',
            '-r',
            str(requirements),
            '-t',
            str(temp_dir),
            '--platform',
            'manylinux2014_x86_64',
            '--only-binary=:all:',
        ],
        check=True,
    )

    for item in os.listdir(SRC_DIR):
        if item not in SCRAPER_LAMBDAS:
            src = os.path.join(SRC_DIR, item)
            if os.path.isdir(src):
                dest = os.path.join(temp_dir, item)
                shutil.copytree(src, dest, ignore=shutil.ignore_patterns('__pycache__'))
            else:
                shutil.copy(src, temp_dir)

    # packaging individual scraper lambdas

    for _lambda in SCRAPER_LAMBDAS:
        clear_scraper_modules(temp_dir)

        print(f'packaging {_lambda}')

        lambda_src = SRC_DIR / _lambda
        shutil.copytree(
            lambda_src,
            temp_dir / _lambda,
            ignore=shutil.ignore_patterns('__pycache__', 'handler.py'),
        )
        shutil.copy(lambda_src / 'handler.py', temp_dir / 'handler.py')

        BUILD_DIR.mkdir(exist_ok=True)
        zip_path = BUILD_DIR / f'{_lambda}.zip'
        zip_directory(temp_dir, zip_path)
        print(f'created {zip_path}')

    shutil.rmtree(temp_dir)


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


if __name__ == '__main__':
    main()
