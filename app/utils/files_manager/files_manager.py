# app/tools/file_managers/file_manager.py

from .file_text_manager import TextFileManager
from .file_json_manager import JSONFileManager
from .file_operations_manager import FileOperationsManager
from .directory_manager import DirectoryManager


class FileManager:
    """
    Unified File Manager - Menyatukan semua file operations dalam satu interface.
    """

    def __init__(self):
        self.text = TextFileManager()
        self.json = JSONFileManager()
        self.ops = FileOperationsManager()
        self.dir = DirectoryManager()

        # Backward compatibility - direct access to common methods
        self._setup_direct_methods()

    def _setup_direct_methods(self):
        """Setup direct methods untuk backward compatibility"""
        # Text operations
        self.create_file = self.text.create_file
        self.read_file = self.text.read_file
        self.write_file = self.text.write_file
        self.append_file = self.text.append_file

        # JSON operations
        self.create_json = self.json.create_json
        self.write_json = self.json.write_json
        self.read_json = self.json.read_json
        self.append_json = self.json.append_json

        # File operations
        self.delete_file = self.ops.delete_file
        self.copy_file = self.ops.copy_file
        self.rename_file = self.ops.rename_file
        self.move_file = self.ops.move_file
        self.restore_file = self.ops.restore_file
        self.get_file_info = self.ops.get_file_info

        # Directory operations
        self.list_directory = self.dir.list_directory
        self.create_directory = self.dir.create_directory
        self.delete_directory = self.dir.delete_directory
        self.copy_directory = self.dir.copy_directory
        self.get_directory_size = self.dir.get_directory_size

    def get_stats(self) -> dict:
        """
        Dapatkan statistics tentang file manager.

        Returns:
            dict: Manager statistics
        """
        return {
            "managers": {
                "text": "TextFileManager",
                "json": "JSONFileManager",
                "ops": "FileOperationsManager",
                "dir": "DirectoryManager",
            },
            "features": {
                "text_operations": 4,
                "json_operations": 4,
                "file_operations": 6,
                "directory_operations": 5,
            },
        }
