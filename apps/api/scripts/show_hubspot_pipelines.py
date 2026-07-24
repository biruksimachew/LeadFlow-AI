import asyncio

from app.providers.crm.factory import (
    build_crm_provider,
)


async def main() -> None:

    provider = build_crm_provider()

    try:

        pipelines = await provider.get_deal_pipelines()

        for pipeline in pipelines:

            print()
            print(
                "PIPELINE:",
                pipeline.get("label"),
                "| ID:",
                pipeline.get("id"),
            )

            for stage in pipeline.get(
                "stages",
                [],
            ):
                print(
                    "   STAGE:",
                    stage.get("label"),
                    "| ID:",
                    stage.get("id"),
                    "| CLOSED:",
                    stage.get(
                        "metadata",
                        {},
                    ).get("isClosed"),
                )

    finally:

        if hasattr(provider, "close"):
            await provider.close()


if __name__ == "__main__":
    asyncio.run(main())