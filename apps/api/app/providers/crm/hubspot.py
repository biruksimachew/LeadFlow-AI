import httpx

from app.config import settings
from app.providers.crm.base import (
    CRMContactMatch,
    CRMContactResult,
    CRMDealResult,
    CRMOwner,
    CRMProviderError,
)

CONTACT_PROPERTIES = [
    {
        "groupName": "contactinformation",
        "name": "leadflow_phone_e164",
        "label": "LeadFlow Phone E164",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": True,
    },
    {
        "groupName": "contactinformation",
        "name": "leadflow_score",
        "label": "LeadFlow Score",
        "type": "number",
        "fieldType": "number",
        "hasUniqueValue": False,
    },
    {
        "groupName": "contactinformation",
        "name": "leadflow_source",
        "label": "LeadFlow Source",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
    {
        "groupName": "contactinformation",
        "name": "leadflow_service_type",
        "label": "LeadFlow Service Type",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
    {
        "groupName": "contactinformation",
        "name": "leadflow_urgency",
        "label": "LeadFlow Urgency",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
    {
        "groupName": "contactinformation",
        "name": "leadflow_service_zone",
        "label": "LeadFlow Service Zone",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
    {
        "groupName": "contactinformation",
        "name": "leadflow_automation_status",
        "label": "LeadFlow Automation Status",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
    {
        "groupName": "contactinformation",
        "name": "leadflow_correlation_id",
        "label": "LeadFlow Correlation ID",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
]


DEAL_PROPERTIES = [
    {
        "groupName": "dealinformation",
        "name": "leadflow_lead_id",
        "label": "LeadFlow Lead ID",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": True,
    },
    {
        "groupName": "dealinformation",
        "name": "leadflow_score",
        "label": "LeadFlow Score",
        "type": "number",
        "fieldType": "number",
        "hasUniqueValue": False,
    },
    {
        "groupName": "dealinformation",
        "name": "leadflow_source",
        "label": "LeadFlow Source",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
    {
        "groupName": "dealinformation",
        "name": "leadflow_service_type",
        "label": "LeadFlow Service Type",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
    {
        "groupName": "dealinformation",
        "name": "leadflow_urgency",
        "label": "LeadFlow Urgency",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
    {
        "groupName": "dealinformation",
        "name": "leadflow_automation_status",
        "label": "LeadFlow Automation Status",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
    {
        "groupName": "dealinformation",
        "name": "leadflow_correlation_id",
        "label": "LeadFlow Correlation ID",
        "type": "string",
        "fieldType": "text",
        "hasUniqueValue": False,
    },
]
class HubSpotProvider:

    def __init__(self):

        if not settings.hubspot_access_token:
            raise CRMProviderError(
                "HUBSPOT_NOT_CONFIGURED",
                "HUBSPOT_ACCESS_TOKEN is not configured.",
            )

        self.base_url = (
            settings.hubspot_api_base_url.rstrip("/")
        )

        self.api_version = (
            settings.hubspot_api_version
        )

        self.client = httpx.AsyncClient(
            timeout=settings.hubspot_timeout_seconds,
            headers={
                "Authorization": (
                    f"Bearer "
                    f"{settings.hubspot_access_token}"
                ),
                "Content-Type": "application/json",
            },
        )

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> dict:

        try:

            response = await self.client.request(
                method,
                f"{self.base_url}{path}",
                **kwargs,
            )

        except httpx.TimeoutException as exc:

            raise CRMProviderError(
                "HUBSPOT_TIMEOUT",
                "HubSpot request timed out.",
                retryable=True,
            ) from exc

        except httpx.RequestError as exc:

            raise CRMProviderError(
                "HUBSPOT_NETWORK_ERROR",
                str(exc),
                retryable=True,
            ) from exc

        if response.status_code == 429:

            raise CRMProviderError(
                "HUBSPOT_RATE_LIMIT",
                "HubSpot rate limit reached.",
                retryable=True,
                status_code=429,
            )

        if response.status_code >= 500:

            raise CRMProviderError(
                "HUBSPOT_SERVER_ERROR",
                (
                    f"HubSpot returned "
                    f"{response.status_code}."
                ),
                retryable=True,
                status_code=response.status_code,
            )

        if response.status_code == 404:
            raise CRMProviderError(
                "HUBSPOT_NOT_FOUND",
                "HubSpot record or property was not found.",
                retryable=False,
                status_code=404,
            )

        if response.status_code >= 400:

            raise CRMProviderError(
                "HUBSPOT_API_ERROR",
                (
                    f"HubSpot returned "
                    f"{response.status_code}: "
                    f"{response.text[:500]}"
                ),
                retryable=False,
                status_code=response.status_code,
            )

        if not response.content:
            return {}

        return response.json()


    async def list_owners(
        self,
    ) -> list[CRMOwner]:

        payload = await self._request(
            "GET",
            (
                f"/crm/owners/"
                f"{self.api_version}"
                "?limit=100"
            ),
        )

        owners: list[CRMOwner] = []

        for item in payload.get(
            "results",
            []
        ):

            if item.get("archived"):
                continue

            owners.append(
                CRMOwner(
                    id=str(item["id"]),
                    email=item.get("email"),
                    first_name=item.get(
                        "firstName"
                    ),
                    last_name=item.get(
                        "lastName"
                    ),
                )
            )

        return owners


    async def health_check(
        self,
    ) -> bool:

        owners = await self.list_owners()

        return isinstance(
            owners,
            list,
        )


    async def _property_exists(
        self,
        object_type: str,
        property_name: str,
    ) -> bool:

        try:
            await self._request(
                "GET",
                (
                    f"/crm/properties/"
                    f"{self.api_version}/"
                    f"{object_type}/"
                    f"{property_name}"
                ),
            )

            return True

        except CRMProviderError as exc:

            if exc.status_code == 404:
                return False

            raise


    async def _ensure_property(
        self,
        object_type: str,
        definition: dict,
    ) -> None:

        exists = await self._property_exists(
            object_type,
            definition["name"],
        )

        if exists:
            return

        await self._request(
            "POST",
            (
                f"/crm/properties/"
                f"{self.api_version}/"
                f"{object_type}"
            ),
            json=definition,
        )


    async def ensure_properties(self) -> None:

        for definition in CONTACT_PROPERTIES:

            await self._ensure_property(
                "contacts",
                definition,
            )

        for definition in DEAL_PROPERTIES:

            await self._ensure_property(
                "deals",
                definition,
            )




    async def _batch_read_contact(
        self,
        *,
        id_property: str,
        value: str,
    ) -> dict | None:

        try:

            payload = await self._request(
                "POST",
                (
                    f"/crm/objects/"
                    f"{self.api_version}/"
                    f"contacts/batch/read"
                ),
                json={
                    "idProperty": id_property,
                    "properties": [
                        "email",
                        "phone",
                        "leadflow_phone_e164",
                    ],
                    "inputs": [
                        {
                            "id": value,
                        }
                    ],
                },
            )

        except CRMProviderError as exc:

            if exc.status_code == 404:
                return None

            raise

        results = payload.get(
            "results",
            [],
        )

        if not results:
            return None

        return results[0]


    async def find_contact(
        self,
        *,
        email: str | None,
        phone_e164: str | None,
    ) -> CRMContactMatch | None:

        email_contact = None
        phone_contact = None

        if email:

            email_contact = await self._batch_read_contact(
                id_property="email",
                value=email,
            )

        if phone_e164:

            phone_contact = await self._batch_read_contact(
                id_property="leadflow_phone_e164",
                value=phone_e164,
            )

        if (
            email_contact is not None
            and phone_contact is not None
            and email_contact["id"] != phone_contact["id"]
        ):
            raise CRMProviderError(
                "HUBSPOT_IDENTITY_CONFLICT",
                (
                    "Email and normalized phone match "
                    "different HubSpot contacts."
                ),
                retryable=False,
            )

        if email_contact is not None:

            return CRMContactMatch(
                contact_id=str(
                    email_contact["id"]
                ),
                matched_by="email",
            )

        if phone_contact is not None:

            return CRMContactMatch(
                contact_id=str(
                    phone_contact["id"]
                ),
                matched_by="phone",
            )

        return None

    async def upsert_contact(
        self,
        *,
        email: str | None,
        phone_e164: str | None,
        properties: dict[str, str],
    ) -> CRMContactResult:

        existing = await self.find_contact(
            email=email,
            phone_e164=phone_e164,
        )

        if existing is not None:

            payload = await self._request(
                "PATCH",
                (
                    f"/crm/objects/"
                    f"{self.api_version}/"
                    f"contacts/"
                    f"{existing.contact_id}"
                ),
                json={
                    "properties": properties,
                },
            )

            return CRMContactResult(
                contact_id=str(
                    payload["id"]
                ),
                created=False,
            )

        identity_property = None
        identity_value = None

        if email:
            identity_property = "email"
            identity_value = email

        elif phone_e164:
            identity_property = (
                "leadflow_phone_e164"
            )
            identity_value = phone_e164

        else:
            raise CRMProviderError(
                "HUBSPOT_CONTACT_IDENTITY_MISSING",
                (
                    "Contact requires normalized "
                    "email or phone."
                ),
                retryable=False,
            )

        payload = await self._request(
            "POST",
            (
                f"/crm/objects/"
                f"{self.api_version}/"
                f"contacts/batch/upsert"
            ),
            json={
                "inputs": [
                    {
                        "id": identity_value,
                        "idProperty": identity_property,
                        "properties": properties,
                    }
                ]
            },
        )

        results = payload.get(
            "results",
            [],
        )

        if not results:
            raise CRMProviderError(
                "HUBSPOT_UPSERT_EMPTY_RESULT",
                "HubSpot contact upsert returned no result.",
                retryable=True,
            )

        result = results[0]

        return CRMContactResult(
            contact_id=str(result["id"]),
            created=bool(
                result.get("new", False)
            ),
        )


    async def get_deal_pipelines(
        self,
    ) -> list[dict]:

        payload = await self._request(
            "GET",
            (
                f"/crm/pipelines/"
                f"{self.api_version}/deals"
            ),
        )

        return payload.get("results", [])



    async def find_deal(
        self,
        *,
        leadflow_lead_id: str,
    ) -> CRMDealResult | None:

        try:

            payload = await self._request(
                "GET",
                (
                    f"/crm/objects/"
                    f"{self.api_version}/"
                    f"deals/"
                    f"{leadflow_lead_id}"
                    "?idProperty=leadflow_lead_id"
                ),
            )

        except CRMProviderError as exc:

            if exc.status_code == 404:
                return None

            raise

        return CRMDealResult(
            deal_id=str(payload["id"]),
            created=False,
        )


    async def upsert_deal(
        self,
        *,
        leadflow_lead_id: str,
        properties: dict[str, str],
    ) -> CRMDealResult:

        existing = await self.find_deal(
            leadflow_lead_id=leadflow_lead_id
        )

        if existing is not None:

            payload = await self._request(
                "PATCH",
                (
                    f"/crm/objects/"
                    f"{self.api_version}/"
                    f"deals/"
                    f"{leadflow_lead_id}"
                    "?idProperty=leadflow_lead_id"
                ),
                json={
                    "properties": properties,
                },
            )

            return CRMDealResult(
                deal_id=str(payload["id"]),
                created=False,
            )

        payload = await self._request(
            "POST",
            (
                f"/crm/objects/"
                f"{self.api_version}/deals"
            ),
            json={
                "properties": properties,
            },
        )

        return CRMDealResult(
            deal_id=str(payload["id"]),
            created=True,
        )


    async def associate_contact_with_deal(
        self,
        *,
        contact_id: str,
        deal_id: str,
    ) -> None:

        await self._request(
            "PUT",
            (
                f"/crm/objects/"
                f"{self.api_version}/"
                f"deal/{deal_id}/"
                f"associations/default/"
                f"contact/{contact_id}"
            ),
        )


    async def close(self) -> None:
        await self.client.aclose()




    