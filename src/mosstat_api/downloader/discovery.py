from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from mosstat_api.sources import SourceConfig


ALLOWED_SUFFIXES = {".xls", ".xlsx", ".csv", ".ods"}


class SourceDiscoveryError(RuntimeError):
    """Не удалось получить или разобрать страницу источника."""


@dataclass(frozen=True, slots=True)
class FileCandidate:
    title: str
    url: str
    score: int


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


def _is_data_file(url: str) -> bool:
    path = PurePosixPath(urlparse(url).path)
    return path.suffix.casefold() in ALLOWED_SUFFIXES


def _score_candidate(title: str, url: str, keywords: tuple[str, ...]) -> int:
    searchable_text = _normalize_text(f"{title} {url}")
    return sum(
        1
        for keyword in keywords
        if _normalize_text(keyword) in searchable_text
    )


def extract_file_candidates(
    html: str,
    page_url: str,
    keywords: tuple[str, ...],
) -> list[FileCandidate]:
    soup = BeautifulSoup(html, "lxml")
    candidates: list[FileCandidate] = []
    seen_urls: set[str] = set()

    for link in soup.select("a[href]"):
        href = link.get("href")
        if not isinstance(href, str):
            continue

        absolute_url = urljoin(page_url, href)
        if absolute_url in seen_urls or not _is_data_file(absolute_url):
            continue

        seen_urls.add(absolute_url)
        title = " ".join(link.stripped_strings) or PurePosixPath(
            urlparse(absolute_url).path
        ).name
        score = _score_candidate(title, absolute_url, keywords)

        candidates.append(
            FileCandidate(
                title=title,
                url=absolute_url,
                score=score,
            )
        )

    return sorted(
        candidates,
        key=lambda candidate: (-candidate.score, candidate.title.casefold()),
    )


def discover_source_files(source: SourceConfig) -> list[FileCandidate]:
    try:
        response = httpx.get(
            source.page_url,
            follow_redirects=True,
            timeout=30.0,
            # Сервер Мосстата не отдает полную цепочку сертификатов.
            # Отключение проверки допустимо только для публичных страниц
            # из фиксированного списка SOURCES и не должно применяться
            # к произвольным пользовательским URL.
            verify=False,
            headers={
                "User-Agent": "mosstat-mvp/0.1 educational-project",
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise SourceDiscoveryError(
            f"Не удалось загрузить страницу {source.page_url}: {error}"
        ) from error

    return extract_file_candidates(
        html=response.text,
        page_url=source.page_url,
        keywords=source.keywords,
    )
