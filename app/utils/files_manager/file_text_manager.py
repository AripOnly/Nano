from pathlib import Path
from .base_file_manager import BaseFileManager


class TextFileManager(BaseFileManager):
    """Manager for standard text file operations"""

    def create_file(
        self, filepath: str | Path, content: str = "", overwrite: bool = False
    ) -> dict:
        """
        Creates a new text file.

        Args:
            filepath: File path
            content: File content
            overwrite: Overwrite if the file already exists

        Returns:
            dict: {status, message}
        """
        try:
            path = self._validate_path(filepath)

            # Check if file already exists
            if path.exists() and not overwrite:
                return self._standard_warning_response(
                    f"File '{path}' already exists. File not modified."
                )

            # Create directory if it doesn't exist
            self._ensure_directory_exists(path)

            # Write file using safe write
            if self._safe_write(path, content):
                return self._standard_success_response(
                    f"File '{path}' successfully created."
                )
            else:
                return self._standard_error_response(f"Failed to create file '{path}'.")

        except Exception as e:
            return self._standard_error_response(
                f"Error creating file '{filepath}': {str(e)}"
            )

    def read_file(self, filepath: str | Path) -> str | dict:
        """
        Reads the content of a text file.

        Args:
            filepath: File path

        Returns:
            str: The content of the file on success.
            dict: {status, message} on error.
        """
        try:
            path = self._validate_path(filepath)

            # Check if file exists
            if not self._check_file_exists(path):
                return self._standard_error_response(f"File '{path}' not found.")

            # Detect encoding and read file
            encoding = self._detect_encoding(path)

            with open(path, "r", encoding=encoding) as f:
                content = f.read()

            # Return content directly on success
            return content

        except Exception as e:
            return self._standard_error_response(
                f"Error reading file '{filepath}': {str(e)}"
            )

    def write_file(
        self, filepath: str | Path, content: str, safe_write: bool = True
    ) -> dict:
        """
        Writes/overwrites a text file.

        Args:
            filepath: File path
            content: File content
            safe_write: Use atomic write for safety

        Returns:
            dict: {status, message}
        """
        try:
            path = self._validate_path(filepath)

            # Ensure directory exists
            self._ensure_directory_exists(path)

            # Write file
            if safe_write:
                success = self._safe_write(path, content)
            else:
                # Direct write (faster, less safe)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                success = True

            if success:
                return self._standard_success_response(
                    f"File '{path}' successfully written."
                )
            else:
                return self._standard_error_response(f"Failed to write file '{path}'.")

        except Exception as e:
            return self._standard_error_response(
                f"Error writing file '{filepath}': {str(e)}"
            )

    def append_file(self, filepath: str | Path, content: str) -> dict:
        """
        Appends content to the end of a file.

        Args:
            filepath: File path
            content: Content to append

        Returns:
            dict: {status, message}
        """
        try:
            path = self._validate_path(filepath)

            # Ensure directory exists
            self._ensure_directory_exists(path)

            # Append to file
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)

            return self._standard_success_response(
                f"Content successfully appended to '{path}'."
            )

        except Exception as e:
            return self._standard_error_response(
                f"Error appending content to '{filepath}': {str(e)}"
            )
