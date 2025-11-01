"""Businessmap/Kanbanize MCP tools for A2IA.

These tools provide MCP-decorated wrappers around the core businessmap functions.
"""

import json
import logging

from ..core import get_mcp_app
from . import businessmap
from .data import TEAMS, CARDS

logger = logging.getLogger(__name__)

mcp = get_mcp_app()


@mcp.tool()
async def get_team_members(team_name: str) -> str:
    """Get all members of a specific team.

    Args:
        team_name: Name of the team (e.g., 'datahub', 'platform', 'frontend', 'backend')

    Returns:
        JSON string with team members
    """
    team_name_lower = team_name.lower()

    if team_name_lower not in TEAMS:
        return json.dumps({
            "error": f"Team '{team_name}' not found",
            "available_teams": list(TEAMS.keys())
        }, indent=2)

    result = {
        "teamMembers": {
            team_name_lower: TEAMS[team_name_lower]
        }
    }

    return json.dumps(result, indent=2)


@mcp.tool()
async def list_all_teams() -> str:
    """List all available teams.

    Returns:
        JSON string with all teams and their members
    """
    result = {
        "teams": list(TEAMS.keys()),
        "teamMembers": TEAMS
    }

    return json.dumps(result, indent=2)


@mcp.tool()
async def get_card_details(card_id: str) -> str:
    """Get detailed information about a specific card from mock data.

    Args:
        card_id: The ID of the card to retrieve

    Returns:
        JSON string with card details
    """
    if card_id not in CARDS:
        return json.dumps({
            "error": f"Card '{card_id}' not found",
            "available_cards": list(CARDS.keys())
        }, indent=2)

    return json.dumps(CARDS[card_id], indent=2)


# Businessmap/Kanbanize Integration Tools

@mcp.tool()
async def get_businessmap_card(card_id: int) -> str:
    """Fetch a single card from Businessmap/Kanbanize by ID.

    Args:
        card_id: The Businessmap card ID

    Returns:
        JSON string with card details or error message
    """
    try:
        card_data = await businessmap.get_card_async(card_id)
        if card_data is None:
            return json.dumps({
                "error": f"Card {card_id} not found or API request failed"
            }, indent=2)

        return json.dumps(card_data, indent=2)
    except Exception as e:
        logger.exception(f"Error fetching card {card_id}: {e}")
        return json.dumps({
            "error": f"Failed to fetch card {card_id}: {str(e)}"
        }, indent=2)


@mcp.tool()
async def get_businessmap_card_with_children(card_id: int) -> str:
    """Fetch a card and all its child cards recursively.

    Args:
        card_id: The Businessmap card ID

    Returns:
        JSON string with card hierarchy including all children
    """
    try:
        card_hierarchy = await businessmap.get_card_with_children(card_id)
        if card_hierarchy is None:
            return json.dumps({
                "error": f"Card {card_id} not found or API request failed"
            }, indent=2)

        return json.dumps(card_hierarchy, indent=2)
    except Exception as e:
        logger.exception(f"Error fetching card hierarchy for {card_id}: {e}")
        return json.dumps({
            "error": f"Failed to fetch card hierarchy: {str(e)}"
        }, indent=2)


@mcp.tool()
async def get_businessmap_cards_by_board(board_id: int = None) -> str:
    """Get all cards for a specific board.

    Args:
        board_id: Board ID (optional, uses configured default if not provided)

    Returns:
        JSON string with list of cards
    """
    try:
        cards = await businessmap.get_cards_by_board(board_id)
        if cards is None:
            return json.dumps({
                "error": "Failed to fetch cards or board not found"
            }, indent=2)

        return json.dumps({"cards": cards, "count": len(cards)}, indent=2)
    except Exception as e:
        logger.exception(f"Error fetching cards by board: {e}")
        return json.dumps({
            "error": f"Failed to fetch cards: {str(e)}"
        }, indent=2)


@mcp.tool()
async def get_businessmap_cards_by_column(board_id: int = None, column_id: int = None) -> str:
    """Get all cards in a specific column.

    Args:
        board_id: Board ID (optional, uses configured default)
        column_id: Column ID (optional, uses configured default)

    Returns:
        JSON string with list of cards in the column
    """
    try:
        cards = await businessmap.get_cards_by_column(board_id, column_id)
        if cards is None:
            return json.dumps({
                "error": "Failed to fetch cards or column not found"
            }, indent=2)

        return json.dumps({"cards": cards, "count": len(cards)}, indent=2)
    except Exception as e:
        logger.exception(f"Error fetching cards by column: {e}")
        return json.dumps({
            "error": f"Failed to fetch cards: {str(e)}"
        }, indent=2)


@mcp.tool()
async def search_businessmap_cards_by_assignee(assignee_id: str, board_id: int = None) -> str:
    """Search for cards assigned to a specific user.

    Args:
        assignee_id: User's display name (e.g., "Joseph Lee") - will be looked up automatically
        board_id: Board ID (optional, uses configured default)

    Returns:
        JSON string with list of assigned cards
    """
    try:
        cards = await businessmap.search_cards_by_assignee(assignee_id, board_id)
        if cards is None:
            return json.dumps({
                "error": "Failed to fetch cards or assignee not found"
            }, indent=2)

        return json.dumps({"cards": cards, "count": len(cards), "assignee": assignee_id}, indent=2)
    except Exception as e:
        logger.exception(f"Error searching cards by assignee: {e}")
        return json.dumps({
            "error": f"Failed to search cards: {str(e)}"
        }, indent=2)


@mcp.tool()
async def get_businessmap_blocked_cards(board_id: int = None) -> str:
    """Get all blocked cards on a board.

    Args:
        board_id: Board ID (optional, uses configured default)

    Returns:
        JSON string with list of blocked cards
    """
    try:
        cards = await businessmap.get_blocked_cards(board_id)
        if cards is None:
            return json.dumps({
                "error": "Failed to fetch blocked cards"
            }, indent=2)

        return json.dumps({"blocked_cards": cards, "count": len(cards)}, indent=2)
    except Exception as e:
        logger.exception(f"Error fetching blocked cards: {e}")
        return json.dumps({
            "error": f"Failed to fetch blocked cards: {str(e)}"
        }, indent=2)


@mcp.tool()
async def get_businessmap_board_structure(board_id: int = None) -> str:
    """Get the workflow structure for a board including columns.

    Args:
        board_id: Board ID (optional, uses configured default)

    Returns:
        JSON string with board structure including workflows and columns
    """
    try:
        structure = await businessmap.get_board_structure(board_id)
        if structure is None:
            return json.dumps({
                "error": "Failed to fetch board structure"
            }, indent=2)

        return json.dumps(structure, indent=2)
    except Exception as e:
        logger.exception(f"Error fetching board structure: {e}")
        return json.dumps({
            "error": f"Failed to fetch board structure: {str(e)}"
        }, indent=2)


@mcp.tool()
async def get_businessmap_workflow_columns(workflow_id: int = None) -> str:
    """Get all columns for a specific workflow.

    Args:
        workflow_id: Workflow ID (optional, uses configured default)

    Returns:
        JSON string with list of columns
    """
    try:
        columns = await businessmap.get_workflow_columns(workflow_id)
        if columns is None:
            return json.dumps({
                "error": "Failed to fetch workflow columns"
            }, indent=2)

        return json.dumps({"columns": columns, "count": len(columns)}, indent=2)
    except Exception as e:
        logger.exception(f"Error fetching workflow columns: {e}")
        return json.dumps({
            "error": f"Failed to fetch workflow columns: {str(e)}"
        }, indent=2)


@mcp.tool()
async def get_businessmap_column_name(column_id: int) -> str:
    """Get the name of a column by its ID.

    Args:
        column_id: Column ID

    Returns:
        JSON string with column name or error
    """
    try:
        column_name = await businessmap.get_column_name(column_id)
        if column_name is None:
            return json.dumps({
                "error": f"Column {column_id} not found"
            }, indent=2)

        return json.dumps({"column_id": column_id, "name": column_name}, indent=2)
    except Exception as e:
        logger.exception(f"Error fetching column name: {e}")
        return json.dumps({
            "error": f"Failed to fetch column name: {str(e)}"
        }, indent=2)


# MCP Prompts

@mcp.prompt()
async def summarize_team_work(team_name: str) -> str:
    """Generate a formatted summary of what a team is working on.

    This prompt provides instructions for formatting team work summaries with:
    - Card IDs in [#12345] format
    - Card status/column information
    - Concise descriptions
    - Grouped by team member

    Args:
        team_name: Name of the team to summarize

    Returns:
        Prompt text with instructions for formatting the summary
    """
    return f"""Please provide a summary of what the {team_name} team is currently working on.

For each team member, list their assigned cards with the following format:

**Team Member Name** (X cards)
- [#card_id] Card Title - Brief description (Column: status)
- [#card_id] Card Title - Brief description (Column: status)

Guidelines:
- Include card IDs in [#card_id] format for easy reference
- Include the column/status information in parentheses
- Keep descriptions concise (one line max)
- Group all cards by assignee
- Sort cards by priority or position if available
- If a card is blocked, mention it explicitly

Example format:
**Aaron Sinclair** (3 cards)
- [#87362] E2E test fixes - Fixing flaky tests in stage environment (Column: In Progress)
- [#85520] Feature flag removal - Remove deprecated flags from codebase (Column: Ready for Review)
- [#83943] Database optimization - Improve query performance (Column: Blocked - waiting on DBA)
"""


# MCP Resources

@mcp.resource("businessmap://config")
async def get_businessmap_config() -> str:
    """Get current Businessmap configuration.

    Returns:
        JSON string with API configuration (sanitized, no keys)
    """
    config = {
        "api_url": businessmap.API_URL,
        "board_id": businessmap.BOARD_ID,
        "workflow_id": businessmap.WORKFLOW_ID,
        "column_id": businessmap.COLUMN_ID,
        "api_key_configured": bool(businessmap.API_KEY),
    }
    return json.dumps(config, indent=2)


@mcp.resource("businessmap://board/{board_id}/status")
async def get_board_status(board_id: int) -> str:
    """Get status overview for a board.

    Args:
        board_id: Board ID to get status for

    Returns:
        JSON string with board status including card counts
    """
    try:
        all_cards = await businessmap.get_cards_by_board(board_id)
        blocked_cards = await businessmap.get_blocked_cards(board_id)

        if all_cards is None:
            return json.dumps({"error": "Failed to fetch board data"}, indent=2)

        status = {
            "board_id": board_id,
            "total_cards": len(all_cards) if all_cards else 0,
            "blocked_cards": len(blocked_cards) if blocked_cards else 0,
            "status": "operational" if all_cards is not None else "error"
        }

        return json.dumps(status, indent=2)
    except Exception as e:
        logger.exception(f"Error fetching board status: {e}")
        return json.dumps({
            "error": f"Failed to fetch board status: {str(e)}"
        }, indent=2)


