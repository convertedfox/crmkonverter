from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO

OUTPUT_COLUMNS = [
    "E-Mail Adresse",
    "Erstkontakt",
    "Anrede",
    "Hauptadresse PLZ",
    "Organisationname",
    "Nachname",
    "Vorname",
    "Matrikelnummer",
    "Studienrichtung",
    "Hauptadresse Stadt",
    "Kontakttyp",
    "Bemerkung",
    "DHBW-Newsletter",
]

REQUIRED_COLUMNS = [
    "email",
    "activated",
    "salutation",
    "zip",
    "company",
    "lastname",
    "firstname",
    "matrikelnummer",
    "studienrichtung",
    "vorname",
    "city",
    "nachname",
    "source",
]


class ConversionError(Exception):
    """Raised when uploaded CSV data cannot be converted safely."""


@dataclass(frozen=True)
class ConversionStats:
    row_count: int
    firstnames_filled_from_vorname: int
    lastnames_filled_from_nachname: int
    lastnames_filled_with_nn: int


@dataclass(frozen=True)
class ConversionResult:
    rows: list[dict[str, str]]
    csv_bytes: bytes
    stats: ConversionStats


def convert_csv_bytes(csv_bytes: bytes) -> ConversionResult:
    """Convert uploaded CAS prospect CSV bytes into CRM import CSV bytes."""
    text = _decode_csv_bytes(csv_bytes)
    return convert_csv_text(text)


def convert_csv_text(csv_text: str) -> ConversionResult:
    input_file = StringIO(csv_text)
    reader = csv.DictReader(input_file, delimiter=";")

    if reader.fieldnames is None:
        raise ConversionError("Die CSV-Datei enthält keine Kopfzeile.")

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in reader.fieldnames
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ConversionError(
            f"Die CSV-Datei enthält nicht alle Pflichtspalten: {missing}"
        )

    rows: list[dict[str, str]] = []
    firstnames_filled = 0
    lastnames_filled = 0
    lastnames_filled_with_nn = 0

    try:
        for row in reader:
            firstname = row["firstname"]
            if _is_blank(firstname) and not _is_blank(row["vorname"]):
                firstname = row["vorname"]
                firstnames_filled += 1

            lastname = row["lastname"]
            if _is_blank(lastname) and not _is_blank(row["nachname"]):
                lastname = row["nachname"]
                lastnames_filled += 1

            if _is_blank(lastname):
                lastname = "N.N."
                lastnames_filled_with_nn += 1

            rows.append(
                {
                    "E-Mail Adresse": row["email"],
                    "Erstkontakt": row["activated"],
                    "Anrede": row["salutation"],
                    "Hauptadresse PLZ": row["zip"],
                    "Organisationname": row["company"],
                    "Nachname": lastname,
                    "Vorname": firstname,
                    "Matrikelnummer": row["matrikelnummer"],
                    "Studienrichtung": row["studienrichtung"],
                    "Hauptadresse Stadt": row["city"],
                    "Kontakttyp": "Studieninteressent",
                    "Bemerkung": row["source"],
                    "DHBW-Newsletter": "ja",
                }
            )
    except csv.Error as error:
        raise ConversionError(
            f"Die CSV-Datei konnte nicht gelesen werden: {error}"
        ) from error

    return ConversionResult(
        rows=rows,
        csv_bytes=_rows_to_csv_bytes(rows),
        stats=ConversionStats(
            row_count=len(rows),
            firstnames_filled_from_vorname=firstnames_filled,
            lastnames_filled_from_nachname=lastnames_filled,
            lastnames_filled_with_nn=lastnames_filled_with_nn,
        ),
    )


def _decode_csv_bytes(csv_bytes: bytes) -> str:
    try:
        return csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ConversionError(
            "Die CSV-Datei muss als UTF-8 oder UTF-8 mit BOM gespeichert sein."
        ) from error


def _rows_to_csv_bytes(rows: list[dict[str, str]]) -> bytes:
    output_file = StringIO()
    writer = csv.DictWriter(
        output_file,
        fieldnames=OUTPUT_COLUMNS,
        delimiter=";",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output_file.getvalue().encode("utf-8-sig")


def _is_blank(value: str | None) -> bool:
    return value is None or not value.strip()
