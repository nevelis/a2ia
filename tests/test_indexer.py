"""Tests for file indexing and line-range reading functionality."""

import pytest
from pathlib import Path
from a2ia.tools.indexer import (
    FileIndexer,
    PythonParser,
    JavaScriptParser,
    TerraformParser,
    Symbol,
    FileIndex,
)
from a2ia.tools.filesystem_tools import index_file, read_file_lines
from a2ia.workspace import Workspace


# Sample file contents for testing
PYTHON_SAMPLE = '''"""Module docstring."""

MODULE_VAR = "test"
DEBUG = True

class MyClass:
    """Class docstring."""
    
    def __init__(self, value):
        self.value = value
    
    def method_one(self, arg1, arg2):
        return arg1 + arg2
    
    async def async_method(self):
        return "async"

def standalone_function(param1, param2):
    """Function docstring."""
    return param1 * param2

async def async_function():
    pass

class AnotherClass:
    pass
'''

JAVASCRIPT_SAMPLE = '''// JavaScript sample
export const CONFIG = {
  key: "value"
};

class MyComponent {
  constructor(props) {
    this.props = props;
  }
  
  render() {
    return null;
  }
  
  async fetchData() {
    return fetch('/api');
  }
}

function regularFunction(a, b) {
  return a + b;
}

const arrowFunction = (x, y) => {
  return x * y;
};

export async function asyncFunction() {
  return await Promise.resolve();
}

export class ExportedClass {
  method() {}
}
'''

TERRAFORM_SAMPLE = '''variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

locals {
  common_tags = {
    Environment = "dev"
    Terraform   = "true"
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  
  tags = local.common_tags
}

resource "aws_security_group" "web_sg" {
  name = "web-sg"
  
  ingress {
    from_port = 80
    to_port   = 80
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
}

output "instance_ip" {
  value = aws_instance.web.public_ip
}

module "vpc" {
  source = "./modules/vpc"
  cidr   = "10.0.0.0/16"
}
'''


class TestPythonParser:
    """Test Python file parsing."""
    
    def test_parse_python_classes(self):
        parser = PythonParser()
        symbols = parser.parse(PYTHON_SAMPLE)
        
        # Check classes
        classes = [s for s in symbols if s.type == 'class']
        assert len(classes) == 2
        assert classes[0].name == 'MyClass'
        assert classes[1].name == 'AnotherClass'
    
    def test_parse_python_functions(self):
        parser = PythonParser()
        symbols = parser.parse(PYTHON_SAMPLE)
        
        # Check standalone functions
        functions = [s for s in symbols if s.type == 'function']
        assert len(functions) == 2
        assert any(s.name == 'standalone_function' for s in functions)
        assert any(s.name == 'async_function' for s in functions)
    
    def test_parse_python_methods(self):
        parser = PythonParser()
        symbols = parser.parse(PYTHON_SAMPLE)
        
        # Check methods
        methods = [s for s in symbols if s.type == 'method']
        assert len(methods) >= 3  # __init__, method_one, async_method
        assert any(s.name == '__init__' and s.parent == 'MyClass' for s in methods)
        assert any(s.name == 'method_one' and s.parent == 'MyClass' for s in methods)
        assert any(s.name == 'async_method' and s.parent == 'MyClass' for s in methods)
    
    def test_parse_python_module_variables(self):
        parser = PythonParser()
        symbols = parser.parse(PYTHON_SAMPLE)
        
        # Check module-level variables
        variables = [s for s in symbols if s.type == 'variable']
        assert len(variables) >= 2
        assert any(s.name == 'MODULE_VAR' for s in variables)
        assert any(s.name == 'DEBUG' for s in variables)
    
    def test_parse_python_with_signatures(self):
        parser = PythonParser()
        symbols = parser.parse(PYTHON_SAMPLE)
        
        # Check that functions have signatures
        func = next(s for s in symbols if s.name == 'standalone_function')
        assert func.signature == '(param1, param2)'
    
    def test_parse_python_line_numbers(self):
        parser = PythonParser()
        symbols = parser.parse(PYTHON_SAMPLE)
        
        # Verify line numbers are captured
        my_class = next(s for s in symbols if s.name == 'MyClass')
        assert my_class.start_line > 0
        assert my_class.end_line >= my_class.start_line


class TestJavaScriptParser:
    """Test JavaScript file parsing."""
    
    def test_parse_javascript_classes(self):
        parser = JavaScriptParser()
        symbols = parser.parse(JAVASCRIPT_SAMPLE)
        
        classes = [s for s in symbols if s.type == 'class']
        assert len(classes) == 2
        assert any(s.name == 'MyComponent' for s in classes)
        assert any(s.name == 'ExportedClass' for s in classes)
    
    def test_parse_javascript_functions(self):
        parser = JavaScriptParser()
        symbols = parser.parse(JAVASCRIPT_SAMPLE)
        
        functions = [s for s in symbols if s.type == 'function']
        assert len(functions) >= 3  # regularFunction, arrowFunction, asyncFunction
        assert any(s.name == 'regularFunction' for s in functions)
        assert any(s.name == 'arrowFunction' for s in functions)
        assert any(s.name == 'asyncFunction' for s in functions)
    
    def test_parse_javascript_methods(self):
        parser = JavaScriptParser()
        symbols = parser.parse(JAVASCRIPT_SAMPLE)
        
        methods = [s for s in symbols if s.type == 'method']
        # Should find constructor, render, fetchData, and method from ExportedClass
        assert len(methods) >= 3
        assert any(s.name == 'render' and s.parent == 'MyComponent' for s in methods)
    
    def test_parse_javascript_constants(self):
        parser = JavaScriptParser()
        symbols = parser.parse(JAVASCRIPT_SAMPLE)
        
        variables = [s for s in symbols if s.type == 'variable']
        assert any(s.name == 'CONFIG' for s in variables)
    
    def test_can_parse_js_extensions(self):
        parser = JavaScriptParser()
        assert parser.can_parse("test.js", "")
        assert parser.can_parse("test.jsx", "")
        assert parser.can_parse("test.ts", "")
        assert parser.can_parse("test.tsx", "")
        assert not parser.can_parse("test.py", "")


class TestTerraformParser:
    """Test Terraform file parsing."""
    
    def test_parse_terraform_resources(self):
        parser = TerraformParser()
        symbols = parser.parse(TERRAFORM_SAMPLE)
        
        resources = [s for s in symbols if s.type == 'resource']
        assert len(resources) == 2
        assert any(s.name == 'web' and s.signature == 'aws_instance' for s in resources)
        assert any(s.name == 'web_sg' and s.signature == 'aws_security_group' for s in resources)
    
    def test_parse_terraform_variables(self):
        parser = TerraformParser()
        symbols = parser.parse(TERRAFORM_SAMPLE)
        
        variables = [s for s in symbols if s.type == 'variable']
        assert len(variables) == 2
        assert any(s.name == 'instance_type' for s in variables)
        assert any(s.name == 'region' for s in variables)
    
    def test_parse_terraform_outputs(self):
        parser = TerraformParser()
        symbols = parser.parse(TERRAFORM_SAMPLE)
        
        outputs = [s for s in symbols if s.type == 'output']
        assert len(outputs) == 1
        assert outputs[0].name == 'instance_ip'
    
    def test_parse_terraform_data_sources(self):
        parser = TerraformParser()
        symbols = parser.parse(TERRAFORM_SAMPLE)
        
        data_sources = [s for s in symbols if s.type == 'data']
        assert len(data_sources) == 1
        assert data_sources[0].name == 'ubuntu'
        assert data_sources[0].signature == 'aws_ami'
    
    def test_parse_terraform_modules(self):
        parser = TerraformParser()
        symbols = parser.parse(TERRAFORM_SAMPLE)
        
        modules = [s for s in symbols if s.type == 'module']
        assert len(modules) == 1
        assert modules[0].name == 'vpc'
    
    def test_parse_terraform_locals(self):
        parser = TerraformParser()
        symbols = parser.parse(TERRAFORM_SAMPLE)
        
        locals_blocks = [s for s in symbols if s.type == 'locals']
        assert len(locals_blocks) == 1
        assert locals_blocks[0].name == 'locals'


class TestFileIndexer:
    """Test the main FileIndexer class."""
    
    def test_index_python_file(self, tmp_path):
        # Create a test Python file
        test_file = tmp_path / "test.py"
        test_file.write_text(PYTHON_SAMPLE)
        
        indexer = FileIndexer()
        index = indexer.index_file(str(test_file))
        
        assert index.language == "python"
        assert index.size_bytes > 0
        assert index.total_lines > 0
        assert len(index.symbols) > 0
        assert index.path == str(test_file)
    
    def test_index_javascript_file(self, tmp_path):
        test_file = tmp_path / "test.js"
        test_file.write_text(JAVASCRIPT_SAMPLE)
        
        indexer = FileIndexer()
        index = indexer.index_file(str(test_file))
        
        assert index.language == "javascript"
        assert len(index.symbols) > 0
    
    def test_index_terraform_file(self, tmp_path):
        test_file = tmp_path / "test.tf"
        test_file.write_text(TERRAFORM_SAMPLE)
        
        indexer = FileIndexer()
        index = indexer.index_file(str(test_file))
        
        assert index.language == "terraform"
        assert len(index.symbols) > 0
    
    def test_index_unknown_file(self, tmp_path):
        test_file = tmp_path / "test.xyz"
        test_file.write_text("some content")
        
        indexer = FileIndexer()
        index = indexer.index_file(str(test_file))
        
        assert index.language == "unknown"
        assert index.size_bytes > 0
        assert index.total_lines > 0
        assert len(index.symbols) == 0
    
    def test_file_metadata(self, tmp_path):
        content = "Line 1\nLine 2\nLine 3"
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)
        
        indexer = FileIndexer()
        index = indexer.index_file(str(test_file))
        
        assert index.total_lines == 3
        assert index.size_bytes == len(content.encode('utf-8'))


class TestWorkspaceLineReading:
    """Test line-range reading in Workspace class."""
    
    def test_read_file_lines_basic(self, tmp_path):
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)
        
        ws = Workspace(tmp_path)
        result = ws.read_file_lines("test.txt", start_line=2, end_line=4)
        
        assert result["success"]
        assert result["lines"] == ["Line 2", "Line 3", "Line 4"]
        assert result["start_line"] == 2
        assert result["end_line"] == 4
        assert result["total_lines"] == 5
        assert result["count"] == 3
    
    def test_read_file_lines_to_end(self, tmp_path):
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)
        
        ws = Workspace(tmp_path)
        result = ws.read_file_lines("test.txt", start_line=3, end_line=-1)
        
        assert result["success"]
        assert result["lines"] == ["Line 3", "Line 4", "Line 5"]
        assert result["end_line"] == 5
    
    def test_read_file_lines_single_line(self, tmp_path):
        content = "Line 1\nLine 2\nLine 3"
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)
        
        ws = Workspace(tmp_path)
        result = ws.read_file_lines("test.txt", start_line=2, end_line=2)
        
        assert result["success"]
        assert result["lines"] == ["Line 2"]
        assert result["count"] == 1
    
    def test_read_file_lines_entire_file(self, tmp_path):
        content = "Line 1\nLine 2\nLine 3"
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)
        
        ws = Workspace(tmp_path)
        result = ws.read_file_lines("test.txt", start_line=1, end_line=-1)
        
        assert result["success"]
        assert result["lines"] == ["Line 1", "Line 2", "Line 3"]
        assert result["total_lines"] == 3
    
    def test_read_file_lines_out_of_bounds(self, tmp_path):
        content = "Line 1\nLine 2\nLine 3"
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)
        
        ws = Workspace(tmp_path)
        
        # End line beyond file
        result = ws.read_file_lines("test.txt", start_line=2, end_line=100)
        assert result["end_line"] == 3
        assert result["lines"] == ["Line 2", "Line 3"]
        
        # Start line at 0
        result = ws.read_file_lines("test.txt", start_line=0, end_line=2)
        assert result["start_line"] == 1
        assert result["lines"] == ["Line 1", "Line 2"]


@pytest.mark.asyncio
class TestIndexFileTool:
    """Test the index_file MCP tool."""
    
    async def test_index_file_tool_python(self, sandbox_ws):
        # Create test file
        test_file = Path(sandbox_ws.path) / "test.py"
        test_file.write_text(PYTHON_SAMPLE)
        
        # Call the tool
        result = await index_file("test.py")
        
        import json
        data = json.loads(result)
        
        assert data["success"]
        assert data["language"] == "python"
        assert data["total_lines"] > 0
        assert len(data["symbols"]) > 0
        
        # Check that we found classes
        classes = [s for s in data["symbols"] if s["type"] == "class"]
        assert len(classes) > 0
    
    async def test_index_file_tool_javascript(self, sandbox_ws):
        test_file = Path(sandbox_ws.path) / "test.js"
        test_file.write_text(JAVASCRIPT_SAMPLE)
        
        result = await index_file("test.js")
        
        import json
        data = json.loads(result)
        
        assert data["success"]
        assert data["language"] == "javascript"
        assert len(data["symbols"]) > 0
    
    async def test_index_file_tool_terraform(self, sandbox_ws):
        test_file = Path(sandbox_ws.path) / "main.tf"
        test_file.write_text(TERRAFORM_SAMPLE)
        
        result = await index_file("main.tf")
        
        import json
        data = json.loads(result)
        
        assert data["success"]
        assert data["language"] == "terraform"
        
        # Check for resources
        resources = [s for s in data["symbols"] if s["type"] == "resource"]
        assert len(resources) > 0
    
    async def test_index_file_tool_error(self, sandbox_ws):
        # Try to index non-existent file
        result = await index_file("nonexistent.py")
        
        import json
        data = json.loads(result)
        
        assert not data["success"]
        assert "error" in data


@pytest.mark.asyncio
class TestReadFileLinesTools:
    """Test the read_file_lines MCP tool."""
    
    async def test_read_file_lines_tool(self, sandbox_ws):
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        test_file = Path(sandbox_ws.path) / "test.txt"
        test_file.write_text(content)
        
        result = await read_file_lines("test.txt", start_line=2, end_line=4)
        
        assert result["success"]
        assert result["lines"] == ["Line 2", "Line 3", "Line 4"]
        assert result["count"] == 3


@pytest.mark.asyncio
class TestIndexAndReadWorkflow:
    """Test the workflow of indexing a file then reading specific parts."""
    
    async def test_index_then_read_python_class(self, sandbox_ws):
        # Create a larger Python file
        test_file = Path(sandbox_ws.path) / "mymodule.py"
        test_file.write_text(PYTHON_SAMPLE)
        
        # Step 1: Index the file
        index_result = await index_file("mymodule.py")
        import json
        index_data = json.loads(index_result)
        
        assert index_data["success"]
        
        # Step 2: Find MyClass in the index
        my_class = next(
            s for s in index_data["symbols"] 
            if s["name"] == "MyClass" and s["type"] == "class"
        )
        
        # Step 3: Read just the class definition
        lines_result = await read_file_lines(
            "mymodule.py",
            start_line=my_class["start_line"],
            end_line=my_class["end_line"]
        )
        
        assert lines_result["success"]
        assert "class MyClass:" in lines_result["lines"][0]
    
    async def test_index_then_read_terraform_resource(self, sandbox_ws):
        test_file = Path(sandbox_ws.path) / "main.tf"
        test_file.write_text(TERRAFORM_SAMPLE)
        
        # Index
        index_result = await index_file("main.tf")
        import json
        index_data = json.loads(index_result)
        
        # Find a resource
        web_resource = next(
            s for s in index_data["symbols"]
            if s["name"] == "web" and s["type"] == "resource"
        )
        
        # Read the resource block
        lines_result = await read_file_lines(
            "main.tf",
            start_line=web_resource["start_line"],
            end_line=web_resource["end_line"]
        )
        
        assert lines_result["success"]
        assert "aws_instance" in lines_result["lines"][0]
