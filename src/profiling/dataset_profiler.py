"""
Dataset Profiler for Unseen Tabular Datasets (Mode B / Examiner Mode).

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Union
import numpy as np
import pandas as pd


@dataclass
class ColumnProfile:
    """Detailed profile of a single column."""
    name: str
    dtype_str: str
    inferred_type: str  # 'numeric', 'categorical', 'datetime', 'identifier', 'constant', 'all_missing'
    total_count: int
    missing_count: int
    missing_pct: float
    unique_count: int
    cardinality_ratio: float
    sample_values: List[Any]
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    mean_val: Optional[float] = None
    std_val: Optional[float] = None
    top_categories: Optional[Dict[str, int]] = None
    is_constant: bool = False
    is_candidate_id: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DatasetProfile:
    """Summary profile of the uploaded dataset."""
    filename: str
    total_rows: int
    total_columns: int
    duplicate_rows: int
    columns: Dict[str, ColumnProfile]
    candidate_targets: List[str] = field(default_factory=list)
    candidate_features: List[str] = field(default_factory=list)
    candidate_identifiers: List[str] = field(default_factory=list)
    candidate_constants: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "duplicate_rows": self.duplicate_rows,
            "columns": {k: v.to_dict() for k, v in self.columns.items()},
            "candidate_targets": self.candidate_targets,
            "candidate_features": self.candidate_features,
            "candidate_identifiers": self.candidate_identifiers,
            "candidate_constants": self.candidate_constants,
            "warnings": self.warnings,
        }


class DatasetProfiler:
    """
    Automated inspector and profiler for arbitrary tabular datasets (CSV / Excel).
    Operates without requiring hardcoded column names or prior schema knowledge.
    """

    ID_PATTERNS = [
        re.compile(r"^id$", re.IGNORECASE),
        re.compile(r".*_id$", re.IGNORECASE),
        re.compile(r"^id_.*", re.IGNORECASE),
        re.compile(r".*serial.*", re.IGNORECASE),
        re.compile(r".*batch.*", re.IGNORECASE),
        re.compile(r".*guid.*", re.IGNORECASE),
        re.compile(r".*uuid.*", re.IGNORECASE),
        re.compile(r"^index$", re.IGNORECASE),
    ]

    TARGET_HINTS = [
        re.compile(r".*yield.*", re.IGNORECASE),
        re.compile(r".*strength.*", re.IGNORECASE),
        re.compile(r".*shrinkage.*", re.IGNORECASE),
        re.compile(r".*quality.*", re.IGNORECASE),
        re.compile(r".*roughness.*", re.IGNORECASE),
        re.compile(r".*target.*", re.IGNORECASE),
        re.compile(r".*output.*", re.IGNORECASE),
        re.compile(r".*defect.*", re.IGNORECASE),
    ]

    def load_file(self, filepath_or_buffer: Any, filename: Optional[str] = None) -> pd.DataFrame:
        """
        Load tabular file from path or buffer supporting CSV, Excel (.xlsx/.xls).
        Handles encoding fallbacks defensively.
        """
        fname = filename or (filepath_or_buffer if isinstance(filepath_or_buffer, str) else "uploaded_dataset")
        ext = os.path.splitext(fname)[1].lower()

        if ext in [".xlsx", ".xls"]:
            try:
                df = pd.read_excel(filepath_or_buffer)
            except Exception as e:
                raise ValueError(f"Failed to read Excel file '{fname}': {str(e)}")
        else:
            # Attempt UTF-8, then fallback to latin-1
            try:
                df = pd.read_csv(filepath_or_buffer, encoding="utf-8")
            except UnicodeDecodeError:
                if isinstance(filepath_or_buffer, str):
                    df = pd.read_csv(filepath_or_buffer, encoding="latin-1")
                else:
                    filepath_or_buffer.seek(0)
                    df = pd.read_csv(filepath_or_buffer, encoding="latin-1")
            except Exception as e:
                raise ValueError(f"Failed to parse CSV file '{fname}': {str(e)}")

        if df.empty:
            raise ValueError(f"The supplied dataset '{fname}' is empty (0 rows).")

        # Strip whitespace from column names
        df.columns = [str(c).strip() for c in df.columns]
        return df

    def profile(self, df: pd.DataFrame, filename: str = "dataset") -> DatasetProfile:
        """
        Profile an entire DataFrame and return structured metadata.
        """
        total_rows, total_cols = df.shape
        dup_rows = int(df.duplicated().sum())

        col_profiles: Dict[str, ColumnProfile] = {}
        candidate_targets: List[str] = []
        candidate_features: List[str] = []
        candidate_identifiers: List[str] = []
        candidate_constants: List[str] = []
        warnings: List[str] = []

        if total_rows < 30:
            warnings.append(
                f"Small sample size warning: Dataset contains only {total_rows} rows. "
                "Statistical power and model evaluation reliability will be severely limited."
            )

        if dup_rows > 0:
            warnings.append(f"Duplicate rows detected: {dup_rows} identical rows found ({dup_rows / total_rows:.1%}).")

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            missing_pct = float(missing_count / total_rows) if total_rows > 0 else 0.0
            non_null = series.dropna()
            unique_count = int(non_null.nunique())
            cardinality_ratio = float(unique_count / total_rows) if total_rows > 0 else 0.0

            # Safe sample values for preview (convert non-serializables)
            samples = [
                float(x) if isinstance(x, (np.floating, float)) and not np.isnan(x)
                else int(x) if isinstance(x, (np.integer, int))
                else str(x)
                for x in non_null.head(4).tolist()
            ]

            # Inferred Type Determination
            if missing_count == total_rows:
                inferred_type = "all_missing"
                is_constant = True
                is_id = False
            elif unique_count <= 1:
                inferred_type = "constant"
                is_constant = True
                is_id = False
            elif self._matches_id_pattern(col, series, unique_count, total_rows):
                inferred_type = "identifier"
                is_id = True
                is_constant = False
            elif pd.api.types.is_numeric_dtype(series):
                inferred_type = "numeric"
                is_constant = False
                is_id = False
            elif pd.api.types.is_datetime64_any_dtype(series):
                inferred_type = "datetime"
                is_constant = False
                is_id = False
            else:
                inferred_type = "categorical"
                is_constant = False
                is_id = False

            # Numeric statistics
            min_v, max_v, mean_v, std_v = None, None, None, None
            if inferred_type == "numeric" and len(non_null) > 0:
                min_v = float(non_null.min())
                max_v = float(non_null.max())
                mean_v = float(non_null.mean())
                std_v = float(non_null.std(ddof=1)) if len(non_null) > 1 else 0.0
                if std_v == 0.0:
                    is_constant = True
                    inferred_type = "constant"

            # Categorical statistics
            top_cats = None
            if inferred_type == "categorical" and len(non_null) > 0:
                vc = non_null.value_counts().head(5).to_dict()
                top_cats = {str(k): int(v) for k, v in vc.items()}

            cp = ColumnProfile(
                name=col,
                dtype_str=str(series.dtype),
                inferred_type=inferred_type,
                total_count=total_rows,
                missing_count=missing_count,
                missing_pct=missing_pct,
                unique_count=unique_count,
                cardinality_ratio=cardinality_ratio,
                sample_values=samples,
                min_val=min_v,
                max_val=max_v,
                mean_val=mean_v,
                std_val=std_v,
                top_categories=top_cats,
                is_constant=is_constant,
                is_candidate_id=is_id,
            )
            col_profiles[col] = cp

            # Categorize semantic candidate roles
            if is_constant:
                candidate_constants.append(col)
                warnings.append(f"Column '{col}' is constant (zero variance) and should be excluded from modeling.")
            elif is_id:
                candidate_identifiers.append(col)
                warnings.append(f"Column '{col}' appears to be a unique record identifier or sequence index.")
            elif inferred_type == "all_missing":
                warnings.append(f"Column '{col}' is 100% missing values.")
            else:
                # Valid candidate feature
                candidate_features.append(col)
                # If numeric with variance and not pure ID, consider candidate target
                if inferred_type == "numeric" and not is_constant:
                    candidate_targets.append(col)

        # Prioritize candidate targets matching known manufacturing target keywords
        candidate_targets.sort(key=lambda c: any(p.match(c) for p in self.TARGET_HINTS), reverse=True)

        return DatasetProfile(
            filename=filename,
            total_rows=total_rows,
            total_columns=total_cols,
            duplicate_rows=dup_rows,
            columns=col_profiles,
            candidate_targets=candidate_targets,
            candidate_features=candidate_features,
            candidate_identifiers=candidate_identifiers,
            candidate_constants=candidate_constants,
            warnings=warnings,
        )

    def _matches_id_pattern(self, col: str, series: pd.Series, unique_count: int, total_rows: int) -> bool:
        """Check if column looks like a database primary key or sequence identifier."""
        # 1. Exact name pattern match
        for pat in self.ID_PATTERNS:
            if pat.match(col):
                return True
        # 2. Never treat continuous floating-point variables as identifiers
        if pd.api.types.is_float_dtype(series):
            return False
        # 3. 100% uniqueness in string / object or integer sequence
        if total_rows >= 20 and unique_count == total_rows:
            return True
        return False
