from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceConfig:
    code: str
    name: str
    page_url: str
    file_url: str
    keywords: tuple[str, ...]


SOURCES: tuple[SourceConfig, ...] = (
    SourceConfig(
        code="consumer_price_index",
        name="Динамика индекса потребительских цен на товары и услуги",
        page_url="https://77.rosstat.gov.ru/folder/64640",
        file_url=(
            "https://77.rosstat.gov.ru/storage/mediabank/"
            "Динамика индекса потребительских цен на товары и услуги "
            "в 2000-2026 гг(2).xlsx"
        ),
        keywords=("индекс", "потребительских", "цен", "динамика"),
    ),
    SourceConfig(
        code="population_income",
        name="Динамика денежных доходов населения г. Москвы",
        page_url="https://77.rosstat.gov.ru/folder/64641",
        file_url=(
            "https://77.rosstat.gov.ru/storage/mediabank/"
            "Динамика денежных доходов населения г. Москвы "
            "за 2014-2024 гг.(2).xlsx"
        ),
        keywords=("денежных", "доходов", "динамика"),
    ),
    SourceConfig(
        code="poverty_rate",
        name=(
            "Доля населения с доходами ниже прожиточного минимума "
            "и границы бедности"
        ),
        page_url="https://77.rosstat.gov.ru/folder/64641",
        file_url=(
            "https://77.rosstat.gov.ru/storage/mediabank/"
            "Доля населения с денежными доходами ниже прожиточного "
            "минимума и границы бедности за 2011-2025 гг..xlsx"
        ),
        keywords=("доля", "населения", "бедности"),
    ),
    SourceConfig(
        code="disease_incidence",
        name="Заболеваемость населения по основным классам болезней",
        page_url="https://77.rosstat.gov.ru/folder/64643",
        file_url=(
            "https://77.rosstat.gov.ru/storage/mediabank/"
            "Заболеваемость населения по основным классам болезней "
            "в 2020-2024 гг(1).xlsx"
        ),
        keywords=("заболеваемость", "классам", "болезней"),
    ),
    SourceConfig(
        code="medical_staff",
        name="Численность медицинских кадров",
        page_url="https://77.rosstat.gov.ru/folder/64643",
        file_url=(
            "https://77.rosstat.gov.ru/storage/mediabank/"
            "Численность медицинских кадров за 2020-2024 гг(1).xlsx"
        ),
        keywords=("численность", "медицинских", "кадров"),
    ),
)


SOURCES_BY_CODE: dict[str, SourceConfig] = {
    source.code: source for source in SOURCES
}
