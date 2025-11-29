import json
from pathlib import Path
from .base_file_manager import BaseFileManager
from typing import Any


class JSONFileManager(BaseFileManager):
    """Manager specifically for JSON file operations"""

    def create_json(self, filepath: str | Path, data, overwrite: bool = False) -> dict:
        """Create a JSON file with standardized response."""
        try:
            path = self._validate_path(filepath)

            if path.exists() and not overwrite:
                return self._standard_warning_response(
                    f"File '{path}' already exists. Use overwrite=True to overwrite.",
                    data=str(path),
                )

            processed_data = self._process_json_data(data)
            self._ensure_directory_exists(path)

            if self._safe_json_write(path, processed_data):
                return self._standard_success_response(
                    f"JSON file '{path}' created successfully.",
                    data=str(path),
                )
            else:
                return self._standard_error_response(
                    f"Failed to create JSON file '{path}'."
                )

        except Exception as e:
            return self._standard_error_response(
                f"Error creating JSON file '{filepath}': {str(e)}"
            )

    def write_json(self, filepath: str | Path, data, safe_mode: bool = True) -> dict:
        """Write or overwrite JSON using standardized responses."""
        try:
            path = self._validate_path(filepath)
            processed_data = self._process_json_data(data)
            self._ensure_directory_exists(path)

            if safe_mode:
                success = self._safe_json_write(path, processed_data)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(processed_data, f, ensure_ascii=False, indent=4)
                success = True

            if success:
                return self._standard_success_response(
                    f"JSON file '{path}' written successfully.",
                    data=str(path),
                )
            else:
                return self._standard_error_response(
                    f"Failed to write JSON file '{path}'."
                )

        except Exception as e:
            return self._standard_error_response(
                f"Error writing JSON file '{filepath}': {str(e)}"
            )

    def read_json(self, filepath: str | Path, auto_fix: bool = True) -> Any:
        """
        Reads JSON and returns:
        - data (dict/list) on success
        - dict error/warning on failure
        """
        try:
            path = self._validate_path(filepath)

            if not self._check_file_exists(path):
                return self._standard_error_response(f"File '{path}' not found.")

            if self._get_file_size_mb(path) == 0:
                return self._standard_warning_response(
                    f"File '{path}' is empty.", data=None
                )

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                if not auto_fix:
                    raise

                repaired = self._try_fix_json(content)
                if repaired is None:
                    return self._standard_error_response(
                        f"Invalid JSON format in '{path}'."
                    )
                return repaired

        except Exception as e:
            return self._standard_error_response(
                f"Error reading JSON file '{filepath}': {str(e)}"
            )

    def append_json(
        self, filepath: str | Path, new_data, max_size_mb: int = 10
    ) -> dict:
        """
        Appends data to JSON and returns standardized dict response.
        """
        try:
            path = self._validate_path(filepath)

            if self._get_file_size_mb(path) > max_size_mb:
                return self._standard_error_response(
                    f"File '{path}' is too large (> {max_size_mb}MB)."
                )

            existing_data = []

            # Load existing JSON if possible
            if path.exists() and self._get_file_size_mb(path) > 0:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    existing_data = json.loads(content)
                except Exception:
                    existing_data = []

            # Process new data
            processed_data = self._process_json_data(new_data)

            # Merge logic
            if isinstance(existing_data, list):
                if isinstance(processed_data, list):
                    existing_data.extend(processed_data)
                else:
                    existing_data.append(processed_data)

            elif isinstance(existing_data, dict) and isinstance(processed_data, dict):
                existing_data.update(processed_data)

            else:
                return self._standard_error_response(
                    "Incompatible data types for append operation."
                )

            # Write back
            if self._safe_json_write(path, existing_data):
                return self._standard_success_response(
                    f"Data appended to '{path}' successfully.",
                    data={
                        "path": str(path),
                        "size_mb": round(self._get_file_size_mb(path), 3),
                    },
                )
            else:
                return self._standard_error_response(
                    f"Failed to write JSON file '{path}' after append."
                )

        except Exception as e:
            return self._standard_error_response(
                f"Error appending data to '{filepath}': {str(e)}"
            )

    def _process_json_data(self, data):
        """Validate and normalize JSON data."""
        if isinstance(data, (set, tuple)):
            data = list(data)

        if data is None:
            data = {}

        if not isinstance(data, (dict, list)):
            raise ValueError(
                f"Data type '{type(data).__name__}' is invalid. Must be dict or list."
            )

        return data
