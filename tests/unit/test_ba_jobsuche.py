import base64
from urllib.parse import quote

import pytest
import requests

from src.data_sources.ba_jobsuche import BAJobsucheClient, BAJobsucheUnavailable


class FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self) -> None:
        self.headers = {}
        self.calls = []
        self.responses = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def test_search_jobs_builds_expected_request() -> None:
    session = FakeSession()
    session.responses.append(FakeResponse({"stellenangebote": [{"referenznummer": "ABC"}]}))
    client = BAJobsucheClient(session=session, timeout_seconds=5)  # type: ignore[arg-type]

    results = client.search_jobs("AI Engineer", "Berlin", size=10)

    assert results == [{"referenznummer": "ABC"}]
    assert session.headers["X-API-Key"] == "jobboerse-jobsuche"
    url, kwargs = session.calls[0]
    assert url.endswith("/pc/v4/app/jobs")
    assert kwargs["params"]["was"] == "AI Engineer"
    assert kwargs["params"]["wo"] == "Berlin"
    assert kwargs["params"]["size"] == 10
    assert kwargs["params"]["angebotsart"] == 1
    assert kwargs["params"]["pav"] == "false"


def test_get_job_details_base64_encodes_reference() -> None:
    session = FakeSession()
    session.responses.append(FakeResponse({"stellenangebotsTitel": "AI Engineer"}))
    client = BAJobsucheClient(session=session)  # type: ignore[arg-type]

    client.get_job_details("10001-123-S")

    expected = quote(base64.b64encode(b"10001-123-S").decode("ascii"), safe="")
    assert session.calls[0][0].endswith(f"/pc/v4/jobdetails/{expected}")


def test_search_jobs_wraps_http_errors_as_optional_source_failure() -> None:
    session = FakeSession()
    session.responses.append(FakeResponse({}, status_code=403))
    client = BAJobsucheClient(session=session)  # type: ignore[arg-type]

    with pytest.raises(BAJobsucheUnavailable, match="HTTP 403"):
        client.search_jobs("Softwareentwickler", "Berlin", size=10)
