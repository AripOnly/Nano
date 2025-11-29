# app/tools/tools_calling_manager.py

from app.utils import FileManager


class ToolsCalling:
    def __init__(self):
        self.path_schema = "app/data/tools_schema/schema.json"
        self.fm = FileManager()

        # Mapping tool_name -> handler function
        self.tools_map = {
            "create_file": self._handle_create_file,
            "read_file": self._handle_read_file,
            "write_file": self._handle_write_file,
            "append_to_file": self._handle_append_to_file,
            "delete_file": self._handle_delete_file,
            "list_directory": self._handle_list_directory,
            "move_file": self._handle_move_file,
        }

    # =====================================
    # SCHEMA HANDLER
    # =====================================
    def tools_schema(self):
        return self.fm.read_json(self.path_schema)

    # =====================================
    # MAIN ENTRY
    # =====================================
    def tools_calling(self, tool_name, arg):
        if tool_name not in self.tools_map:
            return {
                "status": "error",
                "message": f"Tool '{tool_name}' not found or not implemented.",
            }

        try:
            handler = self.tools_map[tool_name]
            raw_output = handler(arg)
            return self.format_tools_response(raw_output)

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "content": {"tool": tool_name, "args": arg},
            }

    # =====================================
    # TOOL HANDLERS (Modular)
    # =====================================
    def _handle_create_file(self, arg):
        return self.fm.create_file(
            arg.get("filepath"), arg.get("content"), arg.get("overwrite", False)
        )

    def _handle_read_file(self, arg):
        return self.fm.read_file(arg.get("filepath"))

    def _handle_write_file(self, arg):
        return self.fm.write_file(
            arg.get("filepath"), arg.get("content"), arg.get("safe_write", True)
        )

    def _handle_append_to_file(self, arg):
        return self.fm.append_file(arg.get("filepath"), arg.get("content"))

    def _handle_delete_file(self, arg):
        return self.fm.delete_file(arg.get("filepath"), arg.get("safe_delete", True))

    def _handle_list_directory(self, arg):
        return self.fm.list_directory(
            arg.get("dirpath"),
            arg.get("only_files", False),
            arg.get("filter_ext"),
            arg.get("recursive", False),
        )

    def _handle_move_file(self, arg):
        return self.fm.move_file(
            arg.get("src"), arg.get("dst"), arg.get("overwrite", False)
        )

    def format_tools_response(self, response):
        if isinstance(response, dict):
            return response
        else:
            result = {
                "status": "success",
                "message": "Tool executed successfully.",
                "data": response,
            }
            return result
