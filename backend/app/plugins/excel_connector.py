import pandas as pd
import os
from typing import Dict, Any
from .base_connector import BaseDataConnector

class ExcelConnector(BaseDataConnector):
    """
    Connector for handling Excel files (.xlsx, .xls).
    """

    def read_data(self, source: str, **kwargs) -> pd.DataFrame:
        if not self.validate_source(source):
            raise ValueError(f"Invalid or inaccessible Excel file: {source}")
        
        # Load the first sheet by default
        engine = 'openpyxl' if source.lower().endswith('.xlsx') else 'xlrd'
        return pd.read_excel(source, engine=engine, **kwargs)

    def validate_source(self, source: str) -> bool:
        ext = os.path.splitext(source)[1].lower()
        return os.path.exists(source) and ext in ['.xlsx', '.xls']

    def get_metadata(self, source: str, **kwargs) -> Dict[str, Any]:
        if not self.validate_source(source):
            from app.core.dataset_validator import ValidationErrorModel, ValidationCode, DatasetValidator
            return {
                "is_valid": False,
                "error_object": ValidationErrorModel(
                    code=ValidationCode.UNSUPPORTED_FILE,
                    message="Unsupported file format. Please upload an Excel file (.xlsx, .xls).",
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

            engine = 'openpyxl' if source.lower().endswith('.xlsx') else 'xlrd'
            excel_file = pd.ExcelFile(source, engine=engine)
            sheet_names = excel_file.sheet_names
            
            # Extract raw headers before pandas renaming
            try:
                raw_headers_df = pd.read_excel(source, sheet_name=0, header=None, nrows=1, engine=engine)
                raw_headers = raw_headers_df.iloc[0].tolist() if not raw_headers_df.empty else []
            except Exception:
                raw_headers = []
                
            df = pd.read_excel(source, sheet_name=0, engine=engine)
            
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
                "sheet_names": sheet_names,
                "is_valid": True,
                "warnings": [w.model_dump() for w in warnings]
            }
        except Exception as e:
            from app.core.dataset_validator import ValidationErrorModel, ValidationCode, DatasetValidator
            return {
                "is_valid": False,
                "error_object": ValidationErrorModel(
                    code=ValidationCode.CORRUPTED_FILE,
                    message=f"Corrupted Excel structure: {str(e)}",
                    recovery=DatasetValidator.get_recovery_guidance(ValidationCode.CORRUPTED_FILE),
                ).model_dump()
            }
