from mosstat_api.downloader.discovery import (
    SourceDiscoveryError,
    discover_source_files,
)
from mosstat_api.sources import SOURCES


def main() -> None:
    print(f"Загружено конфигураций: {len(SOURCES)}")

    for source in SOURCES:
        print(f"\n=== {source.name} ===")
        print(f"Страница: {source.page_url}")

        try:
            candidates = discover_source_files(source)
        except SourceDiscoveryError as error:
            print(f"Ошибка: {error}")
            continue

        print(f"Найдено файлов: {len(candidates)}")

        if not candidates:
            print("Файлы XLS/XLSX/CSV/ODS не найдены")
            continue

        for candidate in candidates[:10]:
            print(f"[{candidate.score}] {candidate.title}")
            print(f"    {candidate.url}")


if __name__ == "__main__":
    main()
