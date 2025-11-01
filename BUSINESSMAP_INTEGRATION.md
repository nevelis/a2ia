# Businessmap/Kanbanize Integration for A2IA

This document describes the Businessmap (formerly Kanbanize) integration that has been added to A2IA.

## Overview

The integration provides comprehensive access to Businessmap/Kanbanize boards, cards, and team data through both MCP tools and REST API endpoints. All functionality uses shared domain-specific functions for consistency.

## Architecture

### Core Module (`a2ia/tools/businessmap.py`)
- **Purpose**: Core API client functions for Businessmap/Kanbanize
- **Features**:
  - Rate limiting with retry logic (honors `Retry-After` header)
  - Exponential backoff for server errors
  - Configurable sleep function for testing
  - Comprehensive error handling

### Data Module (`a2ia/tools/data.py`)
- **Purpose**: Team roster data and mock card data
- **Teams**: All company teams with member lists
- **Mock Cards**: Sample card data for testing/demos

### MCP Tools (`a2ia/tools/businessmap_tools.py`)
- **Purpose**: MCP-decorated wrappers around businessmap functions
- **Tools**: 12 MCP tools + 1 prompt + 2 resources
- **Returns**: JSON-formatted strings

### REST API (`a2ia/rest_server.py`)
- **Purpose**: RESTful HTTP endpoints for Businessmap operations
- **Endpoints**: 12 endpoints under `/businessmap/*`
- **Returns**: JSON responses with proper HTTP status codes

## Available Tools/Endpoints

### Team Management
1. **List All Teams**
   - MCP: `list_all_teams()`
   - REST: `GET /businessmap/teams`
   - Returns all teams and their members

2. **Get Team Members**
   - MCP: `get_team_members(team_name: str)`
   - REST: `GET /businessmap/teams/{team_name}`
   - Returns members of a specific team

### Card Operations
3. **Get Card**
   - MCP: `get_businessmap_card(card_id: int)`
   - REST: `GET /businessmap/cards/{card_id}`
   - Fetch single card by ID

4. **Get Card with Children**
   - MCP: `get_businessmap_card_with_children(card_id: int)`
   - REST: `GET /businessmap/cards/{card_id}/children`
   - Recursively fetch card and all child cards

5. **Get Cards by Board**
   - MCP: `get_businessmap_cards_by_board(board_id: int = None)`
   - REST: `GET /businessmap/boards/{board_id}/cards`
   - Get all cards on a board

6. **Get Cards by Column**
   - MCP: `get_businessmap_cards_by_column(board_id: int = None, column_id: int = None)`
   - REST: `GET /businessmap/boards/{board_id}/columns/{column_id}/cards`
   - Get cards in a specific column

7. **Search Cards by Assignee**
   - MCP: `search_businessmap_cards_by_assignee(assignee_id: str, board_id: int = None)`
   - REST: `GET /businessmap/cards/search/assignee/{assignee_name}`
   - Find cards assigned to a user (by name)

8. **Get Blocked Cards**
   - MCP: `get_businessmap_blocked_cards(board_id: int = None)`
   - REST: `GET /businessmap/boards/{board_id}/blocked`
   - Get all blocked cards on a board

### Board Structure
9. **Get Board Structure**
   - MCP: `get_businessmap_board_structure(board_id: int = None)`
   - REST: `GET /businessmap/boards/{board_id}/structure`
   - Get workflow structure including columns

10. **Get Workflow Columns**
    - MCP: `get_businessmap_workflow_columns(workflow_id: int = None)`
    - REST: `GET /businessmap/workflows/{workflow_id}/columns`
    - Get all columns for a workflow

11. **Get Column Name**
    - MCP: `get_businessmap_column_name(column_id: int)`
    - REST: `GET /businessmap/columns/{column_id}/name`
    - Get name of a column by ID

### Configuration
12. **Get Config**
    - MCP: `get_businessmap_config()` (resource: `businessmap://config`)
    - REST: `GET /businessmap/config`
    - Get current configuration (API URL, board ID, etc.)

### MCP-Only Features
- **Prompt**: `summarize_team_work(team_name: str)` - Template for team work summaries
- **Resource**: `businessmap://board/{board_id}/status` - Board status overview

## Environment Variables

The following environment variables must be set in your `.env` file:

```bash
# Required
BUSINESSMAP_API_KEY=your_api_key_here

# Optional (defaults shown)
BUSINESSMAP_API_URL=https://bettercomp.kanbanize.com/api/v2
BUSINESSMAP_BOARD_ID=37
BUSINESSMAP_WORKFLOW_ID=170
BUSINESSMAP_COLUMN_ID=1234
```

**Note**: `KANBANIZE_API_KEY` is also supported as an alias for `BUSINESSMAP_API_KEY`.

## Testing

All tests are designed to run offline with mocked HTTP calls and mocked sleeps.

### Test Suite (`tests/test_businessmap.py`)
- **32 comprehensive tests**
- **Coverage**:
  - Core businessmap module functions
  - MCP tool wrappers
  - Rate limiting and retry logic
  - Error handling
  - Team roster operations
  - Mock data access

### Test Fixtures (`tests/conftest.py`)
- **`mock_sleep`**: Auto-applied fixture that mocks `asyncio.sleep`
  - Prevents actual sleeping in tests
  - Tests run in ~0.76 seconds
  - Allows verification of sleep call arguments

### Running Tests

```bash
# Run businessmap tests only
pytest tests/test_businessmap.py -v

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/test_businessmap.py --cov=a2ia.tools.businessmap --cov-report=term-missing
```

## Usage Examples

### MCP Example

```python
from a2ia.tools.businessmap_tools import (
    get_team_members,
    get_businessmap_card,
    search_businessmap_cards_by_assignee
)

# Get team members
result = await get_team_members("datahub")
print(result)  # JSON string

# Get a card
card = await get_businessmap_card(12345)
print(card)  # JSON string with card details

# Search by assignee
cards = await search_businessmap_cards_by_assignee("Aaron Sinclair")
print(cards)  # JSON string with assigned cards
```

### REST API Example

```bash
# Get team members
curl -H "Authorization: Bearer $A2IA_PASSWORD" \
  https://a2ia.amazingland.live/businessmap/teams/datahub

# Get a card
curl -H "Authorization: Bearer $A2IA_PASSWORD" \
  https://a2ia.amazingland.live/businessmap/cards/12345

# Search by assignee
curl -H "Authorization: Bearer $A2IA_PASSWORD" \
  "https://a2ia.amazingland.live/businessmap/cards/search/assignee/Aaron%20Sinclair"
```

### Python REST Client Example

```python
import httpx

headers = {"Authorization": f"Bearer {password}"}
base_url = "https://a2ia.amazingland.live"

# Get team members
response = httpx.get(f"{base_url}/businessmap/teams/datahub", headers=headers)
print(response.json())

# Get card with children
response = httpx.get(f"{base_url}/businessmap/cards/12345/children", headers=headers)
print(response.json())
```

## Key Features

### Rate Limiting
- Honors `Retry-After` header from API (429 responses)
- Exponential backoff for server errors (500-599)
- Maximum 3 retry attempts per request

### Error Handling
- Graceful error handling with informative error messages
- HTTP errors return appropriate status codes (REST)
- MCP tools return JSON error objects

### Fast Offline Tests
- All tests use mocked HTTP calls
- Mocked sleep function prevents actual delays
- Tests complete in under 1 second
- 100% test coverage of businessmap functionality

### Type Safety
- Type hints throughout
- Optional parameters with sensible defaults
- Consistent return types

## Implementation Details

### Separation of Concerns
- **Domain Logic**: `businessmap.py` - Pure async functions
- **MCP Interface**: `businessmap_tools.py` - MCP decorators + JSON formatting
- **REST Interface**: `rest_server.py` - HTTP endpoints + error handling
- **Data**: `data.py` - Static team roster and mock cards

### Shared Configuration
All modules read from the same environment variables, ensuring consistency across MCP and REST interfaces.

### OpenAPI Spec
The REST API automatically generates OpenAPI documentation at:
- Swagger UI: `https://a2ia.amazingland.live/docs`
- ReDoc: `https://a2ia.amazingland.live/redoc`
- OpenAPI JSON: `https://a2ia.amazingland.live/openapi.json`

## Dynamic Tool Registration

The businessmap tools are **dynamically registered** with the MCP server. This means:

1. **No hardcoded tool lists** - Tools are discovered at runtime by importing modules
2. **Automatic tool discovery** - The tool schema generator queries the MCP server directly
3. **Easy to extend** - Add new tools by creating functions with `@mcp.tool()` decorator
4. **Always in sync** - Generated `tools.json` always reflects currently registered tools

### How It Works

1. `SimpleMCPClient.list_tools()` dynamically imports all tool modules
2. Tool modules register their tools via `@mcp.tool()` decorators on import
3. The client queries the MCP app for all registered tools
4. Tools are converted to Ollama format with snake_case → TitleCase conversion
5. Result is a complete, up-to-date tool schema

This approach eliminates the need to manually update tool lists when adding new tools!

## Files Created/Modified

### Created
- `a2ia/tools/businessmap.py` - Core API client
- `a2ia/tools/businessmap_tools.py` - MCP tool wrappers
- `a2ia/tools/data.py` - Team roster and mock data
- `tests/test_businessmap.py` - Comprehensive test suite
- `BUSINESSMAP_INTEGRATION.md` - This document

### Modified
- `a2ia/mcp_server.py` - Import businessmap_tools
- `a2ia/rest_server.py` - Add 12 Businessmap endpoints
- `tests/conftest.py` - Add mock_sleep fixture
- `a2ia/client/simple_mcp.py` - Dynamic tool registration from MCP server

## Next Steps

1. **Set Environment Variables**: Add `BUSINESSMAP_API_KEY` to your `.env` file
2. **Test MCP Tools**: Use Claude Desktop to test the MCP tools
3. **Test REST API**: Use curl or httpx to test the REST endpoints
4. **Customize Configuration**: Adjust board ID, workflow ID, etc. as needed
5. **Extend Functionality**: Add more Businessmap API endpoints as needed

## Notes

- The bender directory was used as reference but not modified
- All tests pass and run offline
- Integration follows A2IA's existing patterns
- REST API and MCP tools are fully synchronized

