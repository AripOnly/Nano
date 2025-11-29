import shutil
from pathlib import Path
from .base_file_manager import BaseFileManager


class DirectoryManager(BaseFileManager):
    """Manager for directory/folder operations"""

    def list_directory(
        self,
        dirpath: str | Path,
        only_files: bool = False,
        filter_ext: list[str] | None = None,
        recursive: bool = False,
    ) -> dict:
        """
        List directory contents.
        Returns structured dict (success / error).
        """
        try:
            path = self._validate_path(dirpath)

            if not path.exists() or not path.is_dir():
                return self._standard_error_response(
                    f"Directory '{path}' was not found or is not a folder."
                )

            # Collect items
            items = list(path.rglob("*")) if recursive else list(path.iterdir())

            # Filter: only files
            if only_files:
                items = [item for item in items if item.is_file()]

            # Filter: extensions
            if filter_ext:
                normalized_exts = [
                    ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                    for ext in filter_ext
                ]
                items = [
                    item for item in items if item.suffix.lower() in normalized_exts
                ]

            # Convert to relative paths
            item_paths = [str(item.relative_to(path)) for item in items]

            return self._standard_success_response(
                f"Listed {len(items)} item(s) in directory '{path}'.",
                data={
                    "count": len(items),
                    "items": item_paths,
                    "absolute_path": str(path),
                },
            )

        except Exception as e:
            return self._standard_error_response(
                f"Error listing directory '{dirpath}': {str(e)}"
            )

    def create_directory(self, dirpath: str | Path, parents: bool = True) -> dict:
        """Create directory with standardized response."""
        try:
            path = self._validate_path(dirpath)

            if path.exists():
                if path.is_dir():
                    return self._standard_warning_response(
                        f"Directory '{path}' already exists.",
                        data=str(path),
                    )
                else:
                    return self._standard_error_response(
                        f"Path '{path}' exists and is not a directory."
                    )

            path.mkdir(parents=parents, exist_ok=True)

            return self._standard_success_response(
                f"Directory '{path}' created successfully.",
                data=str(path),
            )

        except Exception as e:
            return self._standard_error_response(
                f"Error creating directory '{dirpath}': {str(e)}"
            )

    def delete_directory(self, dirpath: str | Path, recursive: bool = False) -> dict:
        """Delete directory with standardized response."""
        try:
            path = self._validate_path(dirpath)

            if not path.exists():
                return self._standard_warning_response(
                    f"Directory '{path}' was not found."
                )

            if not path.is_dir():
                return self._standard_error_response(
                    f"Path '{path}' is not a directory."
                )

            if recursive:
                shutil.rmtree(path)
                msg = f"Directory '{path}' and all contents were deleted."
            else:
                path.rmdir()
                msg = f"Directory '{path}' was deleted."

            return self._standard_success_response(msg, data=str(path))

        except OSError as e:
            if "Directory not empty" in str(e):
                return self._standard_error_response(
                    f"Directory '{dirpath}' is not empty. Use recursive=True."
                )
            return self._standard_error_response(
                f"Error deleting directory '{dirpath}': {str(e)}"
            )

        except Exception as e:
            return self._standard_error_response(
                f"Error deleting directory '{dirpath}': {str(e)}"
            )

    def copy_directory(self, src: str | Path, dst: str | Path) -> dict:
        """Copy directory with consistent response format."""
        try:
            src_path = self._validate_path(src)
            dst_path = self._validate_path(dst)

            if not src_path.exists() or not src_path.is_dir():
                return self._standard_error_response(
                    f"Source directory '{src}' was not found."
                )

            shutil.copytree(src_path, dst_path)

            return self._standard_success_response(
                f"Directory '{src}' copied to '{dst}'.",
                data={"src": str(src_path), "dst": str(dst_path)},
            )

        except FileExistsError:
            return self._standard_error_response(
                f"Destination directory '{dst}' already exists."
            )
        except Exception as e:
            return self._standard_error_response(
                f"Error copying directory '{src}' to '{dst}': {str(e)}"
            )

    def get_directory_size(self, dirpath: str | Path) -> dict:
        """Return directory size (bytes + MB) in dict format."""
        try:
            path = self._validate_path(dirpath)

            if not path.exists() or not path.is_dir():
                return self._standard_error_response(
                    f"Directory '{path}' was not found."
                )

            total_size = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except OSError:
                        pass

            size_mb = total_size / (1024 * 1024)

            return self._standard_success_response(
                f"Size calculated for '{path}'.",
                data={
                    "bytes": total_size,
                    "mb": round(size_mb, 3),
                    "path": str(path),
                },
            )

        except Exception as e:
            return self._standard_error_response(
                f"Error calculating directory size '{dirpath}': {str(e)}"
            )
