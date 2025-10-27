"""Tool call validation and throttling."""

import time
import json
from typing import Any, Dict, List, Tuple, Optional
from collections import defaultdict


class ToolValidator:
    """Validates tool calls and responses."""
    
    def __init__(self, available_tools: List[Dict[str, Any]]):
        """Initialize validator with available tools.
        
        Args:
            available_tools: List of tool definitions from MCP
        """
        self.available_tools = available_tools
        self.tool_schemas = self._build_tool_schemas()
        self.throttler = ToolThrottler()
    
    def _build_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Build lookup map of tool schemas."""
        schemas = {}
        for tool in self.available_tools:
            func = tool.get('function', {})
            name = func.get('name')
            if name:
                schemas[name] = func.get('parameters', {})
        return schemas
    
    def validate_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate tool call before execution.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
        
        Returns:
            (is_valid, error_message) - error_message empty if valid
        """
        # Check 1: Tool exists
        if tool_name not in self.tool_schemas:
            available = list(self.tool_schemas.keys())[:10]  # Show first 10
            return False, f"Tool '{tool_name}' does not exist. Did you mean one of: {', '.join(available)}?"
        
        # Check 2: Throttling
        allowed, reason = self.throttler.should_allow_call(tool_name)
        if not allowed:
            return False, reason
        
        # Check 3: Required parameters
        schema = self.tool_schemas[tool_name]
        required = schema.get('required', [])
        missing = [p for p in required if p not in arguments]
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"
        
        # Check 4: Unknown parameters (typos)
        properties = schema.get('properties', {})
        unknown = [p for p in arguments.keys() if p not in properties]
        if unknown:
            available_params = list(properties.keys())
            return False, f"Unknown parameters: {', '.join(unknown)}. Available: {', '.join(available_params)}"
        
        # Check 5: Type validation
        for param, value in arguments.items():
            if param in properties:
                expected_type = properties[param].get('type')
                if not self._validate_type(value, expected_type):
                    return False, f"Parameter '{param}' should be {expected_type}, got {type(value).__name__}"
        
        return True, ""
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value matches expected type."""
        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict,
        }
        
        if expected_type not in type_map:
            return True  # Unknown type, can't validate
        
        expected_python_type = type_map[expected_type]
        return isinstance(value, expected_python_type)
    
    def validate_tool_response(self, result: Any, tool_name: str) -> Tuple[bool, List[str]]:
        """Validate tool response.
        
        Args:
            result: Tool response
            tool_name: Name of tool that was called
        
        Returns:
            (is_valid, warnings) - List of warnings (can be empty even if valid)
        """
        warnings = []
        
        # Check for common error patterns
        if isinstance(result, dict):
            # Check for explicit errors
            if result.get('success') is False:
                error_msg = result.get('error', 'Unknown error')
                self.throttler.record_call(tool_name, success=False)
                return False, [f"Tool failed: {error_msg}"]
        
        # Sanity checks (warnings, not errors)
        warnings.extend(self._sanity_check_response(result, tool_name))
        
        # Record successful call
        self.throttler.record_call(tool_name, success=True)
        
        return True, warnings
    
    def _sanity_check_response(self, result: Any, tool_name: str) -> List[str]:
        """Perform sanity checks on tool results."""
        warnings = []
        
        # Check 1: Suspiciously large responses
        if isinstance(result, (dict, list)):
            try:
                result_json = json.dumps(result)
                size_kb = len(result_json) / 1024
                if size_kb > 100:  # 100KB
                    warnings.append(f"Large response ({size_kb:.1f}KB). May impact context window.")
            except:
                pass
        
        # Check 2: Duplicate path segments (common bug)
        if isinstance(result, dict):
            path = result.get('path', '')
            if '/a2ia/a2ia/' in path or '/home/aaron/dev/nevelis/a2ia/a2ia/' in path:
                warnings.append(f"Path contains duplicate segments: {path}")
        
        # Check 3: Empty results when content expected
        if isinstance(result, dict):
            if result.get('success') and tool_name in ['read_file', 'grep', 'list_directory']:
                content_key = 'content' if tool_name == 'read_file' else 'matches' if tool_name == 'grep' else 'files'
                if not result.get(content_key):
                    warnings.append(f"Tool succeeded but returned no {content_key}")
        
        return warnings
    
    def get_tool_suggestions(self, invalid_tool_name: str) -> List[str]:
        """Get suggestions for invalid tool names."""
        from difflib import get_close_matches
        
        available = list(self.tool_schemas.keys())
        matches = get_close_matches(invalid_tool_name, available, n=3, cutoff=0.6)
        return matches


class ToolThrottler:
    """Prevent tool thrashing and repeated failures."""
    
    def __init__(self):
        self.call_history: List[Tuple[float, str]] = []  # (timestamp, tool_name)
        self.failed_tools: Dict[str, int] = defaultdict(int)  # tool_name -> failure_count
        self.last_cleanup = time.time()
    
    def should_allow_call(self, tool_name: str) -> Tuple[bool, str]:
        """Check if tool call should be allowed.
        
        Returns:
            (allowed, reason) - reason is empty if allowed
        """
        self._cleanup_old_history()
        now = time.time()
        
        # Check 1: Consecutive failures
        if self.failed_tools[tool_name] >= 3:
            return False, f"⚠️  Tool '{tool_name}' has failed 3+ times in a row. Skipping to prevent thrashing."
        
        # Check 2: Too many calls to same tool in short period
        recent_same_tool = [
            t for ts, t in self.call_history 
            if now - ts < 10 and t == tool_name
        ]
        if len(recent_same_tool) >= 5:
            return False, f"⚠️  Tool '{tool_name}' called 5+ times in 10 seconds. Throttled."
        
        # Check 3: Overall call rate
        recent_all_tools = [
            t for ts, t in self.call_history 
            if now - ts < 5
        ]
        if len(recent_all_tools) >= 10:
            return False, "⚠️  Too many tool calls (10+ in 5 seconds). Throttling to prevent runaway execution."
        
        return True, ""
    
    def record_call(self, tool_name: str, success: bool):
        """Record tool call result."""
        now = time.time()
        self.call_history.append((now, tool_name))
        
        if not success:
            self.failed_tools[tool_name] += 1
        else:
            # Reset failure count on success
            self.failed_tools[tool_name] = 0
    
    def reset_tool_failures(self, tool_name: Optional[str] = None):
        """Reset failure tracking for a tool or all tools."""
        if tool_name:
            self.failed_tools[tool_name] = 0
        else:
            self.failed_tools.clear()
    
    def _cleanup_old_history(self):
        """Clean up history older than 60 seconds."""
        now = time.time()
        # Only cleanup every 10 seconds to avoid overhead
        if now - self.last_cleanup < 10:
            return
        
        self.call_history = [
            (ts, t) for ts, t in self.call_history 
            if now - ts < 60
        ]
        self.last_cleanup = now
    
    def get_stats(self) -> Dict[str, Any]:
        """Get throttling statistics."""
        now = time.time()
        recent = [t for ts, t in self.call_history if now - ts < 60]
        
        tool_counts = defaultdict(int)
        for tool in recent:
            tool_counts[tool] += 1
        
        return {
            'total_calls_last_60s': len(recent),
            'tools_with_failures': {k: v for k, v in self.failed_tools.items() if v > 0},
            'most_called_tools': sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }

