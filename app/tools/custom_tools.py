# app/tools/custom_tools.py
"""
Custom Tools System untuk AI Agent
Provides tools untuk:
- File operations (read, write, create, delete)
- Directory operations (list, create, delete)
- Text processing (search, replace)
- Data operations (parse JSON, CSV, etc)
"""

import os
import json
import re
from pathlib import Path
from app.utils import FileManager


class CustomTools:
    """
    Main Tool Manager untuk AI Agent
    Handles routing & execution dari berbagai tools
    """

    def __init__(self):
        self.fm = FileManager()
        self.path_schema = "app/data/tools_schema/schema.json"

        # Mapping tool_name -> handler function
        self.tools_map = {
            # File Operations
            "create_file": self._handle_create_file,
            "read_file": self._handle_read_file,
            "write_file": self._handle_write_file,
            "append_file": self._handle_append_file,
            "delete_file": self._handle_delete_file,
            "file_exists": self._handle_file_exists,
            # Directory Operations
            "list_directory": self._handle_list_directory,
            "create_directory": self._handle_create_directory,
            "delete_directory": self._handle_delete_directory,
            # Text Operations
            "search_in_file": self._handle_search_in_file,
            "replace_in_file": self._handle_replace_in_file,
            "count_lines": self._handle_count_lines,
            "read_lines": self._handle_read_lines,
            # Data Operations
            "parse_json": self._handle_parse_json,
            "write_json": self._handle_write_json,
            "merge_json": self._handle_merge_json,
        }

    # =====================================
    # MAIN ENTRY
    # =====================================
    def execute_tool(self, tool_name, args):
        """
        Main entry point untuk execute tool

        Args:
            tool_name (str): Nama tool yang akan dijalankan
            args (dict): Arguments untuk tool

        Returns:
            dict: Response dengan status & data
        """
        if tool_name not in self.tools_map:
            return {
                "status": "error",
                "message": f"Tool '{tool_name}' not found",
                "available_tools": list(self.tools_map.keys()),
            }

        try:
            handler = self.tools_map[tool_name]
            result = handler(args)
            return self._format_success(result, tool_name)
        except Exception as e:
            return self._format_error(str(e), tool_name, args)

    # =====================================
    # FILE OPERATIONS HANDLERS
    # =====================================
    def _handle_create_file(self, args):
        """Create new file"""
        filepath = args.get("filepath")
        content = args.get("content", "")
        overwrite = args.get("overwrite", False)

        if not overwrite and os.path.exists(filepath):
            return {"created": False, "reason": "File already exists"}

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {"created": True, "filepath": filepath, "size": len(content)}

    def _handle_read_file(self, args):
        """Read file content"""
        filepath = args.get("filepath")
        start_line = args.get("start_line")
        end_line = args.get("end_line")

        if not os.path.exists(filepath):
            return {"error": "File not found"}

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # If range specified, return subset
        if start_line is not None and end_line is not None:
            start_line = max(0, start_line - 1)  # Convert to 0-indexed
            end_line = min(len(lines), end_line)
            content = "".join(lines[start_line:end_line])
            return {
                "content": content,
                "total_lines": len(lines),
                "returned_lines": end_line - start_line,
                "range": f"{start_line + 1}-{end_line}",
            }

        # Return all
        content = "".join(lines)
        return {"content": content, "total_lines": len(lines), "size": len(content)}

    def _handle_write_file(self, args):
        """Write content to file (overwrite)"""
        filepath = args.get("filepath")
        content = args.get("content")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {"written": True, "filepath": filepath, "size": len(content)}

    def _handle_append_file(self, args):
        """Append content to file"""
        filepath = args.get("filepath")
        content = args.get("content")

        if not os.path.exists(filepath):
            return {"error": "File not found"}

        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content)

        return {"appended": True, "filepath": filepath, "added_size": len(content)}

    def _handle_delete_file(self, args):
        """Delete file"""
        filepath = args.get("filepath")
        safe = args.get("safe", True)

        if not os.path.exists(filepath):
            return {"error": "File not found"}

        os.remove(filepath)
        return {"deleted": True, "filepath": filepath}

    def _handle_file_exists(self, args):
        """Check if file exists"""
        filepath = args.get("filepath")
        exists = os.path.exists(filepath)

        result = {"filepath": filepath, "exists": exists}
        if exists:
            result["size"] = os.path.getsize(filepath)

        return result

    # =====================================
    # DIRECTORY OPERATIONS HANDLERS
    # =====================================
    def _handle_list_directory(self, args):
        """List directory contents"""
        dirpath = args.get("dirpath", ".")
        only_files = args.get("only_files", False)
        recursive = args.get("recursive", False)

        if not os.path.exists(dirpath):
            return {"error": "Directory not found"}

        items = []

        if recursive:
            for root, dirs, files in os.walk(dirpath):
                if not only_files:
                    for d in dirs:
                        items.append(
                            {
                                "name": d,
                                "type": "directory",
                                "path": os.path.join(root, d),
                            }
                        )
                for f in files:
                    items.append(
                        {"name": f, "type": "file", "path": os.path.join(root, f)}
                    )
        else:
            for item in os.listdir(dirpath):
                path = os.path.join(dirpath, item)
                if os.path.isdir(path):
                    if not only_files:
                        items.append({"name": item, "type": "directory", "path": path})
                else:
                    items.append({"name": item, "type": "file", "path": path})

        return {"dirpath": dirpath, "count": len(items), "items": items}

    def _handle_create_directory(self, args):
        """Create directory"""
        dirpath = args.get("dirpath")

        if os.path.exists(dirpath):
            return {"created": False, "reason": "Directory already exists"}

        os.makedirs(dirpath, exist_ok=True)
        return {"created": True, "dirpath": dirpath}

    def _handle_delete_directory(self, args):
        """Delete directory (recursive)"""
        dirpath = args.get("dirpath")

        if not os.path.exists(dirpath):
            return {"error": "Directory not found"}

        import shutil

        shutil.rmtree(dirpath)
        return {"deleted": True, "dirpath": dirpath}

    # =====================================
    # TEXT OPERATIONS HANDLERS
    # =====================================
    def _handle_search_in_file(self, args):
        """Search pattern in file"""
        filepath = args.get("filepath")
        pattern = args.get("pattern")
        regex = args.get("regex", False)

        if not os.path.exists(filepath):
            return {"error": "File not found"}

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        results = []

        for idx, line in enumerate(lines, 1):
            try:
                if regex:
                    if re.search(pattern, line):
                        results.append({"line_number": idx, "content": line.rstrip()})
                else:
                    if pattern in line:
                        results.append({"line_number": idx, "content": line.rstrip()})
            except re.error as e:
                return {"error": f"Regex error: {str(e)}"}

        return {
            "filepath": filepath,
            "pattern": pattern,
            "matches": len(results),
            "results": results,
        }

    def _handle_replace_in_file(self, args):
        """Replace pattern in file"""
        filepath = args.get("filepath")
        pattern = args.get("pattern")
        replacement = args.get("replacement")
        regex = args.get("regex", False)

        if not os.path.exists(filepath):
            return {"error": "File not found"}

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            if regex:
                new_content = re.sub(pattern, replacement, content)
            else:
                new_content = content.replace(pattern, replacement)

            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)

                replaced_count = (
                    content.count(pattern)
                    if not regex
                    else len(re.findall(pattern, content))
                )
                return {
                    "replaced": True,
                    "filepath": filepath,
                    "replacements": replaced_count,
                }
            else:
                return {"replaced": False, "reason": "Pattern not found"}

        except re.error as e:
            return {"error": f"Regex error: {str(e)}"}

    def _handle_count_lines(self, args):
        """Count lines in file"""
        filepath = args.get("filepath")

        if not os.path.exists(filepath):
            return {"error": "File not found"}

        with open(filepath, "r", encoding="utf-8") as f:
            lines = len(f.readlines())

        return {"filepath": filepath, "line_count": lines}

    def _handle_read_lines(self, args):
        """Read specific lines from file"""
        filepath = args.get("filepath")
        start = args.get("start", 1)  # 1-indexed
        end = args.get("end", 10)

        if not os.path.exists(filepath):
            return {"error": "File not found"}

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        start = max(1, start) - 1  # Convert to 0-indexed
        end = min(len(lines), end)

        extracted = lines[start:end]
        return {
            "filepath": filepath,
            "requested_range": f"{start + 1}-{end}",
            "lines": ["".join(extracted)],
            "line_count": len(extracted),
        }

    # =====================================
    # DATA OPERATIONS HANDLERS
    # =====================================
    def _handle_parse_json(self, args):
        """Parse JSON file"""
        filepath = args.get("filepath")

        if not os.path.exists(filepath):
            return {"error": "File not found"}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"parsed": True, "data": data}
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {str(e)}"}

    def _handle_write_json(self, args):
        """Write JSON to file"""
        filepath = args.get("filepath")
        data = args.get("data")
        pretty = args.get("pretty", True)

        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            return {"written": True, "filepath": filepath}
        except Exception as e:
            return {"error": str(e)}

    def _handle_merge_json(self, args):
        """Merge multiple JSON files"""
        filepaths = args.get("filepaths", [])
        output_filepath = args.get("output_filepath")

        merged = {}

        for filepath in filepaths:
            if not os.path.exists(filepath):
                return {"error": f"File not found: {filepath}"}

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    merged.update(data)
            except json.JSONDecodeError as e:
                return {"error": f"JSON parse error in {filepath}: {str(e)}"}

        if output_filepath:
            with open(output_filepath, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)
            return {"merged": True, "files": len(filepaths), "output": output_filepath}

        return {"merged": True, "files": len(filepaths), "data": merged}

    # =====================================
    # RESPONSE FORMATTERS
    # =====================================
    def _format_success(self, data, tool_name):
        """Format successful response"""
        return {"status": "success", "tool": tool_name, "data": data}

    def _format_error(self, error_msg, tool_name, args):
        """Format error response"""
        return {
            "status": "error",
            "tool": tool_name,
            "message": error_msg,
            "args": args,
        }

    def get_tools_schema(self):
        """Get schema untuk semua tools"""
        return {
            "tools": [
                {
                    "name": "create_file",
                    "description": "Create new file with content",
                    "parameters": {
                        "filepath": "string (required)",
                        "content": "string (optional, default: empty)",
                        "overwrite": "boolean (optional, default: false)",
                    },
                },
                {
                    "name": "read_file",
                    "description": "Read file content",
                    "parameters": {
                        "filepath": "string (required)",
                        "start_line": "integer (optional)",
                        "end_line": "integer (optional)",
                    },
                },
                {
                    "name": "write_file",
                    "description": "Write/overwrite file content",
                    "parameters": {
                        "filepath": "string (required)",
                        "content": "string (required)",
                    },
                },
                {
                    "name": "append_file",
                    "description": "Append content to file",
                    "parameters": {
                        "filepath": "string (required)",
                        "content": "string (required)",
                    },
                },
                {
                    "name": "delete_file",
                    "description": "Delete file",
                    "parameters": {
                        "filepath": "string (required)",
                        "safe": "boolean (optional, default: true)",
                    },
                },
                {
                    "name": "search_in_file",
                    "description": "Search pattern in file",
                    "parameters": {
                        "filepath": "string (required)",
                        "pattern": "string (required)",
                        "regex": "boolean (optional, default: false)",
                    },
                },
                {
                    "name": "replace_in_file",
                    "description": "Replace pattern in file",
                    "parameters": {
                        "filepath": "string (required)",
                        "pattern": "string (required)",
                        "replacement": "string (required)",
                        "regex": "boolean (optional, default: false)",
                    },
                },
                {
                    "name": "list_directory",
                    "description": "List directory contents",
                    "parameters": {
                        "dirpath": "string (optional, default: '.')",
                        "only_files": "boolean (optional, default: false)",
                        "recursive": "boolean (optional, default: false)",
                    },
                },
            ]
        }
