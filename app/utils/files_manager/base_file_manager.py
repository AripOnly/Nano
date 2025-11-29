# app/tools/file_managers/base_file_manager.py

import os
import tempfile
import shutil
from pathlib import Path
from app.utils.logger import log


class BaseFileManager:
    """
    Base class untuk semua file operations.
    Berisi common utilities dan safety patterns.
    """

    def __init__(self):
        self.supported_text_encodings = ["utf-8", "latin-1", "cp1252"]

    def _validate_path(self, filepath: str | Path) -> Path:
        """
        Validasi dan convert path ke Path object.

        Args:
            filepath: Path sebagai string atau Path object

        Returns:
            Path object yang sudah divalidasi

        Raises:
            ValueError: Jika path tidak valid
        """
        try:
            path = Path(filepath)
            if not path.parent:
                raise ValueError(f"Invalid path: {filepath}")
            return path
        except Exception as e:
            log.error(f"Path validation failed for '{filepath}': {e}")
            raise ValueError(f"Invalid path: {filepath}") from e

    def _ensure_directory_exists(self, path: Path) -> None:
        """
        Pastikan parent directory exists.

        Args:
            path: Path object
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log.error(f"Failed to create directory '{path.parent}': {e}")
            raise

    def _safe_write(self, path: Path, content: str, encoding: str = "utf-8") -> bool:
        """
        Atomic write menggunakan temporary file.

        Args:
            path: Target file path
            content: Content to write
            encoding: Text encoding

        Returns:
            True jika berhasil, False jika gagal
        """
        temp_path = None
        try:
            # Create temp file in same directory for atomic replace
            with tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                dir=path.parent,
                encoding=encoding,
                suffix=".tmp",
            ) as tmp_file:
                temp_path = Path(tmp_file.name)
                tmp_file.write(content)

            # Atomic replace
            os.replace(temp_path, path)
            log.debug(f"Atomic write successful for '{path}'")
            return True

        except Exception as e:
            log.error(f"Safe write failed for '{path}': {e}")
            # Cleanup temp file if exists
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return False

    def _safe_json_write(self, path: Path, data, encoding: str = "utf-8") -> bool:
        """
        Atomic JSON write menggunakan temporary file.

        Args:
            path: Target file path
            data: Data to serialize as JSON
            encoding: Text encoding

        Returns:
            True jika berhasil, False jika gagal
        """
        import json

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                dir=path.parent,
                encoding=encoding,
                suffix=".tmp",
            ) as tmp_file:
                temp_path = Path(tmp_file.name)
                json.dump(data, tmp_file, ensure_ascii=False, indent=4)

            # Atomic replace
            os.replace(temp_path, path)
            log.debug(f"Atomic JSON write successful for '{path}'")
            return True

        except Exception as e:
            log.error(f"Safe JSON write failed for '{path}': {e}")
            # Cleanup temp file if exists
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return False

    def _try_fix_json(self, json_str: str):
        """
        Helper function untuk coba perbaiki JSON rusak.

        Args:
            json_str: JSON string yang mungkin rusak

        Returns:
            Parsed data jika berhasil, None jika gagal
        """
        import json

        try:
            json_str = json_str.strip()
            if not json_str:
                return None

            # Coba parse langsung
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Simple auto-fix attempts
            try:
                # Coba tambahkan kurung jika missing
                if not json_str.startswith("{") and not json_str.startswith("["):
                    if ":" in json_str:
                        json_str = "{" + json_str + "}"
                    else:
                        json_str = "[" + json_str + "]"
                return json.loads(json_str)
            except:
                return None
        except Exception:
            return None

    def _get_file_size_mb(self, path: Path) -> float:
        """
        Dapatkan ukuran file dalam MB.

        Args:
            path: File path

        Returns:
            Size in MB, 0 jika file tidak ada atau error
        """
        try:
            if path.exists() and path.is_file():
                return path.stat().st_size / (1024 * 1024)
            return 0.0
        except Exception as e:
            log.error(f"Failed to get file size for '{path}': {e}")
            return 0.0

    def _standard_success_response(self, message: str, data=None) -> dict:
        """
        Standard success response format.
        """
        response = {"status": "success", "message": message}
        if data is not None:
            response["data"] = data
        return response

    def _standard_warning_response(self, message: str, data=None) -> dict:
        """
        Standard warning response format.
        """
        response = {"status": "warning", "message": message}
        if data is not None:
            response["data"] = data
        return response

    def _standard_error_response(self, message: str, data=None) -> dict:
        """
        Standard error response format.
        """
        response = {"status": "error", "message": message}
        if data is not None:
            response["data"] = data
        return response

    def _check_file_exists(self, path: Path) -> bool:
        """
        Cek apakah file exists dan adalah file (bukan directory).

        Args:
            path: File path to check

        Returns:
            True jika file valid, False jika tidak
        """
        try:
            return path.exists() and path.is_file()
        except Exception as e:
            log.error(f"Error checking file existence for '{path}': {e}")
            return False

    def _detect_encoding(self, path: Path) -> str:
        """
        Detect file encoding (simple implementation).

        Args:
            path: File path

        Returns:
            Detected encoding string
        """
        import chardet

        try:
            with open(path, "rb") as f:
                raw_data = f.read(8192)  # Read first 8KB for detection
                result = chardet.detect(raw_data)
                encoding = result["encoding"] or "utf-8"
                log.debug(f"Detected encoding for '{path}': {encoding}")
                return encoding
        except Exception as e:
            log.warning(f"Encoding detection failed for '{path}', using utf-8: {e}")
            return "utf-8"
