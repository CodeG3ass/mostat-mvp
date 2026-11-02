import argparse

from mosstat_api.config import settings
from mosstat_api.downloader.download import DownloadError, download_source
from mosstat_api.sources import SOURCES, SOURCES_BY_CODE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Скачать исходные XLSX-файлы Мосстата",
    )
    parser.add_argument(
        "dataset_code",
        nargs="?",
        choices=tuple(SOURCES_BY_CODE),
        help="Код одного набора; без аргумента скачиваются все наборы",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected_sources = (
        (SOURCES_BY_CODE[args.dataset_code],)
        if args.dataset_code
        else SOURCES
    )

    failed = False

    for source in selected_sources:
        print(f"\n=== {source.name} ===")

        try:
            result = download_source(source, settings.raw_data_dir)
        except DownloadError as error:
            failed = True
            print(f"Ошибка: {error}")
            continue

        action = "уже существовал" if result.reused else "скачан"
        print(f"Файл {action}: {result.path}")
        print(f"Размер: {result.size_bytes} байт")
        print(f"SHA-256: {result.sha256}")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
