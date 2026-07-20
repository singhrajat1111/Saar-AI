import pandas as pd
import os
from typing import Dict, Any
from .base_connector import BaseDataConnector

class CSVConnector(BaseDataConnector):
    """
    Connector for handling CSV files.
    """

    def read_data(self, source: str, **kwargs) -> pd.DataFrame:
        if not self.validate_source(source):
            raise ValueError(f"Invalid or inaccessible CSV file: {source}")
        return pd.read_csv(source, **kwargs)

    def validate_source(self, source: str) -> bool:
        return os.path.exists(source) and source.lower().endswith('.csv')

    def get_metadata(self, source: str, **kwargs) -> Dict[str, Any]:
        if not self.validate_source(source):
            from app.core.dataset_validator import ValidationErrorModel, ValidationCode, DatasetValidator
            return {
                "is_valid": False,
                "error_object": ValidationErrorModel(
                    code=ValidationCode.UNSUPPORTED_FILE,
                    message="Unsupported file format. Please upload a CSV file.",
                    recovery=DatasetValidator.get_recovery_guidance(ValidationCode.UNSUPPORTED_FILE),
                ).model_dump()
            }
        
        try:
            file_size_bytes = os.path.getsize(source)
            if file_size_bytes == 0:
                from app.core.dataset_validator import ValidationErrorModel, ValidationCode, DatasetValidator
                return {
                    "is_valid": False,
                    "error_object": ValidationErrorModel(
                        code=ValidationCode.EMPTY_FILE,
                        message="The uploaded file is empty (0 bytes).",
                        recovery=DatasetValidator.get_recovery_guidance(ValidationCode.EMPTY_FILE),
                    ).model_dump()
                }
            
            # Extract raw headers before pandas renaming
            try:
                raw_headers_df = pd.read_csv(source, header=None, nrows=1, **kwargs)
                raw_headers = raw_headers_df.iloc[0].tolist() if not raw_headers_df.empty else []
            except Exception:
                raw_headers = []
                
            df = pd.read_csv(source, **kwargs)
            from app.core.dataset_validator import DatasetValidator
            is_valid, validation_error, warnings = DatasetValidator.validate(df, raw_headers)
            
            if not is_valid and validation_error:
                return {
                    "is_valid": False,
                    "error_object": validation_error.model_dump()
                }
                
            return {
                "file_size_bytes": file_size_bytes,
                "columns": df.columns.tolist(),
                "inferred_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "is_valid": True,
                "warnings": [w.model_dump() for w in warnings]
            }
        except pd.errors.EmptyDataError:
            from app.core.dataset_validator import ValidationErrorModel, ValidationCode, DatasetValidator
            return {
                "is_valid": False,
                "error_object": ValidationErrorModel(
                    code=ValidationCode.EMPTY_DATASET,
                    message="The uploaded dataset contains no data.",
                    recovery=DatasetValidator.get_recovery_guidance(ValidationCode.EMPTY_DATASET),
                ).model_dump()
            }
        except UnicodeDecodeError:
            from app.core.dataset_validator import ValidationErrorModel, ValidationCode, DatasetValidator
            return {
                "is_valid": False,
                "error_object": ValidationErrorModel(
                    code=ValidationCode.INVALID_ENCODING,
                    message=(
                        "The file could not be read with the detected encoding. "
                        "Please save the file with UTF-8 encoding and re-upload."
                    ),
                    recovery=DatasetValidator.get_recovery_guidance(ValidationCode.INVALID_ENCODING),
                ).model_dump()
            }
        except Exception as e:
            from app.core.dataset_validator import ValidationErrorModel, ValidationCode, DatasetValidator
            return {
                "is_valid": False,
                "error_object": ValidationErrorModel(
                    code=ValidationCode.CORRUPTED_FILE,
                    message=f"Corrupted CSV structure: {str(e)}",
                    recovery=DatasetValidator.get_recovery_guidance(ValidationCode.CORRUPTED_FILE),
                ).model_dump()
            }
