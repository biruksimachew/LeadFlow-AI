import asyncio

from app.providers.crm.factory import build_crm_provider


async def main() -> None:

    provider = build_crm_provider()

    try:

        print("Provisioning HubSpot properties...")

        await provider.ensure_properties()

        print("HubSpot properties are ready.")

    finally:

        if hasattr(provider, "close"):
            await provider.close()


if __name__ == "__main__":
    asyncio.run(main())