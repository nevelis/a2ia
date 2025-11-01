"""Unit tests for Businessmap/Kanbanize integration.

Tests both the core businessmap module and the MCP/REST integrations.
All tests use mocked HTTP calls and mocked sleeps for fast offline execution.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from a2ia.tools import businessmap
from a2ia.tools.businessmap_tools import (
    get_businessmap_card,
    get_businessmap_card_with_children,
    get_businessmap_cards_by_board,
    get_businessmap_cards_by_column,
    search_businessmap_cards_by_assignee,
    get_businessmap_blocked_cards,
    get_businessmap_config,
    get_board_status,
    get_team_members,
    list_all_teams,
    get_card_details,
)


# Test fixtures

@pytest.fixture
def mock_card_data():
    """Sample card data for testing."""
    return {
        "card_id": 12345,
        "title": "Test Card",
        "description": "Test description",
        "column_name": "In Progress",
        "owner_user_id": "user123",
        "type_name": "Feature",
        "workflow_name": "Development",
        "board_id": 37,
        "linked_cards": [
            {"card_id": 67890, "link_type": "child"}
        ]
    }


@pytest.fixture
def mock_child_card_data():
    """Sample child card data for testing."""
    return {
        "card_id": 67890,
        "title": "Child Card",
        "description": "Child description",
        "column_name": "Done",
        "owner_user_id": "user456",
        "type_name": "Task",
        "workflow_name": "Development",
        "board_id": 37,
        "linked_cards": []
    }


@pytest.fixture
def mock_cards_response():
    """Sample cards list response."""
    return {
        "data": {
            "data": [
                {"card_id": 1, "title": "Card 1"},
                {"card_id": 2, "title": "Card 2"},
            ]
        }
    }


# Test businessmap.py client functions

@pytest.mark.asyncio
async def test_get_card_async_success(mock_card_data):
    """Test successful card fetch."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": mock_card_data}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await businessmap.get_card_async(12345)

        assert result == mock_card_data
        assert result["card_id"] == 12345
        assert result["title"] == "Test Card"


@pytest.mark.asyncio
async def test_get_card_async_not_found():
    """Test card fetch with invalid ID."""
    result = await businessmap.get_card_async(0)
    assert result is None


@pytest.mark.asyncio
async def test_get_card_async_http_error():
    """Test card fetch with HTTP error."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not found", request=MagicMock(), response=mock_response
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await businessmap.get_card_async(99999)

        assert result is None


@pytest.mark.asyncio
async def test_get_card_async_rate_limit(mock_sleep):
    """Test card fetch with rate limiting and Retry-After header."""
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {"Retry-After": "5"}  # API says wait 5 seconds
    mock_response_429.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate limited", request=MagicMock(), response=mock_response_429
    )

    mock_response_success = MagicMock()
    mock_response_success.json.return_value = {"data": {"card_id": 12345}}
    mock_response_success.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        # First call returns 429, second succeeds
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=[mock_response_429, mock_response_success]
        )

        result = await businessmap.get_card_async(12345)

        assert result["card_id"] == 12345

        # Verify sleep was called with the Retry-After value
        mock_sleep.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_get_cards_async_success(mock_cards_response):
    """Test successful cards fetch."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_cards_response
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await businessmap.get_cards_async({"board_ids": [37]})

        assert result == mock_cards_response
        assert len(result["data"]["data"]) == 2


@pytest.mark.asyncio
async def test_get_cards_async_empty_params():
    """Test cards fetch with empty params."""
    result = await businessmap.get_cards_async({})
    assert result is None


@pytest.mark.asyncio
async def test_get_card_with_children(mock_card_data, mock_child_card_data):
    """Test fetching card with children."""
    with patch("a2ia.tools.businessmap.get_card_async") as mock_get_card:
        # Mock parent card
        mock_get_card.side_effect = [mock_card_data, mock_child_card_data]

        result = await businessmap.get_card_with_children(12345)

        assert result is not None
        assert result["card_id"] == 12345
        assert result["title"] == "Test Card"
        assert len(result["children"]) == 1
        assert result["children"][0]["card_id"] == 67890


@pytest.mark.asyncio
async def test_get_card_with_children_cycle_detection():
    """Test that cycle detection prevents infinite loops."""
    seen = {12345}
    result = await businessmap.get_card_with_children(12345, seen)
    assert result is None


@pytest.mark.asyncio
async def test_get_cards_by_board(mock_cards_response):
    """Test getting cards by board."""
    with patch("a2ia.tools.businessmap.get_cards_async") as mock_get_cards:
        mock_get_cards.return_value = mock_cards_response

        result = await businessmap.get_cards_by_board(37)

        assert result is not None
        assert len(result) == 2


@pytest.mark.asyncio
async def test_get_cards_by_column(mock_cards_response):
    """Test getting cards by column."""
    with patch("a2ia.tools.businessmap.get_cards_async") as mock_get_cards:
        mock_get_cards.return_value = mock_cards_response

        result = await businessmap.get_cards_by_column(37, 1234)

        assert result is not None
        assert len(result) == 2


@pytest.mark.asyncio
async def test_search_cards_by_assignee(mock_cards_response):
    """Test searching cards by assignee."""
    mock_user = {"user_id": "user123", "realname": "Test User"}

    with patch("a2ia.tools.businessmap.find_user_by_name") as mock_find_user:
        with patch("a2ia.tools.businessmap.get_cards_async") as mock_get_cards:
            mock_find_user.return_value = mock_user
            mock_get_cards.return_value = mock_cards_response

            result = await businessmap.search_cards_by_assignee("Test User", 37)

            assert result is not None
            assert len(result) == 2


@pytest.mark.asyncio
async def test_search_cards_by_assignee_user_not_found(mock_cards_response):
    """Test searching cards by assignee when user is not found."""
    with patch("a2ia.tools.businessmap.find_user_by_name") as mock_find_user:
        mock_find_user.return_value = None

        result = await businessmap.search_cards_by_assignee("Nonexistent User", 37)

        assert result is None


@pytest.mark.asyncio
async def test_get_users_async_success():
    """Test successful users fetch."""
    mock_users = [
        {"user_id": "user123", "realname": "John Doe"},
        {"user_id": "user456", "realname": "Jane Smith"}
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": mock_users}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await businessmap.get_users_async()

        assert result == mock_users
        assert len(result) == 2


@pytest.mark.asyncio
async def test_find_user_by_name_exact_match():
    """Test finding user by exact name match."""
    mock_users = [
        {"user_id": "user123", "realname": "John Doe"},
        {"user_id": "user456", "realname": "Jane Smith"}
    ]

    with patch("a2ia.tools.businessmap.get_users_async") as mock_get_users:
        mock_get_users.return_value = mock_users

        result = await businessmap.find_user_by_name("John Doe")

        assert result is not None
        assert result["user_id"] == "user123"
        assert result["realname"] == "John Doe"


@pytest.mark.asyncio
async def test_find_user_by_name_partial_match():
    """Test finding user by partial name match."""
    mock_users = [
        {"user_id": "user123", "realname": "John Doe"},
        {"user_id": "user456", "realname": "Jane Smith"}
    ]

    with patch("a2ia.tools.businessmap.get_users_async") as mock_get_users:
        mock_get_users.return_value = mock_users

        result = await businessmap.find_user_by_name("john")

        assert result is not None
        assert result["user_id"] == "user123"


@pytest.mark.asyncio
async def test_find_user_by_name_not_found():
    """Test finding user that doesn't exist."""
    mock_users = [
        {"user_id": "user123", "realname": "John Doe"}
    ]

    with patch("a2ia.tools.businessmap.get_users_async") as mock_get_users:
        mock_get_users.return_value = mock_users

        result = await businessmap.find_user_by_name("Nonexistent")

        assert result is None


@pytest.mark.asyncio
async def test_get_blocked_cards(mock_cards_response):
    """Test getting blocked cards."""
    with patch("a2ia.tools.businessmap.get_cards_async") as mock_get_cards:
        mock_get_cards.return_value = mock_cards_response

        result = await businessmap.get_blocked_cards(37)

        assert result is not None
        assert len(result) == 2


# Test MCP server tool functions

@pytest.mark.asyncio
async def test_get_businessmap_card_tool(mock_card_data):
    """Test get_businessmap_card MCP tool."""
    with patch("a2ia.tools.businessmap.get_card_async") as mock_get_card:
        mock_get_card.return_value = mock_card_data

        result = await get_businessmap_card(12345)
        data = json.loads(result)

        assert data["card_id"] == 12345
        assert data["title"] == "Test Card"


@pytest.mark.asyncio
async def test_get_businessmap_card_tool_not_found():
    """Test get_businessmap_card tool with not found."""
    with patch("a2ia.tools.businessmap.get_card_async") as mock_get_card:
        mock_get_card.return_value = None

        result = await get_businessmap_card(99999)
        data = json.loads(result)

        assert "error" in data


@pytest.mark.asyncio
async def test_get_businessmap_card_with_children_tool(mock_card_data):
    """Test get_businessmap_card_with_children MCP tool."""
    hierarchy = {
        "card_id": 12345,
        "title": "Test Card",
        "children": []
    }

    with patch("a2ia.tools.businessmap.get_card_with_children") as mock_get_hierarchy:
        mock_get_hierarchy.return_value = hierarchy

        result = await get_businessmap_card_with_children(12345)
        data = json.loads(result)

        assert data["card_id"] == 12345
        assert "children" in data


@pytest.mark.asyncio
async def test_get_businessmap_cards_by_board_tool():
    """Test get_businessmap_cards_by_board MCP tool."""
    cards = [{"card_id": 1}, {"card_id": 2}]

    with patch("a2ia.tools.businessmap.get_cards_by_board") as mock_get_cards:
        mock_get_cards.return_value = cards

        result = await get_businessmap_cards_by_board(37)
        data = json.loads(result)

        assert data["count"] == 2
        assert len(data["cards"]) == 2


@pytest.mark.asyncio
async def test_get_businessmap_cards_by_column_tool():
    """Test get_businessmap_cards_by_column MCP tool."""
    cards = [{"card_id": 1}]

    with patch("a2ia.tools.businessmap.get_cards_by_column") as mock_get_cards:
        mock_get_cards.return_value = cards

        result = await get_businessmap_cards_by_column(37, 1234)
        data = json.loads(result)

        assert data["count"] == 1


@pytest.mark.asyncio
async def test_search_businessmap_cards_by_assignee_tool():
    """Test search_businessmap_cards_by_assignee MCP tool."""
    cards = [{"card_id": 1, "owner": "user123"}]

    with patch("a2ia.tools.businessmap.search_cards_by_assignee") as mock_search:
        mock_search.return_value = cards

        result = await search_businessmap_cards_by_assignee("Test User", 37)
        data = json.loads(result)

        assert data["assignee"] == "Test User"
        assert data["count"] == 1


@pytest.mark.asyncio
async def test_get_businessmap_blocked_cards_tool():
    """Test get_businessmap_blocked_cards MCP tool."""
    cards = [{"card_id": 1, "is_blocked": True}]

    with patch("a2ia.tools.businessmap.get_blocked_cards") as mock_get_blocked:
        mock_get_blocked.return_value = cards

        result = await get_businessmap_blocked_cards(37)
        data = json.loads(result)

        assert data["count"] == 1
        assert "blocked_cards" in data


@pytest.mark.asyncio
async def test_get_businessmap_config_resource():
    """Test get_businessmap_config MCP resource."""
    result = await get_businessmap_config()
    data = json.loads(result)

    assert "api_url" in data
    assert "board_id" in data
    assert "api_key_configured" in data


@pytest.mark.asyncio
async def test_get_board_status_resource():
    """Test get_board_status MCP resource."""
    all_cards = [{"card_id": 1}, {"card_id": 2}]
    blocked_cards = [{"card_id": 2}]

    with patch("a2ia.tools.businessmap.get_cards_by_board") as mock_all:
        with patch("a2ia.tools.businessmap.get_blocked_cards") as mock_blocked:
            mock_all.return_value = all_cards
            mock_blocked.return_value = blocked_cards

            result = await get_board_status(37)
            data = json.loads(result)

            assert data["board_id"] == 37
            assert data["total_cards"] == 2
            assert data["blocked_cards"] == 1
            assert data["status"] == "operational"


@pytest.mark.asyncio
async def test_error_handling_in_tools():
    """Test error handling in MCP tools."""
    with patch("a2ia.tools.businessmap.get_card_async") as mock_get_card:
        mock_get_card.side_effect = Exception("API Error")

        result = await get_businessmap_card(12345)
        data = json.loads(result)

        assert "error" in data
        assert "API Error" in data["error"]


# Test team roster tools

@pytest.mark.asyncio
async def test_get_team_members():
    """Test getting team members."""
    result = await get_team_members("datahub")
    data = json.loads(result)

    assert "teamMembers" in data
    assert "datahub" in data["teamMembers"]
    assert isinstance(data["teamMembers"]["datahub"], list)
    
    # Verify expected members are present
    team_members = data["teamMembers"]["datahub"]
    assert "Andrew Oreshko" in team_members


@pytest.mark.asyncio
async def test_get_team_members_not_found():
    """Test getting team members for non-existent team."""
    result = await get_team_members("nonexistent")
    data = json.loads(result)

    assert "error" in data
    assert "available_teams" in data


@pytest.mark.asyncio
async def test_list_all_teams():
    """Test listing all teams."""
    result = await list_all_teams()
    data = json.loads(result)

    assert "teams" in data
    assert "datahub" in data["teams"]
    assert "platform" in data["teams"]
    assert "teamMembers" in data


@pytest.mark.asyncio
async def test_get_card_details():
    """Test getting card details from mock data."""
    result = await get_card_details("12345")
    data = json.loads(result)

    assert data["id"] == "12345"
    assert data["assignee"] == "Andrew Oreshko"
    assert data["team"] == "datahub"


@pytest.mark.asyncio
async def test_get_card_details_not_found():
    """Test getting card details for non-existent card."""
    result = await get_card_details("99999")
    data = json.loads(result)

    assert "error" in data
    assert "available_cards" in data


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])


