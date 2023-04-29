from datetime import datetime

import pytest
from fastapi import status

from services.services import (
    blacklist_service,
    short_url_service,
    url_use_service,
)

from .factories import (
    BlacklistClientFactory,
    ShortenedURLFactory,
    ShortenedURLUseFactory,
    testing_session,
)

pytestmark = pytest.mark.anyio

BLACKLIST_LIST_URL = "/api/v1/blacklist"
BLACKLIST_DETAIL_URL = "/api/v1/blacklist/{id}"
PING_URL = "/api/v1/ping"
TEST_URL = "https://www.ya.ru"
SHORT_URL_LIST_URL = "/api/v1/"
SHORT_URL_DETAIL_URL = "/api/v1/{id}"
SHORT_URL_STATUS_URL = "/api/v1/{id}/status"
SHORT_URL_SHORTEN_URL = "/api/v1/shorten"


class TestBlacklistAPIs:
    @pytest.fixture
    async def create_blacklist(self, api_client):
        clients = [await BlacklistClientFactory() for _ in range(3)]
        return clients

    async def test_blacklist_middleware(self, api_client, mocker):
        mock_client = mocker.patch("fastapi.Request.client")
        mock_client.host = "198.51.255.42"

        response = await api_client.get(BLACKLIST_LIST_URL)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": "You`ve been temporary blacklisted"
        }

    async def test_show_blacklist(self, api_client, create_blacklist):
        response = await api_client.get(BLACKLIST_LIST_URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == len(create_blacklist)

    async def test_blacklist(self, api_client):
        data = {
            "host": "198.51.111.42",
            "until": datetime.now(tz=None).isoformat(),
        }

        response = await api_client.post(BLACKLIST_LIST_URL, json=data)
        response_json = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert response_json["host"] == data["host"]
        assert response_json["until"] == data["until"]
        assert "id" in response_json

    async def test_unblacklist(self, api_client, create_blacklist):
        to_be_deleted_ip_id = create_blacklist[0].id

        response = await api_client.delete(
            BLACKLIST_DETAIL_URL.format(id=to_be_deleted_ip_id)
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""

        async with testing_session() as db:
            ips = await blacklist_service.get_multi(db=db)
        assert to_be_deleted_ip_id not in [ip.id for ip in ips]


class TestDbAPIs:
    async def test_ping(self, api_client):
        response = await api_client.get(PING_URL)

        assert response.status_code == status.HTTP_200_OK
        assert (
            "Connection established. Database time:"
            in response.json()["message"]
        )


class TestShortURLAPIs:
    @pytest.fixture
    async def create_short_url(self):
        url = await ShortenedURLFactory()
        return url

    @pytest.fixture
    async def create_short_url_with_calls(self, api_client, create_short_url):
        url = create_short_url
        async with testing_session() as db:
            calls_before = await url_use_service.count(
                db=db, filter=dict(url_id=url.id)
            )
        return url, calls_before

    async def test_create(self, api_client, mocker):
        shortener_mock = mocker.patch(
            "api.v1.shortened_url.generate_short_url",
            return_value="https://test_mock.com",
        )
        data = {"original_url": TEST_URL}

        response = await api_client.post(SHORT_URL_LIST_URL, json=data)
        response_json = response.json()

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response_json
        assert "created_at" in response_json
        assert "deleted" in response_json
        assert response_json["original"] == TEST_URL
        assert response_json["value"] == shortener_mock.return_value

    async def test_bulk_create(self, api_client):
        data = [
            {"original_url": f"https://url{number}.com" for number in range(3)}
        ]
        response = await api_client.post(SHORT_URL_SHORTEN_URL, json=data)
        response_json = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(response_json) == len(data)
        for url in response_json:
            assert "short_id" in url
            assert "short_url" in url

    async def test_retrieve(self, api_client, create_short_url):
        url = create_short_url

        response = await api_client.get(SHORT_URL_DETAIL_URL.format(id=url.id))

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["Location"] == create_short_url.original

    async def test_destroy(self, api_client, create_short_url):
        """Deletion only sets URL as deleted"""
        url = create_short_url
        assert not url.deleted
        async with testing_session() as db:
            urls_before = await short_url_service.count(db=db)

        response = await api_client.delete(
            SHORT_URL_DETAIL_URL.format(id=url.id)
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""
        async with testing_session() as db:
            url_after = await short_url_service.get(db=db, id=url.id)
            urls_after = await short_url_service.count(db=db)
        assert urls_after == urls_before
        assert url_after.deleted

    async def test_status(self, api_client, create_short_url):
        url = create_short_url
        uses = [await ShortenedURLUseFactory(url_id=url.id) for _ in range(2)]

        response = await api_client.get(SHORT_URL_STATUS_URL.format(id=url.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == len(uses)

    async def test_status_full_info(self, api_client, create_short_url):
        url = create_short_url
        uses = [await ShortenedURLUseFactory(url_id=url.id) for _ in range(2)]

        response = await api_client.get(
            SHORT_URL_STATUS_URL.format(id=url.id), params={"full_info": True}
        )
        response_json = response.json()
        print(response_json)
        assert response.status_code == status.HTTP_200_OK
        assert len(response_json) == len(uses)
        for use in response_json:
            assert "id" in use
            assert "created_at" in use
            assert "host" in use
            assert "port" in use
            assert "user_agent" in use
            assert "user_id" in use

    async def test_status_added(self, api_client, create_short_url_with_calls):
        """URL call history is updated on a call"""
        url, before = create_short_url_with_calls
        await api_client.get(SHORT_URL_DETAIL_URL.format(id=url.id))

        async with testing_session() as db:
            after = await url_use_service.count(
                db=db, filter=dict(url_id=url.id)
            )
        assert before + 1 == after
