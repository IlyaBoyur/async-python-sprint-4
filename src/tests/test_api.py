from datetime import datetime, timedelta

import pytest
from fastapi import status

from main import app
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


BLACKLIST_LIST_URL = app.url_path_for("show_blacklist")
BLACKLIST_DETAIL_URL = app.url_path_for("remove_from_blacklist", id="{id}")
PING_URL = app.url_path_for("ping_db")
SHORT_URL_LIST_URL = app.url_path_for("create_short_url")
SHORT_URL_DETAIL_URL = app.url_path_for("read_short_url", id="{id}")
SHORT_URL_STATUS_URL = app.url_path_for(
    "read_short_url_use_history", id="{id}"
)
SHORT_URL_SHORTEN_URL = app.url_path_for("bulk_create_short_url")

TEST_URL = "https://www.ya.ru"
TEST_SHORT_URL = "{url}/not-really-short/"


class TestBlacklistAPIs:
    @pytest.fixture
    async def create_blacklist(self, api_client):
        clients = [await BlacklistClientFactory() for _ in range(3)]
        return clients

    async def test_blacklist_middleware(self, api_client, mocker):
        await BlacklistClientFactory(
            host="198.51.255.42", until=datetime.now() + timedelta(hours=1)
        )
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
    async def shortener_mock(self, mocker):
        shortener_mock = mocker.patch(
            "api.v1.shortened_url.generate_short_url",
            side_effect=lambda url: TEST_SHORT_URL.format(url=url),
        )
        return shortener_mock

    @pytest.fixture
    async def create_short_url_with_calls(self, api_client, create_short_url):
        url = create_short_url
        async with testing_session() as db:
            calls_before = await url_use_service.count(
                db=db, filter=dict(url_id=url.id)
            )
        return url, calls_before

    async def test_create(self, api_client, shortener_mock):
        data = {"original_url": TEST_URL}

        response = await api_client.post(SHORT_URL_LIST_URL, json=data)
        response_json = response.json()

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response_json
        assert "created_at" in response_json
        assert "deleted" in response_json
        assert response_json["original"] == TEST_URL
        assert response_json["value"] == shortener_mock.side_effect(TEST_URL)
        shortener_mock.assert_called_once_with(TEST_URL)

    async def test_bulk_create(self, api_client, shortener_mock):
        data = [
            {"original_url": f"https://url{number}.com"} for number in range(3)
        ]
        response = await api_client.post(SHORT_URL_SHORTEN_URL, json=data)
        response_json = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(response_json) == len(data)
        for url in response_json:
            assert "short_id" in url
            assert "short_url" in url
        for url in data:
            shortener_mock.assert_any_call(url["original_url"])

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
