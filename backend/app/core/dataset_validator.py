import unicodedata
from enum import Enum
import pandas as pd
import numpy as np
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple, Optional
from app.core.reliability_helper import ReliabilityHelper

# ---------------------------------------------------------------------------
# Configurable thresholds
# ---------------------------------------------------------------------------

# Fraction of non-null values that must be numeric to trigger a
# MIXED_DATATYPE_COLUMN warning on an object-dtype column.
MIXED_DTYPE_NUMERIC_THRESHOLD: float = 0.60

# Column name length (characters) above which a LONG_COLUMN_NAME warning is emitted.
LONG_COLUMN_NAME_THRESHOLD: int = 100

# Public validator version used in pipeline metadata.
VALIDATOR_VERSION: str = "1.0"


# ---------------------------------------------------------------------------
# Validation codes
# ---------------------------------------------------------------------------

class ValidationCode(str, Enum):
    # ---- Critical Errors (halt pipeline) ------------------------------------
    EMPTY_FILE                = "EMPTY_FILE"
    EMPTY_DATASET             = "EMPTY_DATASET"
    NO_COLUMNS                = "NO_COLUMNS"
    DUPLICATE_HEADERS         = "DUPLICATE_HEADERS"
    BLANK_HEADERS             = "BLANK_HEADERS"
    ALL_NULL_DATASET          = "ALL_NULL_DATASET"
    UNSUPPORTED_FILE          = "UNSUPPORTED_FILE"
    CORRUPTED_FILE            = "CORRUPTED_FILE"
    INVALID_ENCODING          = "INVALID_ENCODING"
    INVALID_HEADER_CHARACTERS = "INVALID_HEADER_CHARACTERS"
    UNEXPECTED_PIPELINE_ERROR = "UNEXPECTED_PIPELINE_ERROR"

    # ---- Quality Warnings (informational, do not halt pipeline) -------------
    HIGH_MISSINGNESS      = "HIGH_MISSINGNESS"
    HIGH_OUTLIERS         = "HIGH_OUTLIERS"
    VERY_SMALL_DATASET    = "VERY_SMALL_DATASET"
    ONE_ROW_DATASET       = "ONE_ROW_DATASET"
    ONE_COLUMN_DATASET    = "ONE_COLUMN_DATASET"
    CONSTANT_COLUMN       = "CONSTANT_COLUMN"
    MIXED_DATATYPE_COLUMN = "MIXED_DATATYPE_COLUMN"
    LONG_COLUMN_NAME      = "LONG_COLUMN_NAME"
    DUPLICATE_ROWS        = "DUPLICATE_ROWS"
    INFINITY_VALUES       = "INFINITY_VALUES"
    EMPTY_STRING_VALUES   = "EMPTY_STRING_VALUES"
    LOW_STATISTICAL_RELIABILITY = "LOW_STATISTICAL_RELIABILITY"


# ---------------------------------------------------------------------------
# Per-code actionable recovery guidance
# ---------------------------------------------------------------------------

RECOVERY_GUIDANCE: Dict[str, str] = {
    # Critical errors
    ValidationCode.EMPTY_FILE: (
        "Upload a non-empty file containing at least column headers and one data row."
    ),
    ValidationCode.EMPTY_DATASET: (
        "Add at least one data row below the header row and re-upload the file."
    ),
    ValidationCode.NO_COLUMNS: (
        "Upload a properly formatted dataset that contains column headers."
    ),
    ValidationCode.DUPLICATE_HEADERS: (
        "Rename duplicate column headers so every column has a unique, descriptive name."
    ),
    ValidationCode.BLANK_HEADERS: (
        "Ensure every column has a unique, non-empty descriptive name before uploading."
    ),
    ValidationCode.ALL_NULL_DATASET: (
        "Populate the dataset with actual data values before uploading for analysis."
    ),
    ValidationCode.CORRUPTED_FILE: (
        "Re-export or recreate the file and ensure it is not truncated or password-protected."
    ),
    ValidationCode.UNSUPPORTED_FILE: (
        "Convert the file to CSV (.csv) or Excel (.xlsx, .xls) before uploading."
    ),
    ValidationCode.INVALID_ENCODING: (
        "Save the file with UTF-8 encoding before uploading."
    ),
    ValidationCode.INVALID_HEADER_CHARACTERS: (
        "Replace emoji-only or symbol-only column headers with descriptive text names."
    ),
    ValidationCode.UNEXPECTED_PIPELINE_ERROR: (
        "Retry the upload. If the issue persists, review the server logs for more details."
    ),
    # Quality warnings
    ValidationCode.HIGH_MISSINGNESS: (
        "Impute missing values using the column median (numeric) or mode (categorical), "
        "or remove the column if it provides insufficient signal."
    ),
    ValidationCode.HIGH_OUTLIERS: (
        "Review and clip extreme outliers to the 1.5×IQR boundary, "
        "or apply a robust scaler before modeling."
    ),
    ValidationCode.CONSTANT_COLUMN: (
        "Retain constant columns for descriptive summaries. "
        "Drop them before predictive modeling since they provide zero variance."
    ),
    ValidationCode.MIXED_DATATYPE_COLUMN: (
        "Convert invalid values to numeric (coerce), replace them with missing values, "
        "or remove the affected rows before analysis."
    ),
    ValidationCode.VERY_SMALL_DATASET: (
        "Collect additional observations. "
        "A minimum of 30 rows is recommended for statistically meaningful inference."
    ),
    ValidationCode.ONE_ROW_DATASET: (
        "Collect additional observations. Statistical analysis requires multiple data points."
    ),
    ValidationCode.ONE_COLUMN_DATASET: (
        "Add more attribute columns to enable correlation analysis and predictive modeling."
    ),
    ValidationCode.LONG_COLUMN_NAME: (
        "Shorten column names to improve readability and compatibility with downstream tools."
    ),
    ValidationCode.DUPLICATE_ROWS: (
        "Remove exact duplicate records to prevent double-counting "
        "and skewed statistical estimates."
    ),
    ValidationCode.INFINITY_VALUES: (
        "Review infinite values and replace them with finite values or missing values "
        "before statistical modeling."
    ),
    ValidationCode.EMPTY_STRING_VALUES: (
        "Treat empty strings consistently as missing values, or populate them where they "
        "represent omitted data."
    ),
    ValidationCode.LOW_STATISTICAL_RELIABILITY: (
        "Use results as exploratory guidance and collect more observations before making "
        "high-confidence decisions."
    ),
}


# ---------------------------------------------------------------------------
# Internal helper — Unicode-aware header character check
# ---------------------------------------------------------------------------

def _has_valid_header_characters(header_str: str) -> bool:
    """
        Returns True if the column header contains at least one Unicode letter or
        number from any script.

        Uses ``unicodedata.category()`` for script-agnostic classification so we
        accept multilingual business headers while rejecting emoji-only and
        symbol-only labels.
    """
    stripped = header_str.strip()
    if not stripped:
        return False  # blank — caught upstream
    for ch in stripped:
        cat = unicodedata.category(ch)
        if cat.startswith("L") or cat.startswith("N"):
            return True
    return False


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ValidationErrorModel(BaseModel):
    """Represents a critical validation failure that halts the pipeline."""
    version: str = "1.0"
    status: str = "validation_failed"
    code: ValidationCode
    message: str
    severity: str = "critical"
    recoverable: bool = True
    recovery: Optional[str] = None


class ValidationWarningModel(BaseModel):
    """Represents a non-fatal data quality warning."""
    code: ValidationCode
    column: Optional[str] = None
    message: str
    severity: str = "warning"
    explanation: Optional[str] = None
    affected_columns: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    # Extended structured fields (populated for MIXED_DATATYPE_COLUMN and others)
    expected_type: Optional[str] = None
    detected_type: Optional[str] = None
    invalid_values: Optional[List[str]] = None
    invalid_count: Optional[int] = None
    invalid_percentage: Optional[float] = None
    recommendation: Optional[str] = None


# ---------------------------------------------------------------------------
# Centralized validator
# ---------------------------------------------------------------------------

class DatasetValidator:
    """
    Centralized validation engine for uploaded datasets.

    Performs critical validations (halt pipeline on failure) and records
    non-fatal quality warnings. All validation decisions live here — agents
    consume the structured results rather than re-implementing rules.
    """

    @staticmethod
    def get_recovery_guidance(code: ValidationCode) -> str:
        """Returns per-code actionable recovery guidance."""
        return RECOVERY_GUIDANCE.get(
            code,
            "Review the dataset and re-upload after making the necessary corrections."
        )

    @staticmethod
    def _mixed_datatype_warning(
        col_str: str,
        numeric_pct: float,
        invalid_count: int,
        invalid_pct: float,
        sample_invalids: List[str],
    ) -> ValidationWarningModel:
        return ValidationWarningModel(
            code=ValidationCode.MIXED_DATATYPE_COLUMN,
            column=col_str,
            affected_columns=[col_str],
            message=(
                f"Column '{col_str}' appears to be predominantly numeric "
                f"({round(numeric_pct * 100, 1)}% of values coerce to a number) "
                f"but contains {invalid_count} non-numeric value(s) ({invalid_pct}%). "
                "This is a quality warning, not a validation failure."
            ),
            explanation=(
                "The column is analyzable, but mixed numeric and text values can affect "
                "aggregation, modeling, and type inference."
            ),
            severity="warning",
            expected_type="numeric",
            detected_type="mixed (numeric + text)",
            invalid_values=sample_invalids,
            invalid_count=invalid_count,
            invalid_percentage=invalid_pct,
            metadata={
                "numeric_percentage": round(numeric_pct * 100, 2),
                "sample_invalid_values": sample_invalids,
            },
            recommendation=DatasetValidator.get_recovery_guidance(
                ValidationCode.MIXED_DATATYPE_COLUMN
            ),
        )

    @staticmethod
    def validate(
        df: pd.DataFrame,
        raw_headers: Optional[List[Any]] = None,
    ) -> Tuple[bool, Optional[ValidationErrorModel], List[ValidationWarningModel]]:
        """
        Validates the DataFrame.

        Args:
            df:          The loaded pandas DataFrame.
            raw_headers: Optional list of raw header values extracted before
                         pandas rename/deduplication (used for blank/dup checks).

        Returns:
            (is_valid, error_model, warnings_list)
        """
        warnings: List[ValidationWarningModel] = []

        headers_to_check = raw_headers if raw_headers is not None else df.columns.tolist()

        # ------------------------------------------------------------------
        # Critical checks — any failure returns immediately
        # ------------------------------------------------------------------

        # 1. No columns at all
        if len(headers_to_check) == 0:
            return (
                False,
                ValidationErrorModel(
                    code=ValidationCode.NO_COLUMNS,
                    message="The uploaded dataset has no columns.",
                    recovery=DatasetValidator.get_recovery_guidance(ValidationCode.NO_COLUMNS),
                ),
                [],
            )

        # 2. Blank or unnamed column headers
        blank_cols = [
            str(col) for col in headers_to_check
            if pd.isna(col)
            or not str(col).strip()
            or str(col).startswith("Unnamed:")
            or str(col).lower() == "nan"
        ]
        if blank_cols:
            return (
                False,
                ValidationErrorModel(
                    code=ValidationCode.BLANK_HEADERS,
                    message="The dataset contains blank or unnamed column headers.",
                    recovery=DatasetValidator.get_recovery_guidance(ValidationCode.BLANK_HEADERS),
                ),
                [],
            )

        # 3. Duplicate column headers
        headers_str = [str(h) for h in headers_to_check]
        seen: set = set()
        dup_cols: List[str] = []
        for h in headers_str:
            if h in seen:
                dup_cols.append(h)
            else:
                seen.add(h)
        if dup_cols:
            return (
                False,
                ValidationErrorModel(
                    code=ValidationCode.DUPLICATE_HEADERS,
                    message=(
                        f"The dataset contains duplicate column headers: "
                        f"{', '.join(sorted(set(dup_cols)))}."
                    ),
                    recovery=DatasetValidator.get_recovery_guidance(
                        ValidationCode.DUPLICATE_HEADERS
                    ),
                ),
                [],
            )

        # 4. Invalid header characters — emoji-only / symbol-only headers
        #    Runs AFTER blank/dup checks so we never double-report.
        invalid_char_headers = [
            str(h) for h in headers_to_check
            if not _has_valid_header_characters(str(h))
        ]
        if invalid_char_headers:
            sample = invalid_char_headers[:5]
            return (
                False,
                ValidationErrorModel(
                    code=ValidationCode.INVALID_HEADER_CHARACTERS,
                    message=(
                        f"The dataset contains column headers with no readable alphanumeric "
                        f"characters (emoji-only or symbol-only): "
                        f"{', '.join(repr(h) for h in sample)}."
                    ),
                    recovery=DatasetValidator.get_recovery_guidance(
                        ValidationCode.INVALID_HEADER_CHARACTERS
                    ),
                ),
                [],
            )

        # 5. Headers only — zero data rows
        if len(df) == 0:
            return (
                False,
                ValidationErrorModel(
                    code=ValidationCode.EMPTY_DATASET,
                    message="The uploaded dataset contains column headers but no data rows.",
                    recovery=DatasetValidator.get_recovery_guidance(ValidationCode.EMPTY_DATASET),
                ),
                [],
            )

        # 6. Entire DataFrame is null
        if df.isnull().all().all():
            return (
                False,
                ValidationErrorModel(
                    code=ValidationCode.ALL_NULL_DATASET,
                    message="The uploaded dataset is entirely empty (all cells are null/NaN).",
                    recovery=DatasetValidator.get_recovery_guidance(
                        ValidationCode.ALL_NULL_DATASET
                    ),
                ),
                [],
            )

        # ------------------------------------------------------------------
        # Quality warnings — dataset is still considered valid
        # ------------------------------------------------------------------

        original_df = df

        # Convert infinity values to missing values (NaN) for downstream-safe
        # quality calculations after critical structural checks have passed.
        df = df.replace([np.inf, -np.inf], np.nan)

        total_rows = len(df)
        total_cols = len(df.columns)

        # --- Dataset-level warnings ---

        # Very small dataset
        if total_rows < 5:
            reliability = ReliabilityHelper.assess(total_rows)
            warnings.append(
                ValidationWarningModel(
                    code=ValidationCode.VERY_SMALL_DATASET,
                    message=(
                        f"The dataset is very small, containing only {total_rows} row(s). "
                        "Statistical reliability will be limited."
                    ),
                    explanation=reliability.explanation,
                    metadata={
                        "rows": total_rows,
                        "reliability_level": reliability.level,
                        "confidence": reliability.confidence,
                        "can_infer": reliability.can_infer,
                        "can_model": reliability.can_model,
                        "can_hypothesis_test": reliability.can_hypothesis_test,
                        "recommended_actions": reliability.recommended_actions,
                    },
                    recommendation=DatasetValidator.get_recovery_guidance(
                        ValidationCode.VERY_SMALL_DATASET
                    ),
                )
            )

        reliability = ReliabilityHelper.assess(total_rows)
        if reliability.requires_caution():
            warnings.append(
                ValidationWarningModel(
                    code=ValidationCode.LOW_STATISTICAL_RELIABILITY,
                    message=reliability.explanation,
                    severity=reliability.severity,
                    explanation=(
                        "The dataset can be analyzed, but the sample size limits the "
                        "strength of statistical conclusions."
                    ),
                    metadata={
                        "rows": total_rows,
                        "level": reliability.level,
                        "confidence": reliability.confidence,
                        "can_infer": reliability.can_infer,
                        "can_model": reliability.can_model,
                        "can_hypothesis_test": reliability.can_hypothesis_test,
                        "can_visualize": reliability.can_visualize,
                        "warnings": reliability.warnings,
                        "recommended_actions": reliability.recommended_actions,
                        "policy_version": reliability.policy_version,
                    },
                    recommendation=DatasetValidator.get_recovery_guidance(
                        ValidationCode.LOW_STATISTICAL_RELIABILITY
                    ),
                )
            )

        # Single data row
        if total_rows == 1:
            warnings.append(
                ValidationWarningModel(
                    code=ValidationCode.ONE_ROW_DATASET,
                    message="The dataset contains exactly one row of data.",
                    explanation=reliability.explanation,
                    metadata={"rows": total_rows, "reliability_level": reliability.level},
                    recommendation=DatasetValidator.get_recovery_guidance(
                        ValidationCode.ONE_ROW_DATASET
                    ),
                )
            )

        # Single column
        if total_cols == 1:
            warnings.append(
                ValidationWarningModel(
                    code=ValidationCode.ONE_COLUMN_DATASET,
                    message="The dataset contains exactly one column of data.",
                    explanation=(
                        "Single-column datasets remain analyzable for univariate summaries, "
                        "but multivariate analysis is not possible."
                    ),
                    metadata={"columns": total_cols},
                    recommendation=DatasetValidator.get_recovery_guidance(
                        ValidationCode.ONE_COLUMN_DATASET
                    ),
                )
            )

        # Excessively long column names
        for col in df.columns:
            col_str = str(col)
            if len(col_str) > LONG_COLUMN_NAME_THRESHOLD:
                warnings.append(
                    ValidationWarningModel(
                        code=ValidationCode.LONG_COLUMN_NAME,
                        column=col_str[:60] + "...",
                        affected_columns=[col_str],
                        message=(
                            f"Column name is excessively long ({len(col_str)} characters). "
                            "Very long names can reduce readability and cause compatibility issues "
                            "with downstream analytical tools."
                        ),
                        explanation=(
                            "Long headers are valid, including Unicode and business symbols, "
                            "but may be harder to display or reference in generated reports."
                        ),
                        metadata={"length": len(col_str), "threshold": LONG_COLUMN_NAME_THRESHOLD},
                        recommendation=DatasetValidator.get_recovery_guidance(
                            ValidationCode.LONG_COLUMN_NAME
                        ),
                    )
                )

        # Duplicate rows
        if total_rows > 1:
            try:
                dup_count = int(df.duplicated().sum())
                if dup_count > 0:
                    dup_pct = round((dup_count / total_rows) * 100, 1)
                    warnings.append(
                        ValidationWarningModel(
                            code=ValidationCode.DUPLICATE_ROWS,
                            message=(
                                f"The dataset contains {dup_count} duplicate row(s) "
                                f"({dup_pct}% of records). Duplicate records can distort "
                                "statistical estimates and model training."
                            ),
                            explanation=(
                                "Duplicate rows are valid data, but they may represent repeated "
                                "records rather than independent observations."
                            ),
                            metadata={
                                "duplicate_rows": dup_count,
                                "duplicate_percentage": dup_pct,
                                "total_rows": total_rows,
                            },
                            recommendation=DatasetValidator.get_recovery_guidance(
                                ValidationCode.DUPLICATE_ROWS
                            ),
                        )
                    )
            except Exception:
                pass

        # --- Per-column warnings ---

        for col in df.columns:
            col_str = str(col)
            series = df[col]
            original_series = original_df[col]
            null_count = int(series.isnull().sum())  # type: ignore
            null_pct = (null_count / total_rows) * 100

            try:
                if pd.api.types.is_numeric_dtype(original_series.dtype):
                    inf_mask = np.isinf(original_series.to_numpy(dtype=float, copy=False))
                    inf_count = int(inf_mask.sum())
                    if inf_count > 0:
                        warnings.append(
                            ValidationWarningModel(
                                code=ValidationCode.INFINITY_VALUES,
                                column=col_str,
                                affected_columns=[col_str],
                                message=(
                                    f"Column '{col_str}' contains {inf_count} infinite value(s). "
                                    "These values were treated as missing for validation metrics."
                                ),
                                explanation=(
                                    "Infinity and -Infinity are accepted as data quality issues, "
                                    "not critical validation failures."
                                ),
                                metadata={
                                    "infinity_count": inf_count,
                                    "total_rows": total_rows,
                                    "infinity_percentage": round((inf_count / total_rows) * 100, 2),
                                },
                                recommendation=DatasetValidator.get_recovery_guidance(
                                    ValidationCode.INFINITY_VALUES
                                ),
                            )
                        )
            except Exception:
                pass

            try:
                empty_string_count = int(
                    original_series.astype("string").str.strip().eq("").fillna(False).sum()
                )
                if empty_string_count > 0:
                    warnings.append(
                        ValidationWarningModel(
                            code=ValidationCode.EMPTY_STRING_VALUES,
                            column=col_str,
                            affected_columns=[col_str],
                            message=(
                                f"Column '{col_str}' contains {empty_string_count} empty string "
                                "value(s)."
                            ),
                            explanation=(
                                "Empty strings are valid, but they often behave like missing "
                                "values and should be handled consistently."
                            ),
                            metadata={
                                "empty_string_count": empty_string_count,
                                "total_rows": total_rows,
                                "empty_string_percentage": round(
                                    (empty_string_count / total_rows) * 100, 2
                                ),
                            },
                            recommendation=DatasetValidator.get_recovery_guidance(
                                ValidationCode.EMPTY_STRING_VALUES
                            ),
                        )
                    )
            except Exception:
                pass

            # Entire column is empty
            if null_count == total_rows:
                warnings.append(
                    ValidationWarningModel(
                        code=ValidationCode.CONSTANT_COLUMN,
                        column=col_str,
                        affected_columns=[col_str],
                        message=(
                            f"Column '{col_str}' is entirely empty (all values are null), "
                            "which means it has zero variance. Empty columns can be retained "
                            "for descriptive review, but they add no analytical value and are "
                            "generally not useful for predictive modeling."
                        ),
                        explanation=(
                            "A fully missing column is structurally valid, but it carries no "
                            "analytical signal until populated."
                        ),
                        metadata={"missing_count": null_count, "missing_percentage": 100.0},
                        recommendation=(
                            "Drop empty columns before modeling, or populate them if they are "
                            "intended to carry meaningful information."
                        ),
                    )
                )
                continue

            # High missingness (>90%)
            if null_pct > 90.0:
                warnings.append(
                    ValidationWarningModel(
                        code=ValidationCode.HIGH_MISSINGNESS,
                        column=col_str,
                        affected_columns=[col_str],
                        message=(
                            f"Column '{col_str}' has a very high missingness ratio "
                            f"({round(null_pct, 1)}% of values are missing)."
                        ),
                        explanation=(
                            "The column is valid, but analyses using it may be unstable because "
                            "most observations are missing."
                        ),
                        metadata={
                            "missing_count": null_count,
                            "missing_percentage": round(null_pct, 2),
                            "threshold_percentage": 90.0,
                        },
                        recommendation=DatasetValidator.get_recovery_guidance(
                            ValidationCode.HIGH_MISSINGNESS
                        ),
                    )
                )

            non_null_series = series.dropna()

            # Constant column (single unique non-null value)
            if non_null_series.nunique() == 1:
                const_val = non_null_series.iloc[0]
                warnings.append(
                    ValidationWarningModel(
                        code=ValidationCode.CONSTANT_COLUMN,
                        column=col_str,
                        affected_columns=[col_str],
                        message=(
                            f"Column '{col_str}' has a single constant value "
                            f"('{const_val}') across all records, which means it has zero "
                            "variance. Constant columns are useful for descriptive analysis and "
                            "data auditing, but they generally do not improve statistical "
                            "inference or predictive modeling because they add no discriminative "
                            "signal."
                        ),
                        explanation=(
                            "Constant columns are valid but provide no variance for statistical "
                            "relationships or predictive features."
                        ),
                        metadata={
                            "unique_non_null_values": 1,
                            "constant_value": str(const_val),
                            "non_null_count": int(len(non_null_series)),
                        },
                        recommendation=DatasetValidator.get_recovery_guidance(
                            ValidationCode.CONSTANT_COLUMN
                        ),
                    )
                )

            # Outlier warning (numeric columns with sufficient data)
            if pd.api.types.is_numeric_dtype(series.dtype) and len(non_null_series) >= 5:
                try:
                    q25 = float(non_null_series.quantile(0.25))
                    q75 = float(non_null_series.quantile(0.75))
                    iqr = q75 - q25
                    lower = q25 - 1.5 * iqr
                    upper = q75 + 1.5 * iqr
                    outliers = non_null_series[
                        (non_null_series < lower) | (non_null_series > upper)
                    ]
                    outliers_pct = (len(outliers) / len(non_null_series)) * 100
                    if outliers_pct > 15.0:
                        warnings.append(
                            ValidationWarningModel(
                                code=ValidationCode.HIGH_OUTLIERS,
                                column=col_str,
                                affected_columns=[col_str],
                                message=(
                                    f"Column '{col_str}' has a high percentage of statistical "
                                    f"outliers ({round(outliers_pct, 1)}% of non-null values "
                                    "lie outside the 1.5×IQR boundary)."
                                ),
                                explanation=(
                                    "Outliers are valid values, but they can dominate summaries, "
                                    "charts, and model fit."
                                ),
                                metadata={
                                    "outlier_count": int(len(outliers)),
                                    "outlier_percentage": round(outliers_pct, 2),
                                    "q1": q25,
                                    "q3": q75,
                                    "iqr": iqr,
                                    "lower_bound": lower,
                                    "upper_bound": upper,
                                },
                                recommendation=DatasetValidator.get_recovery_guidance(
                                    ValidationCode.HIGH_OUTLIERS
                                ),
                            )
                        )
                except Exception:
                    pass

            # Mixed datatype detection
            # Trigger for object/string columns with sufficient non-null data.
            if (
                pd.api.types.is_object_dtype(series.dtype)
                or pd.api.types.is_string_dtype(series.dtype)
            ) and len(non_null_series) > 0:
                try:
                    numeric_coerced = pd.to_numeric(non_null_series, errors="coerce")
                    numeric_count = int(numeric_coerced.notna().sum())
                    numeric_pct = numeric_count / len(non_null_series)

                    # Column is predominantly numeric but has some non-numeric residuals
                    if (
                        numeric_pct >= MIXED_DTYPE_NUMERIC_THRESHOLD
                        and numeric_count < len(non_null_series)
                    ):
                        non_numeric_vals = non_null_series[numeric_coerced.isna()]
                        sample_invalids = [
                            str(v) for v in non_numeric_vals.unique()[:5]
                        ]
                        invalid_count = int(len(non_numeric_vals))
                        invalid_pct = round(
                            (invalid_count / len(non_null_series)) * 100, 2
                        )
                        warnings.append(
                            DatasetValidator._mixed_datatype_warning(
                                col_str=col_str,
                                numeric_pct=numeric_pct,
                                invalid_count=invalid_count,
                                invalid_pct=invalid_pct,
                                sample_invalids=sample_invalids,
                            )
                        )
                except Exception:
                    pass

        return (True, None, warnings)
