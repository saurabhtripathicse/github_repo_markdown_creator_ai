"""
Test Markdown Formatter

This module tests the markdown formatter functionality.
"""

import os
import sys
import unittest
import tempfile
import shutil

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.markdown_formatter import MarkdownFormatter, format_markdown_files

class TestMarkdownFormatter(unittest.TestCase):
    """Test the markdown formatter functionality"""
    
    def setUp(self):
        """Set up the test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.formatter = MarkdownFormatter()
    
    def tearDown(self):
        """Clean up the test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_heading_spacing(self):
        """Test that headings have proper spacing"""
        # Create a test file with improper heading spacing
        test_content = "# Heading 1\nSome text\n## Heading 2\nMore text"
        test_file = os.path.join(self.test_dir, "test_heading_spacing.md")
        
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Format the file
        self.formatter.format_file(test_file)
        
        # Read the formatted content
        with open(test_file, "r", encoding="utf-8") as f:
            formatted_content = f.read()
        
        # Check that headings have proper spacing
        self.assertIn("# Heading 1\n\nSome text\n\n## Heading 2\n\nMore text", formatted_content)
    
    def test_multiple_h1(self):
        """Test that multiple H1 headings are fixed"""
        # Create a test file with multiple H1 headings
        test_content = "# Heading 1\nSome text\n# Another H1\nMore text"
        test_file = os.path.join(self.test_dir, "test_multiple_h1.md")
        
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Format the file
        self.formatter.format_file(test_file)
        
        # Read the formatted content
        with open(test_file, "r", encoding="utf-8") as f:
            formatted_content = f.read()
        
        # Check that the second H1 is converted to H2
        self.assertIn("# Heading 1", formatted_content)
        self.assertIn("## Another H1", formatted_content)
    
    def test_heading_increment(self):
        """Test that heading increments are fixed"""
        # Create a test file with improper heading increments
        test_content = "# Heading 1\nSome text\n### Heading 3\nMore text"
        test_file = os.path.join(self.test_dir, "test_heading_increment.md")
        
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Format the file
        self.formatter.format_file(test_file)
        
        # Read the formatted content
        with open(test_file, "r", encoding="utf-8") as f:
            formatted_content = f.read()
        
        # Check that heading increments are fixed
        self.assertIn("# Heading 1", formatted_content)
        self.assertIn("## Heading 3", formatted_content)
    
    def test_code_block_spacing(self):
        """Test that code blocks have proper spacing"""
        # Create a test file with improper code block spacing
        test_content = "Some text\n```python\ndef hello():\n    print('Hello')\n```\nMore text"
        test_file = os.path.join(self.test_dir, "test_code_block_spacing.md")
        
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Format the file
        self.formatter.format_file(test_file)
        
        # Read the formatted content
        with open(test_file, "r", encoding="utf-8") as f:
            formatted_content = f.read()
        
        # Check that code blocks have proper spacing
        self.assertIn("Some text\n\n```python\ndef hello():\n    print('Hello')\n```\n\nMore text", formatted_content)
    
    def test_format_directory(self):
        """Test formatting a directory of markdown files"""
        # Create multiple test files
        files = {
            "file1.md": "# Heading 1\nSome text",
            "file2.md": "# Heading 2\nMore text",
            "not_markdown.txt": "Not a markdown file"
        }
        
        for filename, content in files.items():
            file_path = os.path.join(self.test_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        # Format the directory
        results = format_markdown_files(self.test_dir, recursive=True)
        
        # Check that only markdown files were formatted
        self.assertEqual(len(results), 2)
        self.assertTrue(results[os.path.join(self.test_dir, "file1.md")])
        self.assertTrue(results[os.path.join(self.test_dir, "file2.md")])
        
        # Check that the non-markdown file was not modified
        with open(os.path.join(self.test_dir, "not_markdown.txt"), "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "Not a markdown file")

if __name__ == "__main__":
    unittest.main()
