import asyncio

from app.providers.crm.factory import build_crm_provider


async def main() -> None:
    provider = build_crm_provider()

    try:
        owners = await provider.list_owners()

        for owner in owners:
            print(
                f"ID: {owner.id} | "
                f"{owner.first_name or ''} "
                f"{owner.last_name or ''} | "
                f"{owner.email or ''}"
            )
    finally:
        if hasattr(provider, "close"):
            await provider.close()


if __name__ == "__main__":
    asyncio.run(main())