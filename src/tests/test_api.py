from datetime import datetime

import pytest
from fastapi import status

from services.services import blacklist_service

from .factories import BlacklistClientFactory, testing_session

pytestmark = pytest.mark.anyio

BLACKLIST_LIST_URL = "/api/v1/blacklist"


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
        BLACKLIST_DETAIL_URL = f"{BLACKLIST_LIST_URL}/{to_be_deleted_ip_id}"

        response = await api_client.delete(BLACKLIST_DETAIL_URL)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""

        async with testing_session() as db:
            ips = await blacklist_service.get_multi(db=db)
        assert to_be_deleted_ip_id not in [ip.id for ip in ips]
