from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
import time
from urllib.parse import unquote, urlparse

import httpx

from mosstat_api.sources import SourceConfig


ALLOWED_HOSTS = {"77.rosstat.gov.ru"}
CHUNK_SIZE = 64 * 1024
MAX_DOWNLOAD_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2.0
DOWNLOAD_TIMEOUT = httpx.Timeout(
    connect=30.0,
    read=180.0,
    write=30.0,
    pool=30.0,
)


class DownloadError(RuntimeError):
    """Не удалось безопасно скачать или сохранить исходный файл."""


@dataclass(frozen=True, slots=True)
class DownloadResult:
    dataset_code: str
    source_url: str
    path: str
    sha256: str
    size_bytes: int
    downloaded_at: str
    reused: bool


def _validate_source_url(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise DownloadError("Разрешены только HTTPS-ссылки")

    if parsed.hostname not in ALLOWED_HOSTS:
        raise DownloadError(f"Недопустимый домен источника: {parsed.hostname}")


def _safe_filename(url: str) -> str:
    original_name = Path(unquote(urlparse(url).path)).name
    cleaned_name = re.sub(r"[^0-9A-Za-zА-Яа-яЁё._() -]+", "_", original_name)
    cleaned_name = cleaned_name.strip(" .")

    if not cleaned_name:
        return "source.xlsx"

    return cleaned_name


def _write_metadata(result: DownloadResult, metadata_path: Path) -> None:
    temporary_path = metadata_path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(metadata_path)


def _download_to_temporary_file(
    source: SourceConfig,
    destination_dir: Path,
) -> tuple[Path, str, int]:
    last_error: httpx.HTTPError | None = None

    for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
        temporary_file: Path | None = None

        try:
            with httpx.stream(
                "GET",
                source.file_url,
                follow_redirects=True,
                timeout=DOWNLOAD_TIMEOUT,
                verify=False,
                headers={
                    "User-Agent": "mosstat-mvp/0.1 educational-project",
                },
            ) as response:
                response.raise_for_status()

                content_type = response.headers.get(
                    "content-type",
                    "",
                ).casefold()
                if "text/html" in content_type:
                    raise DownloadError(
                        "Вместо файла получена HTML-страница: "
                        f"{source.file_url}"
                    )

                digest = sha256()
                size_bytes = 0

                with NamedTemporaryFile(
                    mode="wb",
                    dir=destination_dir,
                    prefix=".download-",
                    suffix=".tmp",
                    delete=False,
                ) as file_object:
                    temporary_file = Path(file_object.name)

                    for chunk in response.iter_bytes(CHUNK_SIZE):
                        if not chunk:
                            continue

                        digest.update(chunk)
                        size_bytes += len(chunk)
                        file_object.write(chunk)

            if size_bytes == 0:
                raise DownloadError(
                    f"Получен пустой файл: {source.file_url}"
                )

            return temporary_file, digest.hexdigest(), size_bytes

        except httpx.HTTPError as error:
            last_error = error

            if temporary_file is not None and temporary_file.exists():
                temporary_file.unlink()

            if attempt < MAX_DOWNLOAD_ATTEMPTS:
                delay = RETRY_DELAY_SECONDS * attempt
                print(
                    f"Попытка {attempt} не удалась: {error}. "
                    f"Повтор через {delay:.0f} сек."
                )
                time.sleep(delay)

        except OSError:
            if temporary_file is not None and temporary_file.exists():
                temporary_file.unlink()
            raise

    raise DownloadError(
        f"Не удалось скачать {source.file_url} после "
        f"{MAX_DOWNLOAD_ATTEMPTS} попыток: {last_error}"
    )


def download_source(
    source: SourceConfig,
    raw_data_dir: Path,
) -> DownloadResult:
    _validate_source_url(source.file_url)

    downloaded_at = datetime.now(UTC)
    destination_dir = (
        raw_data_dir
        / source.code
        / downloaded_at.strftime("%Y-%m-%d")
    )
    destination_dir.mkdir(parents=True, exist_ok=True)

    temporary_file: Path | None = None

    try:
        temporary_file, checksum, size_bytes = _download_to_temporary_file(
            source=source,
            destination_dir=destination_dir,
        )

        safe_name = _safe_filename(source.file_url)
        destination_path = destination_dir / f"{checksum[:12]}-{safe_name}"
        metadata_path = destination_path.with_suffix(
            destination_path.suffix + ".json"
        )

        reused = destination_path.exists()
        if reused:
            temporary_file.unlink()
        else:
            temporary_file.replace(destination_path)

        result = DownloadResult(
            dataset_code=source.code,
            source_url=source.file_url,
            path=str(destination_path),
            sha256=checksum,
            size_bytes=size_bytes,
            downloaded_at=downloaded_at.isoformat(),
            reused=reused,
        )
        _write_metadata(result, metadata_path)
        return result

    except DownloadError:
        raise
    except OSError as error:
        raise DownloadError(
            f"Не удалось сохранить файл {source.file_url}: {error}"
        ) from error
    finally:
        if temporary_file is not None and temporary_file.exists():
            temporary_file.unlink()
