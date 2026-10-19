from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

import requests


class BAJobsucheUnavailable(RuntimeError):
    """Raised when the optional BA Jobsuche backend cannot be used."""


class BAJobsucheClient:
    """Small client for the BA Jobsuche backend used by the public job search.

    This backend is publicly reachable but is not treated here as a guaranteed
    long-term developer API. The fixture dataset remains the stable fallback.
    """

    BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
    API_KEY = "jobboerse-jobsuche"

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self._session = session or requests.Session()
        self._timeout = timeout_seconds
        self._session.headers.update(
            {
                "X-API-Key": self.API_KEY,
                "Accept": "application/json",
                "User-Agent": "Jobsuche/2.9.2",
            }
        )

    def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = self._session.get(
                f"{self.BASE_URL}{path}",
                params=params,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            response_obj = locals().get("response") or getattr(exc, "response", None)
            status_code = getattr(response_obj, "status_code", None)
            status_text = f"HTTP {status_code}" if status_code is not None else "network error"
            raise BAJobsucheUnavailable(
                "BA Jobsuche is currently unavailable "
                f"({status_text}). This project treats that live source as optional; "
                "use the local fixture dataset as the stable fallback."
            ) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise BAJobsucheUnavailable(
                "BA Jobsuche returned a non-JSON response. Use the local fixture "
                "dataset as the stable fallback."
            ) from exc

    def search_jobs(
        self,
        query: str,
        location: str | None = None,
        *,
        page: int = 1,
        size: int = 25,
        radius_km: int | None = None,
    ) -> list[dict[str, Any]]:
        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= size <= 100:
            raise ValueError("size must be between 1 and 100")

        params: dict[str, Any] = {
            "angebotsart": 1,
            "pav": "false",
            "was": query,
            "page": page,
            "size": size,
        }
        if location:
            params["wo"] = location
        if radius_km is not None:
            params["umkreis"] = radius_km

        payload = self._get_json("/pc/v4/app/jobs", params=params)
        offers = payload.get("stellenangebote", [])
        if not isinstance(offers, list):
            raise ValueError("Unexpected BA Jobsuche response: 'stellenangebote' is not a list")
        return offers

    def get_job_details(self, reference_number: str) -> dict[str, Any]:
        encoded = base64.b64encode(reference_number.encode("utf-8")).decode("ascii")
        encoded_path = quote(encoded, safe="")
        payload = self._get_json(f"/pc/v4/jobdetails/{encoded_path}")
        if not isinstance(payload, dict):
            raise ValueError("Unexpected BA job-details response")
        return payload

    @staticmethod
    def reference_number(search_hit: dict[str, Any]) -> str | None:
        value = search_hit.get("referenznummer") or search_hit.get("refnr")
        return str(value) if value else None

    @staticmethod
    def details_to_raw_text(details: dict[str, Any]) -> str:
        title = details.get("stellenangebotsTitel") or details.get("titel") or ""
        description = details.get("stellenangebotsBeschreibung") or details.get("beschreibung") or ""
        location = details.get("arbeitsorte") or details.get("arbeitsort") or ""
        return f"{title}\n\n{description}\n\nLocation: {location}".strip()
