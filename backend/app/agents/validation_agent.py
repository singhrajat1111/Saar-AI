import os
import structlog
import chardet
from typing import Dict, Any
from app.plugins.csv_connector import CSVConnector
from app.plugins.excel_connector import ExcelConnector

logger = structlog.get_logger()

class ValidationAgent:
    """
    Agent responsible for validating the integrity of an uploaded file.
    Detects file types (CSV vs Excel), validates file access/existence,
    auto-detects CSV text encodings, and extracts preliminary metadata.
    """
    
    def __init__(self, file_path: str, file_type: str = "csv"):
        self.file_path = file_path
        self.file_type = file_type.lower()
        
        if self.file_type == "csv":
            self.connector = CSVConnector()
        elif self.file_type in ["xlsx", "xls"]:
            self.connector = ExcelConnector()
        else:
            self.connector = None

    def detect_encoding(self) -> str:
        """
        Detects text encoding of CSV files using chardet.
        """
        try:
            with open(self.file_path, "rb") as f:
                raw_data = f.read(20000)  # Read first 20KB for detection
            result = chardet.detect(raw_data)
            encoding = result.get("encoding") or "utf-8"
            # Normalize common encodings
            if encoding.lower() == "ascii":
                encoding = "utf-8"
            return encoding
        except Exception as e:
            logger.warn("encoding_detection_failed", error=str(e))
            return "utf-8"

    def execute(self) -> Dict[str, Any]:
        logger.info("validation_agent_start", file_path=self.file_path, file_type=self.file_type)
        
        from app.core.dataset_validator import ValidationErrorModel, ValidationCode

        if self.connector is None:
            error_obj = ValidationErrorModel(
                code=ValidationCode.UNSUPPORTED_FILE,
                message=(
                    "Unsupported file format. Please upload a CSV (.csv) or Excel "
                    "(.xlsx, .xls) file."
                ),
            ).model_dump()
            return {"status": "failed", "error_object": error_obj}

        if not os.path.exists(self.file_path):
            error_obj = ValidationErrorModel(
                code=ValidationCode.CORRUPTED_FILE,
                message=f"File path does not exist: {self.file_path}",
                recoverable=False
            ).model_dump()
            return {"status": "failed", "error_object": error_obj}
            
        file_size = os.path.getsize(self.file_path)
        if file_size == 0:
            error_obj = ValidationErrorModel(
                code=ValidationCode.EMPTY_FILE,
                message="The uploaded file is empty (0 bytes)."
            ).model_dump()
            return {"status": "failed", "error_object": error_obj}
            
        # Optional: Limit file size for V1 to 50MB to ensure smooth local operation
        if file_size > 50 * 1024 * 1024:
            error_obj = ValidationErrorModel(
                code=ValidationCode.CORRUPTED_FILE,
                message="File size exceeds the 50MB limit for local analysis.",
                recoverable=True
            ).model_dump()
            return {"status": "failed", "error_object": error_obj}

        try:
            # Gather metadata based on file type
            kwargs = {}
            if self.file_type == "csv":
                encoding = self.detect_encoding()
                logger.info("csv_encoding_detected", encoding=encoding)
                kwargs["encoding"] = encoding
                
            metadata = self.connector.get_metadata(self.file_path, **kwargs)
            if not metadata or not metadata.get("is_valid"):
                error_obj = metadata.get("error_object") if metadata else None
                if not error_obj:
                    reason = metadata.get("error", "Invalid dataset format or corrupted file structure.") if metadata else "Unknown error."
                    error_obj = ValidationErrorModel(
                        code=ValidationCode.CORRUPTED_FILE,
                        message=reason
                    ).model_dump()
                logger.error("validation_agent_fail", error_code=error_obj.get("code"), message=error_obj.get("message"))
                return {"status": "failed", "error_object": error_obj}
                
            metadata["encoding"] = kwargs.get("encoding", "binary")
            
            logger.info("validation_agent_success", file_size_bytes=file_size)
            return {
                "status": "success",
                "metadata": metadata
            }
        except Exception as e:
            logger.error("validation_agent_error", error=str(e))
            error_obj = ValidationErrorModel(
                code=ValidationCode.CORRUPTED_FILE,
                message=f"Corrupted or invalid file structure: {str(e)}"
            ).model_dump()
            return {"status": "failed", "error_object": error_obj}
