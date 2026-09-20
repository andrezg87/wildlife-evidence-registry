import httpx

from app.config import settings


async def convert(from_currency: str, to_currency: str, amount: float) -> float:
    if amount == 0:
        return 0.0
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.currency_exchange_api_base_url}/convert",
            params={"from": from_currency, "to": to_currency, "amount": amount},
        )
        response.raise_for_status()
    return response.json()["converted_amount"]
