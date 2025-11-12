"""File indexing system with pluggable language parsers.

Provides structural analysis of source code files without loading entire content.
Supports Python, JavaScript, Terraform, and extensible to other languages.
"""

import ast
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Symbol:
    """Represents a code symbol (function, class, variable, etc.)."""
    name: str
    type: str  # 'function', 'class', 'method', 'variable', 'resource', etc.
    start_line: int
    end_line: int
    parent: Optional[str] = None  # Parent class/module name
    signature: Optional[str] = None  # Function signature, type annotation, etc.


@dataclass
class FileIndex:
    """Complete index of a file's structure."""
    path: str
    size_bytes: int
    total_lines: int
    symbols: List[Symbol]
    language: str
    encoding: str = "utf-8"


class LanguageParser(ABC):
    """Abstract base class for language-specific parsers."""
    
    @abstractmethod
    def can_parse(self, path: str, content: str) -> bool:
        """Return True if this parser can handle the file."""
        pass
    
    @abstractmethod
    def parse(self, content: str) -> List[Symbol]:
        """Parse content and return list of symbols."""
        pass
    
    @abstractmethod
    def language_name(self) -> str:
        """Return the language name."""
        pass


class PythonParser(LanguageParser):
    """Parser for Python files using AST."""
    
    def can_parse(self, path: str, content: str) -> bool:
        return path.endswith('.py')
    
    def language_name(self) -> str:
        return "python"
    
    def parse(self, content: str) -> List[Symbol]:
        symbols = []
        try:
            tree = ast.parse(content)
            self._visit_node(tree, symbols, None)
        except SyntaxError:
            # If AST parsing fails, fall back to regex
            symbols = self._regex_parse(content)
        return symbols
    
    def _visit_node(self, node: ast.AST, symbols: List[Symbol], parent: Optional[str] = None):
        """Recursively visit AST nodes and extract symbols."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                symbols.append(Symbol(
                    name=child.name,
                    type='class',
                    start_line=child.lineno,
                    end_line=child.end_lineno or child.lineno,
                    parent=parent
                ))
                # Visit class members
                self._visit_node(child, symbols, parent=child.name)
            
            elif isinstance(child, ast.FunctionDef) or isinstance(child, ast.AsyncFunctionDef):
                func_type = 'method' if parent else 'function'
                signature = self._get_function_signature(child)
                symbols.append(Symbol(
                    name=child.name,
                    type=func_type,
                    start_line=child.lineno,
                    end_line=child.end_lineno or child.lineno,
                    parent=parent,
                    signature=signature
                ))
            
            elif isinstance(child, ast.Assign) and not parent:
                # Module-level assignments
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        symbols.append(Symbol(
                            name=target.id,
                            type='variable',
                            start_line=child.lineno,
                            end_line=child.end_lineno or child.lineno,
                            parent=None
                        ))
            
            elif isinstance(child, ast.AnnAssign) and not parent:
                # Module-level annotated assignments
                if isinstance(child.target, ast.Name):
                    symbols.append(Symbol(
                        name=child.target.id,
                        type='variable',
                        start_line=child.lineno,
                        end_line=child.end_lineno or child.lineno,
                        parent=None
                    ))
    
    def _get_function_signature(self, node) -> str:
        """Extract function signature from AST node."""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        return f"({', '.join(args)})"
    
    def _regex_parse(self, content: str) -> List[Symbol]:
        """Fallback regex-based parsing for malformed Python."""
        symbols = []
        lines = content.split('\n')
        
        class_pattern = re.compile(r'^class\s+(\w+)')
        func_pattern = re.compile(r'^(?:async\s+)?def\s+(\w+)\s*\((.*?)\)')
        
        for i, line in enumerate(lines, 1):
            if match := class_pattern.match(line):
                symbols.append(Symbol(
                    name=match.group(1),
                    type='class',
                    start_line=i,
                    end_line=i  # Can't determine end without full parse
                ))
            elif match := func_pattern.match(line):
                symbols.append(Symbol(
                    name=match.group(1),
                    type='function',
                    start_line=i,
                    end_line=i,
                    signature=f"({match.group(2)})"
                ))
        
        return symbols


class JavaScriptParser(LanguageParser):
    """Parser for JavaScript/TypeScript files using regex."""
    
    def can_parse(self, path: str, content: str) -> bool:
        return path.endswith(('.js', '.jsx', '.ts', '.tsx'))
    
    def language_name(self) -> str:
        return "javascript"
    
    def parse(self, content: str) -> List[Symbol]:
        symbols = []
        lines = content.split('\n')
        
        # Patterns for various JS constructs
        class_pattern = re.compile(r'^\s*(?:export\s+)?class\s+(\w+)')
        func_pattern = re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\((.*?)\)')
        arrow_pattern = re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>')
        method_pattern = re.compile(r'^\s*(?:async\s+)?(\w+)\s*\((.*?)\)\s*\{')
        const_pattern = re.compile(r'^\s*(?:export\s+)?const\s+(\w+)\s*=')
        
        current_class = None
        brace_depth = 0
        
        for i, line in enumerate(lines, 1):
            # Track class scope with braces
            brace_depth += line.count('{') - line.count('}')
            
            # Check each pattern in order
            match = class_pattern.match(line)
            if match:
                current_class = match.group(1)
                symbols.append(Symbol(
                    name=current_class,
                    type='class',
                    start_line=i,
                    end_line=i  # Will be updated when we find end
                ))
                continue
            
            match = func_pattern.match(line)
            if match:
                symbols.append(Symbol(
                    name=match.group(1),
                    type='function',
                    start_line=i,
                    end_line=i,
                    signature=f"({match.group(2)})"
                ))
                continue
            
            match = arrow_pattern.match(line)
            if match:
                symbols.append(Symbol(
                    name=match.group(1),
                    type='function',
                    start_line=i,
                    end_line=i,
                    signature=f"({match.group(2)})"
                ))
                continue
            
            if current_class:
                match = method_pattern.match(line)
                if match:
                    # Method inside a class
                    symbols.append(Symbol(
                        name=match.group(1),
                        type='method',
                        start_line=i,
                        end_line=i,
                        parent=current_class,
                        signature=f"({match.group(2)})"
                    ))
                    continue
            
            if not current_class:
                match = const_pattern.match(line)
                if match:
                    # Module-level constant
                    symbols.append(Symbol(
                        name=match.group(1),
                        type='variable',
                        start_line=i,
                        end_line=i
                    ))
                    continue
            
            # Exit class scope
            if current_class and brace_depth == 0:
                current_class = None
        
        return symbols


class TerraformParser(LanguageParser):
    """Parser for Terraform (.tf) files using regex."""
    
    def can_parse(self, path: str, content: str) -> bool:
        return path.endswith('.tf')
    
    def language_name(self) -> str:
        return "terraform"
    
    def parse(self, content: str) -> List[Symbol]:
        symbols = []
        lines = content.split('\n')
        
        # Terraform block patterns
        resource_pattern = re.compile(r'^\s*resource\s+"([^"]+)"\s+"([^"]+)"')
        variable_pattern = re.compile(r'^\s*variable\s+"([^"]+)"')
        output_pattern = re.compile(r'^\s*output\s+"([^"]+)"')
        data_pattern = re.compile(r'^\s*data\s+"([^"]+)"\s+"([^"]+)"')
        module_pattern = re.compile(r'^\s*module\s+"([^"]+)"')
        locals_pattern = re.compile(r'^\s*locals\s*\{')
        
        brace_depth = 0
        current_block = None
        current_block_start = None
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Track brace depth for block boundaries
            prev_depth = brace_depth
            brace_depth += line.count('{') - line.count('}')
            
            if match := resource_pattern.match(line):
                resource_type = match.group(1)
                resource_name = match.group(2)
                symbols.append(Symbol(
                    name=resource_name,
                    type='resource',
                    start_line=i,
                    end_line=i,
                    signature=resource_type
                ))
                current_block = ('resource', i)
            
            elif match := variable_pattern.match(line):
                symbols.append(Symbol(
                    name=match.group(1),
                    type='variable',
                    start_line=i,
                    end_line=i
                ))
                current_block = ('variable', i)
            
            elif match := output_pattern.match(line):
                symbols.append(Symbol(
                    name=match.group(1),
                    type='output',
                    start_line=i,
                    end_line=i
                ))
                current_block = ('output', i)
            
            elif match := data_pattern.match(line):
                data_type = match.group(1)
                data_name = match.group(2)
                symbols.append(Symbol(
                    name=data_name,
                    type='data',
                    start_line=i,
                    end_line=i,
                    signature=data_type
                ))
                current_block = ('data', i)
            
            elif match := module_pattern.match(line):
                symbols.append(Symbol(
                    name=match.group(1),
                    type='module',
                    start_line=i,
                    end_line=i
                ))
                current_block = ('module', i)
            
            elif match := locals_pattern.match(line):
                symbols.append(Symbol(
                    name='locals',
                    type='locals',
                    start_line=i,
                    end_line=i
                ))
                current_block = ('locals', i)
            
            # Update end_line when block closes
            if current_block and brace_depth == 0 and prev_depth > 0:
                block_type, start_line = current_block
                # Find the symbol and update its end_line
                for symbol in symbols:
                    if symbol.start_line == start_line:
                        symbol.end_line = i
                        break
                current_block = None
        
        return symbols


class FileIndexer:
    """Main indexer that delegates to language-specific parsers."""
    
    def __init__(self):
        self.parsers: List[LanguageParser] = [
            PythonParser(),
            JavaScriptParser(),
            TerraformParser(),
        ]
    
    def register_parser(self, parser: LanguageParser):
        """Register a custom parser for additional language support."""
        self.parsers.append(parser)
    
    def index_file(self, path: str, content: Optional[str] = None, encoding: str = "utf-8") -> FileIndex:
        """Index a file and return its structural information.
        
        Args:
            path: File path
            content: Optional file content (will read from path if not provided)
            encoding: File encoding (default: utf-8)
        
        Returns:
            FileIndex with file metadata and symbol information
        """
        # Read file if content not provided
        if content is None:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
        
        # Get file metadata
        size_bytes = len(content.encode(encoding))
        total_lines = content.count('\n') + (1 if content and not content.endswith('\n') else 0)
        
        # Find appropriate parser
        parser = None
        for p in self.parsers:
            if p.can_parse(path, content):
                parser = p
                break
        
        # Parse if we have a parser, otherwise return basic index
        symbols = []
        language = "unknown"
        if parser:
            try:
                symbols = parser.parse(content)
                language = parser.language_name()
            except Exception:
                # If parsing fails, return empty symbol list
                pass
        
        return FileIndex(
            path=path,
            size_bytes=size_bytes,
            total_lines=total_lines,
            symbols=symbols,
            language=language,
            encoding=encoding
        )


# Global indexer instance
_indexer = FileIndexer()


def get_indexer() -> FileIndexer:
    """Get the global indexer instance."""
    return _indexer


def index_file(path: str, content: Optional[str] = None, encoding: str = "utf-8") -> FileIndex:
    """Convenience function to index a file using the global indexer."""
    return _indexer.index_file(path, content, encoding)
