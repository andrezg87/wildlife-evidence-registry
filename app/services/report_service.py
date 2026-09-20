import asyncio
from collections import Counter
from decimal import Decimal
from io import BytesIO
from uuid import uuid4

from app.repositories import (
    currency_repository,
    gemini_repository,
    pdf_repository,
    report_repository,
    storage_repository,
)

LANGUAGE_NAMES = {"zh": "Mandarin Chinese", "ja": "Japanese", "vi": "Vietnamese"}


async def _compute_monthly_aggregates(year: int, month: int) -> dict:
    evidence_rows = await report_repository.list_evidence_for_month(year, month)
    nationalities = await report_repository.list_suspect_nationalities_for_month(year, month)

    total_seizures = len({row["case_id"] for row in evidence_rows})

    potential_loss_usd = sum(
        (row["quantity"] * row["reference_value_usd"] for row in evidence_rows),
        Decimal("0"),
    )
    potential_loss_sgd = await currency_repository.convert(
        "USD", "SGD", float(potential_loss_usd)
    )

    species_totals: dict[str, Decimal] = {}
    for row in evidence_rows:
        value = row["quantity"] * row["reference_value_usd"]
        species_totals[row["common_name"]] = species_totals.get(row["common_name"], Decimal("0")) + value
    most_affected_species = max(species_totals, key=species_totals.get) if species_totals else None

    nationality_counts = Counter(nationalities)
    top_trafficker_nationality = (
        nationality_counts.most_common(1)[0][0] if nationality_counts else None
    )

    return {
        "total_seizures": total_seizures,
        "potential_loss_usd": potential_loss_usd,
        "potential_loss_sgd": Decimal(str(potential_loss_sgd)),
        "most_affected_species": most_affected_species,
        "top_trafficker_nationality": top_trafficker_nationality,
    }


def _build_prompt(aggregates: dict, month: int, year: int, language: str) -> str:
    top_nationality = aggregates["top_trafficker_nationality"] or "not applicable (no suspects this month)"
    most_affected_species = aggregates["most_affected_species"] or "not applicable (no seizures this month)"
    return (
        f"Write a short professional monthly summary in {LANGUAGE_NAMES[language]} for a "
        f"wildlife forensics lab report, covering {month:02d}/{year}. "
        "Use exactly these figures - do not calculate, estimate, or invent any numbers "
        "yourself, only narrate what is given:\n"
        f"- Total seizures this month: {aggregates['total_seizures']}\n"
        f"- Most common trafficker nationality: {top_nationality}\n"
        f"- Potential loss avoided: USD {aggregates['potential_loss_usd']:.2f} "
        f"(SGD {aggregates['potential_loss_sgd']:.2f})\n"
        f"- Species most affected this month: {most_affected_species}\n"
        "Write 3-4 sentences, professional tone, addressed to a regional wildlife "
        f"trafficking authority. Write only in {LANGUAGE_NAMES[language]}. "
        "Output plain text only, no titles or markdown."
    )


async def _build_translation(report_id: str, aggregates: dict, month: int, year: int, language: str) -> dict:
    prompt = _build_prompt(aggregates, month, year, language)
    narrative_text = await gemini_repository.generate_text(prompt)

    pdf_bytes = await asyncio.to_thread(
        pdf_repository.render_report_pdf, narrative_text, language, month, year
    )
    key = f"reports/{report_id}/{language}_{uuid4()}.pdf"
    pdf_key = await asyncio.to_thread(storage_repository.upload_file, key, BytesIO(pdf_bytes))

    return await report_repository.add_translation(report_id, language, narrative_text, pdf_key)


async def generate_monthly_report(year: int, month: int) -> dict:
    report = await report_repository.get_report_by_month(year, month)

    if report is None:
        aggregates = await _compute_monthly_aggregates(year, month)
        report = await report_repository.create_report(
            month=month,
            year=year,
            total_seizures=aggregates["total_seizures"],
            potential_loss_usd=aggregates["potential_loss_usd"],
            potential_loss_sgd=aggregates["potential_loss_sgd"],
            most_affected_species=aggregates["most_affected_species"],
            top_trafficker_nationality=aggregates["top_trafficker_nationality"],
        )
    else:
        aggregates = {
            "total_seizures": report["total_seizures"],
            "potential_loss_usd": report["potential_loss_usd"],
            "potential_loss_sgd": report["potential_loss_sgd"],
            "most_affected_species": report["most_affected_species"],
            "top_trafficker_nationality": report["top_trafficker_nationality"],
        }

    existing_languages = {
        translation["language"]
        for translation in await report_repository.list_translations(str(report["id"]))
    }

    for language in LANGUAGE_NAMES:
        if language not in existing_languages:
            await _build_translation(str(report["id"]), aggregates, month, year, language)

    return report


async def get_report(report_id: str) -> dict | None:
    return await report_repository.get_report_by_id(report_id)


async def list_reports() -> list[dict]:
    return await report_repository.list_reports()


async def list_translations(report_id: str) -> list[dict]:
    translations = await report_repository.list_translations(report_id)
    resolved = []
    for translation in translations:
        pdf_key = translation.pop("pdf_key")
        pdf_url = storage_repository.get_presigned_url(pdf_key) if pdf_key else None
        resolved.append({**translation, "pdf_url": pdf_url})
    return resolved


async def approve_report(report_id: str, approved_by_user_id: str) -> dict | None:
    return await report_repository.approve_report(report_id, approved_by_user_id)
