"""Businessmap/Kanbanize API client for A2IA integration.

This module provides core functions for interacting with the Businessmap (formerly Kanbanize) API.
These functions are used by both MCP tools and REST API endpoints.
"""

import asyncio
import httpx
import logging
import os
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Configuration from environment
API_KEY = os.getenv("BUSINESSMAP_API_KEY") or os.getenv("KANBANIZE_API_KEY", "")
API_URL = os.getenv("BUSINESSMAP_API_URL", "https://bettercomp.kanbanize.com/api/v2")
BOARD_ID = int(os.getenv("BUSINESSMAP_BOARD_ID", "37"))
WORKFLOW_ID = int(os.getenv("BUSINESSMAP_WORKFLOW_ID", "170"))
COLUMN_ID = int(os.getenv("BUSINESSMAP_COLUMN_ID", "1234"))

BASE_HEADERS = {"apikey": API_KEY}

# Sleep function that can be mocked in tests
_sleep_func: Callable[[float], asyncio.Task] = asyncio.sleep


def set_sleep_func(func: Callable[[float], asyncio.Task]) -> None:
    """
    Set the sleep function (useful for testing).

    Args:
        func: Async function to use for sleeping
    """
    global _sleep_func
    _sleep_func = func


async def get_cards_async(params: dict) -> Optional[dict]:
    """Fetch cards based on provided parameters.

    Args:
        params: Query parameters for filtering cards (board_ids, column_ids, etc.)

    Returns:
        Card data dict or None if request fails
    """
    if not params:
        return None

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url=f"{API_URL}/cards",
                headers=BASE_HEADERS,
                params={
                    **params,
                    "per_page": 1000,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.exception(f"Get cards failed: {e}")
            return None

        return response.json()


async def get_card_async(card_id: int) -> Optional[dict]:
    """Fetch a single card by ID with retry logic for rate limiting.

    Args:
        card_id: Businessmap card ID

    Returns:
        Card data dict or None if request fails
    """
    if not card_id:
        return None

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(3):
            try:
                response = await client.get(
                    f"{API_URL}/cards/{card_id}",
                    headers=BASE_HEADERS,
                )
                response.raise_for_status()
                return response.json().get("data")

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Honor Retry-After header from API
                    retry_after = int(e.response.headers.get("Retry-After", "2"))
                    logger.warning(f"Rate limited (429). Waiting {retry_after}s before retrying...")
                    await _sleep_func(retry_after)
                elif 500 <= e.response.status_code < 600:
                    wait = 2 ** attempt
                    logger.warning(f"Server error {e.response.status_code}. Retrying in {wait}s...")
                    await _sleep_func(wait)
                else:
                    logger.error(f"HTTP error {e.response.status_code} for card {card_id}")
                    return None

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                wait = 2 ** attempt
                logger.warning(f"Network issue {e}. Retrying in {wait}s...")
                await _sleep_func(wait)

            except Exception as e:
                logger.exception(f"Unexpected error fetching card {card_id}: {e}")
                return None

        logger.error(f"Failed to fetch card {card_id} after 3 attempts.")
        return None


async def get_card_with_children(card_id: int, seen: Optional[set[int]] = None) -> Optional[dict]:
    """Recursively fetch a card and all its child cards.

    Args:
        card_id: Businessmap card ID
        seen: Set of already-fetched card IDs to prevent cycles

    Returns:
        Dict with card data and nested children, or None if fetch fails
    """
    if seen is None:
        seen = set()
    if card_id in seen:
        return None

    seen.add(card_id)
    card = await get_card_async(card_id)

    if not card:
        return None

    # Extract child card IDs from linked cards
    child_ids = [
        linked["card_id"]
        for linked in card.get("linked_cards", [])
        if linked.get("link_type") == "child"
    ]

    if child_ids:
        child_results = await asyncio.gather(
            *(get_card_with_children(cid, seen) for cid in child_ids)
        )
        children = [c_r for c_r in child_results if c_r is not None]
    else:
        children = []

    return {
        "card_id": card["card_id"],
        "title": card.get("title", ""),
        "description": card.get("description") or card.get("title"),
        "status": card.get("column_name", ""),
        "assignee": card.get("owner_user_id", ""),
        "type": card.get("type_name", ""),
        "workflow": card.get("workflow_name", ""),
        "board_id": card.get("board_id"),
        "linked_cards": card.get("linked_cards", []),
        "children": children,
    }


async def get_cards_by_board(board_id: Optional[int] = None) -> Optional[list]:
    """Get all cards for a specific board.

    Args:
        board_id: Board ID (defaults to configured BOARD_ID)

    Returns:
        List of card data dicts
    """
    board_id = board_id or BOARD_ID
    params = {
        "board_ids": [board_id],
    }

    response = await get_cards_async(params=params)
    if not response:
        return None

    return response.get("data", {}).get("data", [])


async def get_cards_by_column(board_id: Optional[int] = None, column_id: Optional[int] = None) -> Optional[list]:
    """Get all cards in a specific column.

    Args:
        board_id: Board ID (defaults to configured BOARD_ID)
        column_id: Column ID (defaults to configured COLUMN_ID)

    Returns:
        List of card data dicts
    """
    board_id = board_id or BOARD_ID
    column_id = column_id or COLUMN_ID

    params = {
        "board_ids": [board_id],
        "column_ids": [column_id],
    }

    response = await get_cards_async(params=params)
    if not response:
        return None

    return response.get("data", {}).get("data", [])


async def get_users_async() -> Optional[list]:
    """Fetch all users from Businessmap.

    Returns:
        List of user data dicts or None if request fails
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url=f"{API_URL}/users",
                headers=BASE_HEADERS,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except httpx.HTTPError as e:
            logger.exception(f"Get users failed: {e}")
            return None


async def find_user_by_name(name: str) -> Optional[dict]:
    """Find a user by their display name.

    Args:
        name: User's display name (case-insensitive partial match)

    Returns:
        User data dict or None if not found
    """
    users = await get_users_async()
    if not users:
        return None

    name_lower = name.lower()

    # Try exact match first
    for user in users:
        if user.get("realname", "").lower() == name_lower:
            return user

    # Try partial match
    for user in users:
        if name_lower in user.get("realname", "").lower():
            return user

    return None


async def search_cards_by_assignee(assignee_name: str, board_id: Optional[int] = None) -> Optional[list]:
    """Search for cards assigned to a specific user.

    Args:
        assignee_name: User's display name (will be looked up to get user ID)
        board_id: Board ID (defaults to configured BOARD_ID)

    Returns:
        List of card data dicts
    """
    # Look up user by name
    user = await find_user_by_name(assignee_name)
    if not user:
        logger.warning(f"User not found: {assignee_name}")
        return None

    user_id = user.get("user_id")
    if not user_id:
        logger.error(f"User {assignee_name} has no user_id")
        return None

    board_id = board_id or BOARD_ID

    params = {
        "board_ids": [board_id],
        "owner_user_ids": [user_id],
    }

    response = await get_cards_async(params=params)
    if not response:
        return None

    return response.get("data", {}).get("data", [])


async def get_blocked_cards(board_id: Optional[int] = None) -> Optional[list]:
    """Get all blocked cards on a board.

    Args:
        board_id: Board ID (defaults to configured BOARD_ID)

    Returns:
        List of blocked card data dicts
    """
    board_id = board_id or BOARD_ID

    params = {
        "board_ids": [board_id],
        "is_blocked": True,
    }

    response = await get_cards_async(params=params)
    if not response:
        return None

    return response.get("data", {}).get("data", [])


async def get_board_structure(board_id: Optional[int] = None) -> Optional[dict]:
    """Get the workflow structure for a board including columns.

    Args:
        board_id: Board ID (defaults to configured BOARD_ID)

    Returns:
        Dict with board structure including workflows and columns
    """
    board_id = board_id or BOARD_ID

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url=f"{API_URL}/boards/{board_id}",
                headers=BASE_HEADERS,
            )
            response.raise_for_status()
            return response.json().get("data")
        except httpx.HTTPError as e:
            logger.exception(f"Get board structure failed: {e}")
            return None


async def get_workflow_columns(workflow_id: Optional[int] = None) -> Optional[list]:
    """Get all columns for a specific workflow.

    Args:
        workflow_id: Workflow ID (defaults to configured WORKFLOW_ID)

    Returns:
        List of column data dicts
    """
    workflow_id = workflow_id or WORKFLOW_ID

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url=f"{API_URL}/workflows/{workflow_id}",
                headers=BASE_HEADERS,
            )
            response.raise_for_status()
            workflow_data = response.json().get("data")
            return workflow_data.get("columns", []) if workflow_data else None
        except httpx.HTTPError as e:
            logger.exception(f"Get workflow columns failed: {e}")
            return None


async def get_column_name(column_id: int) -> Optional[str]:
    """Get the name of a column by its ID.

    Args:
        column_id: Column ID

    Returns:
        Column name or None if not found
    """
    # First try getting from default workflow
    columns = await get_workflow_columns()
    if columns:
        for column in columns:
            if column.get("column_id") == column_id:
                return column.get("name")

    return None


