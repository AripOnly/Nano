import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from .base_file_manager import BaseFileManager


class FileOperationsManager(BaseFileManager):
    """Manager for file operations: delete, copy, rename, move, restore"""

    def delete_file(self, filepath: str | Path, safe_delete: bool = True) -> dict:
        """
        Deletes a file safely.

        Args:
            filepath: Path of the file to be deleted
            safe_delete: Move to .trash first before permanent deletion

        Returns:
            dict: {status, message}
        """
        try:
            path = self._validate_path(filepath)

            # Check if file exists
            if not self._check_file_exists(path):
                return self._standard_warning_response(f"File '{path}' not found.")

            # Safe delete mode (move to trash)
            if safe_delete:
                trash_dir = path.parent / ".trash"
                trash_dir.mkdir(exist_ok=True)

                # Create unique name with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                trash_name = f"{path.stem}_{timestamp}{path.suffix}"
                trash_path = trash_dir / trash_name

                # Move to trash
                shutil.move(str(path), trash_path)

                return self._standard_success_response(f"File '{path}' moved to trash.")

            # Direct delete (permanent)
            else:
                path.unlink()
                return self._standard_success_response(
                    f"File '{path}' permanently deleted."
                )

        except PermissionError as e:
            return self._standard_error_response(
                f"Permission denied deleting '{filepath}': {str(e)}"
            )
        except Exception as e:
            return self._standard_error_response(
                f"Error deleting file '{filepath}': {str(e)}"
            )

    def copy_file(
        self, src: str | Path, dst: str | Path, overwrite: bool = False
    ) -> dict:
        """
        Copies a file to a new location.

        Args:
            src: Source file path
            dst: Destination file path
            overwrite: Overwrite if the file already exists

        Returns:
            dict: {status, message}
        """
        try:
            src_path = self._validate_path(src)
            dst_path = self._validate_path(dst)

            # Source validation
            if not self._check_file_exists(src_path):
                return self._standard_error_response(f"Source file '{src}' not found.")

            # Determine destination path
            if dst_path.is_dir() or (not dst_path.suffix and not dst_path.exists()):
                target_path = dst_path / src_path.name
            else:
                target_path = dst_path

            # Check overwrite
            if target_path.exists() and not overwrite:
                return self._standard_warning_response(
                    f"File '{target_path}' already exists. Use overwrite=True to overwrite."
                )

            # Ensure destination directory exists
            self._ensure_directory_exists(target_path)

            # Copy using shutil.copy2 (preserve metadata)
            shutil.copy2(src_path, target_path)

            return self._standard_success_response(
                f"File '{src}' successfully copied to '{target_path}'."
            )

        except Exception as e:
            return self._standard_error_response(
                f"Error copying file '{src}' to '{dst}': {str(e)}"
            )

    def rename_file(self, src: str | Path, new_name: str) -> dict:
        """
        Renames a file.

        Args:
            src: Source file path
            new_name: New name or full path

        Returns:
            dict: {status, message}
        """
        try:
            src_path = self._validate_path(src)

            # Source validation
            if not self._check_file_exists(src_path):
                return self._standard_error_response(f"Source file '{src}' not found.")

            # Determine destination path
            new_path = Path(new_name)
            if not new_path.suffix:  # If only a name, use the same directory
                new_path = src_path.parent / new_path

            # Check if destination already exists
            if new_path.exists():
                return self._standard_error_response(
                    f"File '{new_path}' already exists."
                )

            # Ensure destination directory exists
            self._ensure_directory_exists(new_path)

            # Rename file
            src_path.rename(new_path)

            return self._standard_success_response(
                f"File '{src}' successfully renamed to '{new_path}'."
            )

        except Exception as e:
            return self._standard_error_response(
                f"Error renaming file '{src}': {str(e)}"
            )

    def move_file(
        self, src: str | Path, dst: str | Path, overwrite: bool = False
    ) -> dict:
        """
        Moves a file to a new location.

        Args:
            src: Source file path
            dst: Destination file path or directory
            overwrite: Overwrite if the file already exists

        Returns:
            dict: {status, message}
        """
        try:
            src_path = self._validate_path(src)
            dst_path = self._validate_path(dst)

            # Source validation
            if not self._check_file_exists(src_path):
                return self._standard_error_response(f"Source file '{src}' not found.")

            # Determine destination path
            if dst_path.is_dir() or (not dst_path.suffix and not dst_path.exists()):
                target_path = dst_path / src_path.name
            else:
                target_path = dst_path

            # Check overwrite
            if target_path.exists() and not overwrite:
                return self._standard_warning_response(
                    f"File '{target_path}' already exists. Use overwrite=True to overwrite."
                )

            # Ensure destination directory exists
            self._ensure_directory_exists(target_path)

            # Move file
            shutil.move(str(src_path), str(target_path))

            return self._standard_success_response(
                f"File '{src}' successfully moved to '{target_path}'."
            )

        except Exception as e:
            return self._standard_error_response(
                f"Error moving file '{src}' to '{dst}': {str(e)}"
            )

    def restore_file(
        self, trash_path: str | Path, restore_dir: str | Path = None
    ) -> dict:
        """
        Restores a file from trash.

        Args:
            trash_path: Path of the file in the .trash folder
            restore_dir: Destination directory for restoration (optional)

        Returns:
            dict: {status, message}
        """
        try:
            trash_path = self._validate_path(trash_path)

            # Validate file in trash
            if not self._check_file_exists(trash_path):
                return self._standard_error_response(
                    f"File '{trash_path}' not found in trash."
                )

            # Determine restore directory
            if restore_dir:
                restore_dir = Path(restore_dir)
            else:
                # Default: parent of the .trash folder
                restore_dir = trash_path.parent.parent

            # Ensure restore directory exists
            self._ensure_directory_exists(restore_dir)

            # Remove timestamp from file name
            # Format: original_name_timestamp.ext -> original_name.ext
            parts = trash_path.name.rsplit("_", 1)
            if (
                len(parts) > 1
                and parts[1].split(".")[0].isdigit()
                and len(parts[1].split(".")[0]) == 14
            ):
                # Assuming the timestamp is exactly 14 digits (YYYYMMDD_HHMMSS)
                original_name = parts[0] + trash_path.suffix
            else:
                # Fallback if timestamp format is not standard
                original_name = trash_path.name.split("_", 1)[0] + trash_path.suffix

            restore_path = restore_dir / original_name

            # Check if file already exists at destination
            if restore_path.exists():
                # Add _restored suffix
                restore_path = restore_path.with_stem(restore_path.stem + "_restored")

            # Move from trash to restore location
            shutil.move(str(trash_path), str(restore_path))

            return self._standard_success_response(
                f"File successfully restored to '{restore_path}'."
            )

        except Exception as e:
            return self._standard_error_response(
                f"Error restoring file '{trash_path}': {str(e)}"
            )

    def get_file_info(self, filepath: str | Path) -> dict:
        """
        Gets detailed information about a file.

        Args:
            filepath: Path of the file

        Returns:
            dict: File information (name, size, etc.) on success, or a status error dict.
        """
        try:
            path = self._validate_path(filepath)

            if not self._check_file_exists(path):
                return self._standard_error_response(f"File '{path}' not found.")

            stat = path.stat()

            info = {
                "name": path.name,
                "path": str(path.absolute()),
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": path.suffix,
                "parent_dir": str(path.parent),
            }

            # Return info data directly
            return info

        except Exception as e:
            return self._standard_error_response(
                f"Error getting file info for '{filepath}': {str(e)}"
            )
