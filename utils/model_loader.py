import pandas as pd
import joblib
import os
from typing import Any, Dict, Literal, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler, LabelEncoder, PolynomialFeatures
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_selection import SelectFromModel
from sklearn.utils import resample
from sklearn.base import BaseEstimator, TransformerMixin


class RobustNumericImputer(BaseEstimator, TransformerMixin):
    """
    Numeric imputer that prefers per-feature medians but safely falls back to a
    constant value when a column is entirely missing or non-numeric.
    """

    def __init__(self, strategy: str = "median", fill_value: float = 0.0):
        self.strategy = strategy
        self.fill_value = fill_value
        self._imputer: Optional[SimpleImputer] = None

    def fit(self, X, y=None):
        imputer = SimpleImputer(strategy=self.strategy)
        imputer.fit(X)

        # When a column is all-NaN, SimpleImputer's statistics_ entry becomes NaN.
        # Replace those with a conservative constant so the pipeline stays robust.
        stats = np.array(imputer.statistics_, copy=True)
        stats = np.where(np.isnan(stats), self.fill_value, stats)
        imputer.statistics_ = stats

        self._imputer = imputer
        return self

    def transform(self, X):
        if self._imputer is None:
            raise RuntimeError("RobustNumericImputer must be fitted before transform.")
        return self._imputer.transform(X)

# Dataset schemas
LEGACY_DATASET_COLUMNS = [
    "incident_type",
    "injuries",
    "casualties",
    "location_risk",
    "weather",
    "response_time",
    "severity",
]

NEW_DATASET_COLUMNS = [
    "Timestamp",
    "Incident_Severity",
    "Incident_Type",
    "Region_Type",
    "Traffic_Congestion",
    "Weather_Condition",
    "Drone_Availability",
    "Ambulance_Availability",
    "Battery_Life",
    "Air_Traffic",
    "Response_Time",
    "Hospital_Capacity",
    "Distance_to_Incident",
    "Number_of_Injuries",
    "Specialist_Availability",
    "Road_Type",
    "Emergency_Level",
    "Drone_Speed",
    "Ambulance_Speed",
    "Payload_Weight",
    "Fuel_Level",
    "Weather_Impact",
    "Dispatch_Coordinator",
    "Label",
    "Hour",
    "Day_of_Week",
]


DatasetSchema = Literal["legacy", "new", "hybrid"]


def _has_all_columns(df: pd.DataFrame, cols: list[str]) -> bool:
    df_cols = set(df.columns.astype(str))
    return all(c in df_cols for c in cols)


def detect_dataset_schema(df: pd.DataFrame) -> Optional[DatasetSchema]:
    if _has_all_columns(df, NEW_DATASET_COLUMNS):
        return "new"
    if _has_all_columns(df, LEGACY_DATASET_COLUMNS):
        return "legacy"
    return None


def _auto_map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attempts to map common column name variations to the standard 'new' schema
    using both name matching and semantic content analysis.
    """
    mapping = {
        # Timestamp
        "time": "Timestamp", "date": "Timestamp", "dt": "Timestamp", "datetime": "Timestamp",
        # Severity
        "severity_level": "Incident_Severity", "criticity": "Incident_Severity", "risk": "Incident_Severity",
        # Incident Type
        "type": "Incident_Type", "category": "Incident_Type", "incident": "Incident_Type",
        # Injuries/Casualties
        "injury_count": "Number_of_Injuries", "injuries": "Number_of_Injuries",
        "death_count": "Number_of_Casualties", "deaths": "Number_of_Casualties", "casualties": "Number_of_Casualties",
        # Location/Region
        "location": "Region_Type", "area": "Region_Type", "region": "Region_Type",
        # Weather
        "weather_cond": "Weather_Condition", "weather": "Weather_Condition",
        # Targets
        "target": "Label", "outcome": "Label", "class": "Label"
    }
    
    # 1. Name-based mapping (case-insensitive)
    df_cols_lower = {c.lower(): c for c in df.columns}
    new_mapping = {}
    
    for key, standard in mapping.items():
        if key in df_cols_lower and standard not in df.columns:
            new_mapping[df_cols_lower[key]] = standard
            
    df = df.rename(columns=new_mapping)
    
    # 2. Semantic-based mapping (content analysis)
    # Check for Severity/Label-like columns if still missing
    if "Label" not in df.columns and "Incident_Severity" not in df.columns:
        for col in df.columns:
            if df[col].dtype == object:
                unique_vals = set(df[col].dropna().astype(str).str.lower().unique())
                if unique_vals.issubset({"low", "medium", "high", "critical", "severe", "minor", "moderate"}):
                    df = df.rename(columns={col: "Label"})
                    break

    # Check for Incident_Type-like columns
    if "Incident_Type" not in df.columns:
        for col in df.columns:
            if df[col].dtype == object:
                unique_vals = set(df[col].dropna().astype(str).str.lower().unique())
                if any(v in unique_vals for v in ["fire", "medical", "crime", "accident", "traffic", "flood"]):
                    df = df.rename(columns={col: "Incident_Type"})
                    break
                    
    return df

def validate_dataset_columns(df: pd.DataFrame) -> Tuple[bool, Optional[DatasetSchema], list[str]]:
    """
    Returns:
      (ok, schema, missing_columns)
    """
    # Try exact matches first
    schema = detect_dataset_schema(df)
    if schema:
        return True, schema, []

    # Try auto-mapping
    df_mapped = _auto_map_columns(df)
    schema_mapped = detect_dataset_schema(df_mapped)
    if schema_mapped:
        return True, schema_mapped, []

    # Relaxed Hybrid check: Does it have at least one target and one feature?
    target_candidates = ["Label", "Incident_Severity", "Emergency_Level", "severity"]
    df_cols = set(df_mapped.columns)
    has_target = any(c in df_cols for c in target_candidates)
    
    # Any dataset with at least one target and at least ONE other column is trainable.
    if has_target and len(df_cols) >= 2:
        # We still report what's missing from core features for user awareness, 
        # but we return True to allow training.
        core_features = ["Incident_Type", "Number_of_Injuries", "Weather_Condition", "Region_Type"]
        missing_core = [c for c in core_features if c not in df_cols]
        return True, "hybrid", missing_core

    # Total failure: report missing against the ideal 'new' schema
    missing_new = [c for c in NEW_DATASET_COLUMNS if c not in df_cols]
    return False, "new", missing_new


def _normalize_severity_value(v):
    if pd.isna(v):
        return v
    s = str(v).strip()
    s_lower = s.lower()
    mapping = {
        "low": "Low",
        "medium": "Medium",
        "med": "Medium",
        "high": "High",
        "critical": "Critical",
        "severe": "Critical",
    }
    return mapping.get(s_lower, s)


def _choose_target_series_from_new_schema(df: pd.DataFrame) -> pd.Series:
    """
    Prefer a target that looks like the app's severity labels.
    Falls back to Label / Incident_Severity if needed.
    """
    # Prefer Label first (usually the ML target), then Incident_Severity.
    # Emergency_Level is often an input signal (using it as target can tank metrics).
    preferred = ["Label", "Incident_Severity", "Emergency_Level"]
    for col in preferred:
        if col not in df.columns:
            continue
        s = df[col].map(_normalize_severity_value)
        unique = set(s.dropna().astype(str).unique().tolist())
        canonical = {"Low", "Medium", "High", "Critical"}
        if unique and unique.issubset(canonical):
            return s

    if "Label" in df.columns:
        return df["Label"].map(_normalize_severity_value)
    if "Incident_Severity" in df.columns:
        return df["Incident_Severity"].map(_normalize_severity_value)
    if "Emergency_Level" in df.columns:
        return df["Emergency_Level"].map(_normalize_severity_value)
    # Should never happen if NEW_DATASET_COLUMNS are present
    return pd.Series([None] * len(df))


def _choose_target_column_from_new_schema(df: pd.DataFrame) -> str:
    """
    Choose which column to treat as the training target for the new schema.
    Preference: Label -> Incident_Severity -> Emergency_Level
    """
    for col in ["Label", "Incident_Severity", "Emergency_Level"]:
        if col not in df.columns:
            continue
        s = df[col].map(_normalize_severity_value)
        unique = set(s.dropna().astype(str).unique().tolist())
        canonical = {"Low", "Medium", "High", "Critical"}
        if unique and unique.issubset(canonical):
            return col
    # Fallback: most likely target in this dataset
    if "Label" in df.columns:
        return "Label"
    if "Incident_Severity" in df.columns:
        return "Incident_Severity"
    return "Emergency_Level"


def _is_valid_target_column(df: pd.DataFrame, col: str) -> bool:
    if col not in df.columns:
        return False
    if col == "Timestamp":
        return False
    s = df[col].dropna().astype(str)
    return len(s) > 0 and s.nunique() >= 2


def _series_equalish(a: pd.Series, b: pd.Series) -> bool:
    try:
        aa = a.map(_normalize_severity_value).astype(str).fillna("")
        bb = b.map(_normalize_severity_value).astype(str).fillna("")
        if len(aa) != len(bb):
            return False
        return bool((aa == bb).mean() > 0.98)  # allow tiny noise
    except Exception:
        return False


def _safe_train_test_split(
    X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Try stratified split when feasible; fall back to normal split otherwise.
    """
    y_nonnull = y.dropna().astype(str)
    can_stratify = False
    try:
        vc = y_nonnull.value_counts()
        can_stratify = len(vc) >= 2 and int(vc.min()) >= 2
    except Exception:
        can_stratify = False

    if can_stratify:
        return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
    return train_test_split(X, y, test_size=test_size, random_state=random_state)


def _value_counts_dict(y: pd.Series) -> dict:
    return y.value_counts().to_dict()


def _balance_data(X: pd.DataFrame, y: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """
    Balances the dataset by upsampling minority classes to match the majority class.
    Essential for accurate prediction in imbalanced emergency data.
    """
    df = pd.concat([X, y], axis=1)
    target_col = y.name
    
    counts = y.value_counts()
    if len(counts) <= 1:
        return X, y
        
    max_count = counts.max()
    
    balanced_parts = []
    for label, count in counts.items():
        part = df[df[target_col] == label]
        if count < max_count:
            part = resample(part, replace=True, n_samples=max_count, random_state=42)
        balanced_parts.append(part)
        
    df_balanced = pd.concat(balanced_parts)
    return df_balanced.drop(columns=[target_col]), df_balanced[target_col]


def _make_preprocess_pipeline(
    categorical: list[str], 
    numeric: list[str], 
    include_interactions: bool = True,
    select_features: bool = False
) -> Pipeline:
    cat_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    
    num_steps = [
        ("coerce", FunctionTransformer(coerce_numeric, feature_names_out="one-to-one")),
        ("imputer", RobustNumericImputer(strategy="median", fill_value=0.0)),
        ("scaler", StandardScaler()),
    ]
    
    if include_interactions and len(numeric) >= 2:
        # Interaction terms only (e.g. injuries * casualties) to boost signal
        num_steps.append(("interactions", PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)))
        
    num_pipe = Pipeline(steps=num_steps)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", cat_pipe, categorical),
            ("num", num_pipe, numeric),
        ],
        remainder="drop",
    )
    
    steps = [("preprocess", preprocessor)]
    
    if select_features:
        # Add automated signal filtering
        steps.append(("selector", SelectFromModel(RandomForestClassifier(n_estimators=100, random_state=42), threshold="median")))
        
    return Pipeline(steps=steps)


def _value_counts_dict(y: pd.Series) -> Dict[str, int]:
    vc = y.dropna().astype(str).value_counts()
    return {k: int(v) for k, v in vc.items()}


def coerce_numeric(X):
    """
    Picklable coercion helper for sklearn pipelines.
    Converts values to numeric (non-numeric -> NaN) for robust imputing.
    """
    # X may be a DataFrame or ndarray depending on sklearn version.
    if isinstance(X, pd.DataFrame):
        out = X.copy()
        for c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
        return out

    df = pd.DataFrame(X)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.values


def _project_root() -> str:
    # utils/model_loader.py -> project root (one directory up from utils)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def normalize_training_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts either accepted dataset schema into the legacy training schema:
      incident_type, injuries, casualties, location_risk, weather, response_time, severity
    """
    schema = detect_dataset_schema(df)
    if schema == "legacy":
        out = df.copy()
        out["severity"] = out["severity"].map(_normalize_severity_value)
        return out

    out = pd.DataFrame()
    
    # Feature Engineering: Extract Time Components
    if "Timestamp" in df.columns:
        try:
            ts = pd.to_datetime(df["Timestamp"], errors="coerce")
            out["hour"] = ts.dt.hour.fillna(0).astype(int)
            out["day_of_week"] = ts.dt.dayofweek.fillna(0).astype(int)
            out["month"] = ts.dt.month.fillna(0).astype(int)
        except:
            pass

    out["incident_type"] = df["Incident_Type"].astype(str) if "Incident_Type" in df.columns else "Other"
    out["injuries"] = pd.to_numeric(df["Number_of_Injuries"], errors="coerce").fillna(0).astype(int) if "Number_of_Injuries" in df.columns else 0
    out["casualties"] = pd.to_numeric(df["Number_of_Casualties"], errors="coerce").fillna(0).astype(int) if "Number_of_Casualties" in df.columns else 0

    # Derive a rough 1-10 location risk proxy from available signals (keeps prediction UI compatible).
    risk = pd.to_numeric(df["Weather_Impact"], errors="coerce")
    if risk.isna().all():
        risk = pd.to_numeric(df["Traffic_Congestion"], errors="coerce")
    if risk.isna().all():
        risk = pd.to_numeric(df["Emergency_Level"], errors="coerce")

    if risk.isna().all():
        out["location_risk"] = 5
    else:
        # Min-max scale to 1..10
        rmin = float(risk.min(skipna=True))
        rmax = float(risk.max(skipna=True))
        if rmax == rmin:
            out["location_risk"] = 5
        else:
            out["location_risk"] = ((risk - rmin) / (rmax - rmin) * 9 + 1).fillna(5).astype(int)

    out["weather"] = df["Weather_Condition"].astype(str) if "Weather_Condition" in df.columns else "Clear"
    out["response_time"] = pd.to_numeric(df["Response_Time"], errors="coerce").fillna(5).astype(int) if "Response_Time" in df.columns else 5
    
    # Target column extraction
    target_series = _choose_target_series_from_new_schema(df)
    if target_series is not None:
        out["severity"] = target_series.map(_normalize_severity_value)
    else:
        out["severity"] = "Medium" # Safe fallback
        
    return out

class IncidentModel:
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = os.path.join(_project_root(), "models", "incident_model.pkl")
        self.model_path = model_path
        # Two models:
        # - model_ui: trained on a small set of fields used by the prediction form
        # - model_full: trained on the full "new schema" feature set (best metrics)
        self.model_ui: Any = None
        self.model_full: Any = None

        # Backward-compat (older saved models)
        self.model = None
        self.encoders: Dict[str, Any] = {}
        self.is_loaded = False
        self.feature_columns = ["incident_type_enc", "injuries", "casualties", "location_risk", "weather_enc", "response_time"]
        self.label_encoder = None
        self.metrics = {}
        self.last_trained_schema: Optional[DatasetSchema] = None
        self.last_target_column: Optional[str] = None
        self.label_encoder = LabelEncoder() # For HGBC etc.
        self.metrics_history: list[dict] = [] # Track improvements
        
        # Ensure models directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Try to load existing model
        self.load_model()
        
    def load_model(self):
        """Load trained model from disk if available."""
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)

                # New format
                self.model_ui = data.get("model_ui")
                self.model_full = data.get("model_full")
                self.last_trained_schema = data.get("last_trained_schema")
                self.last_target_column = data.get("last_target_column")
                self.metrics_history = data.get("metrics_history", [])

                # Old format (fallback)
                self.model = data.get("model")
                self.encoders = data.get("encoders", {})
                self.label_encoder = data.get("label_encoder")
                self.metrics = data.get("metrics", {})
                self.is_loaded = bool(self.model_ui is not None or self.model is not None)
                return True
            except Exception as e:
                print(f"Error loading model: {e}")
                
        # If no model found, we'll rely on the rule-based backup in predict
        self.is_loaded = False
        return False

    def train(
        self,
        df: pd.DataFrame,
        *,
        target_column: Optional[str] = None,
        optimize_for: Literal["accuracy", "f1"] = "accuracy",
        max_train_rows: int = 50_000,
    ):
        """
        Train a new model on the provided DataFrame.
        Accepted schemas:
          - legacy: incident_type, injuries, casualties, location_risk, weather, response_time, severity
          - new:    see NEW_DATASET_COLUMNS
        """
        try:
            # Apply auto-mapping first
            df = _auto_map_columns(df)
            
            ok, schema, missing_cols = validate_dataset_columns(df)
            if not ok:
                return {"success": False, "error": f"Missing required columns for {schema} schema: {', '.join(missing_cols)}"}

            detected_schema: DatasetSchema = schema or "legacy"
            self.last_trained_schema = detected_schema

            # If the dataset is very large, cap training rows to keep the app responsive.
            # This is a UI-facing Streamlit app, so "fast enough" is the priority.
            if max_train_rows and max_train_rows > 0 and len(df) > max_train_rows:
                df = df.sample(n=int(max_train_rows), random_state=42).reset_index(drop=True)

            # Always train a UI-compatible model (used by the prediction form)
            df_ui = normalize_training_dataframe(df)
            y_ui = df_ui["severity"].map(_normalize_severity_value).astype(str)
            X_ui = df_ui[["incident_type", "injuries", "casualties", "location_risk", "weather", "response_time"]].copy()

            ui_categorical = ["incident_type", "weather"]
            ui_numeric = ["injuries", "casualties", "location_risk", "response_time"]
            ui_pre = _make_preprocess_pipeline(ui_categorical, ui_numeric)
            ui_clf = RandomForestClassifier(
                n_estimators=120,
                random_state=42,
                class_weight="balanced",
                min_samples_leaf=2,
                max_features="sqrt",
                n_jobs=-1,
            )
            self.model_ui = Pipeline(steps=[("preprocess", ui_pre), ("model", ui_clf)])

            X_ui_train, X_ui_test, y_ui_train, y_ui_test = _safe_train_test_split(X_ui, y_ui)
            self.model_ui.fit(X_ui_train, y_ui_train)

            # For new or hybrid schemas, train a full-feature model
            if detected_schema in ["new", "hybrid"]:
                if target_column and _is_valid_target_column(df, target_column):
                    target_col = target_column
                else:
                    target_col = _choose_target_column_from_new_schema(df)
                self.last_target_column = target_col
                y_full = df[target_col].map(_normalize_severity_value).astype(str)

                # Avoid leakage, but don't unnecessarily drop useful signals.
                # Extract deeper temporal features before dropping Timestamp
                X_full = df.copy()
                if "Timestamp" in X_full.columns:
                    try:
                        ts = pd.to_datetime(X_full["Timestamp"])
                        X_full["is_weekend"] = ts.dt.dayofweek.isin([5, 6]).astype(int)
                        X_full["is_night"] = ts.dt.hour.isin([22, 23, 0, 1, 2, 3, 4, 5]).astype(int)
                        X_full["is_rush_hour"] = ts.dt.hour.isin([7, 8, 9, 16, 17, 18]).astype(int)
                    except:
                        pass

                drop_cols = {"Timestamp"}
                if target_col != "Label" and "Label" in df.columns:
                    drop_cols.add("Label")
                if target_col != "Incident_Severity" and "Incident_Severity" in df.columns:
                    if "Label" in df.columns and _series_equalish(df["Label"], df["Incident_Severity"]):
                        drop_cols.add("Incident_Severity")
                if target_col != "Emergency_Level" and "Emergency_Level" in df.columns:
                    # Emergency_Level is often an input feature; only drop it if it's the chosen target.
                    pass

                # Always drop the training target from features
                drop_cols.add(target_col)

                X_full = X_full.drop(columns=[c for c in drop_cols if c in X_full.columns])

                # Infer feature types from the actual uploaded dataset to avoid
                # brittle hard-coded assumptions (e.g., "Moderate" in Traffic_Congestion).
                full_categorical = X_full.select_dtypes(include=["object"]).columns.tolist()
                full_numeric = [c for c in X_full.columns if c not in full_categorical]

                # v5.0 Hardcore: Include interaction terms AND automated signal filtering
                full_pre = _make_preprocess_pipeline(full_categorical, full_numeric, select_features=True)

                # Train two fast candidates and keep the better one on a held-out split.
                X_full_train, X_full_test, y_full_train, y_full_test = _safe_train_test_split(X_full, y_full)
                
                # v5.0 Hardcore: Balance the training data to counteract 60% baseline bias
                X_full_train, y_full_train = _balance_data(X_full_train, y_full_train)

                candidates: list[tuple[str, Any]] = [
                    (
                        "log_reg",
                        LogisticRegression(
                            max_iter=800,
                            solver="saga",
                        ),
                    ),
                    (
                        "extra_trees",
                        ExtraTreesClassifier(
                            n_estimators=350,
                            random_state=42,
                            class_weight=None,
                            min_samples_leaf=1,
                            max_features="sqrt",
                            bootstrap=True,
                            max_samples=0.8,
                            n_jobs=-1,
                        ),
                    ),
                    (
                        "extra_trees_balanced",
                        ExtraTreesClassifier(
                            n_estimators=350,
                            random_state=42,
                            class_weight="balanced",
                            min_samples_leaf=1,
                            max_features="sqrt",
                            bootstrap=True,
                            max_samples=0.8,
                            n_jobs=-1,
                        ),
                    ),
                    (
                        "random_forest",
                        RandomForestClassifier(
                            n_estimators=250,
                            random_state=42,
                            class_weight=None,
                            min_samples_leaf=1,
                            max_features="sqrt",
                            bootstrap=True,
                            max_samples=0.8,
                            n_jobs=-1,
                        ),
                    ),
                    (
                        "random_forest_balanced",
                        RandomForestClassifier(
                            n_estimators=250,
                            random_state=42,
                            class_weight="balanced",
                            min_samples_leaf=1,
                            max_features="sqrt",
                            bootstrap=True,
                            max_samples=0.8,
                            n_jobs=-1,
                        ),
                    ),
                    (
                        "hist_gradient_boosting",
                        HistGradientBoostingClassifier(
                            max_iter=300,
                            random_state=42,
                            early_stopping=True,
                            validation_fraction=0.1,
                            n_iter_no_change=10,
                            learning_rate=0.05
                        ),
                    ),
                    (
                        "stacking_ensemble",
                        StackingClassifier(
                            estimators=[
                                ("rf", RandomForestClassifier(n_estimators=150, random_state=42, class_weight="balanced")),
                                ("et", ExtraTreesClassifier(n_estimators=200, random_state=42, class_weight="balanced")),
                                ("hgb", HistGradientBoostingClassifier(max_iter=200, random_state=42))
                            ],
                            final_estimator=LogisticRegression(),
                            cv=3,
                            n_jobs=-1
                        )
                    )
                ]

                best_name = None
                best_model = None
                best_acc = -1.0
                best_f1 = -1.0

                # Try each candidate; if one fails to train (e.g. only one class in
                # the training split for LogisticRegression), skip it and move on.
                for name, clf in candidates:
                    try:
                        # v5.0 Hardcore: Calibrate probabilities for sharper decision boundaries
                        calibrated_clf = CalibratedClassifierCV(clf, cv=3)
                        pipe = Pipeline(steps=[("preprocess", full_pre), ("model", calibrated_clf)])
                        pipe.fit(X_full_train, y_full_train)
                        pred = pipe.predict(X_full_test)
                        acc = float(accuracy_score(y_full_test, pred))
                        wf1 = float(f1_score(y_full_test, pred, average="weighted"))
                    except Exception as candidate_err:
                        # Keep training robust: log to console for debugging and
                        # continue with the remaining candidates instead of failing
                        # the entire training run.
                        print(f"[IncidentModel.train] Skipping candidate '{name}' due to error: {candidate_err}")
                        continue

                    score = acc if optimize_for == "accuracy" else wf1
                    best_score = best_acc if optimize_for == "accuracy" else best_f1
                    if score > best_score:
                        best_name = name
                        best_model = pipe
                        best_acc = acc
                        best_f1 = wf1

                if best_model is None:
                    # If every candidate failed, surface a clear error instead of
                    # leaving an unfitted pipeline around.
                    raise RuntimeError(
                        "All full-feature model candidates failed to train. "
                        "Check that your dataset has at least two severity classes "
                        "and reasonable label balance."
                    )

                # Hyperparameter Tuning for the best model candidate
                param_grids = {
                    "random_forest": {
                        "model__n_estimators": [100, 200, 300],
                        "model__max_depth": [None, 10, 20, 30],
                        "model__min_samples_split": [2, 5, 10]
                    },
                    "extra_trees": {
                        "model__n_estimators": [200, 400],
                        "model__max_depth": [None, 20],
                        "model__min_samples_leaf": [1, 2]
                    },
                    "hist_gradient_boosting": {
                        "model__max_iter": [400, 800, 1200],
                        "model__learning_rate": [0.01, 0.05, 0.1, 0.2],
                        "model__max_leaf_nodes": [31, 63, 127],
                        "model__min_samples_leaf": [20, 50, 100],
                    },
                    "stacking_ensemble": {
                        "model__final_estimator__C": [0.1, 1.0, 10.0],
                        "model__cv": [3, 5]
                    }
                }

                if best_name in param_grids:
                    print(f"[IncidentModel.train] Tuning final model '{best_name}'...")
                    # Dynamically adjust CV based on class counts to avoid "n_splits must be at most n_samples" error
                    min_class_size = int(y_full_train.value_counts().min())
                    cv_folds = min(3, min_class_size) if min_class_size >= 2 else None
                    
                    if cv_folds:
                        try:
                            search = RandomizedSearchCV(
                                best_model, 
                                param_grids[best_name], 
                                n_iter=max(20, min(80, len(df)//5)), # v5.0 Exhaustive Search
                                cv=cv_folds, 
                                random_state=42, 
                                n_jobs=-1,
                                scoring="accuracy" if optimize_for == "accuracy" else "f1_weighted"
                            )
                            search.fit(X_full_train, y_full_train)
                            self.model_full = search.best_estimator_
                        except Exception as tuning_err:
                            print(f"[IncidentModel.train] Tuning failed, using base candidate: {tuning_err}")
                            self.model_full = best_model
                    else:
                        print(f"[IncidentModel.train] Not enough samples per class for CV tuning, using base candidate.")
                        self.model_full = best_model
                else:
                    self.model_full = best_model

                y_pred = self.model_full.predict(X_full_test)
                accuracy = accuracy_score(y_full_test, y_pred)
                f1 = f1_score(y_full_test, y_pred, average="weighted")
                precision = float(precision_score(y_full_test, y_pred, average="weighted", zero_division=0))
                recall = float(recall_score(y_full_test, y_pred, average="weighted", zero_division=0))
                classes = sorted(pd.Series(y_full).dropna().astype(str).unique().tolist())
                cm = confusion_matrix(y_full_test, y_pred, labels=classes)

                # Track Feature Importance
                importances = {}
                try:
                    pre = self.model_full.named_steps["preprocess"]
                    cat_features = pre.transformers_[0][1].named_steps["onehot"].get_feature_names_out(full_categorical).tolist()
                    feature_names = cat_features + full_numeric
                    
                    clf = self.model_full.named_steps["model"]
                    if hasattr(clf, "feature_importances_"):
                        raw_importances = clf.feature_importances_
                    elif hasattr(clf, "coef_"):
                        # For models like LogisticRegression, use abs(coef) as importance proxy
                        raw_importances = np.abs(clf.coef_[0])
                    else:
                        raw_importances = None
                        
                    if raw_importances is not None:
                        # Ensure lengths match before zipping
                        if len(feature_names) == len(raw_importances):
                            importances = dict(zip(feature_names, raw_importances.tolist()))
                except Exception as imp_err:
                    print(f"[IncidentModel.train] Could not extract importances: {imp_err}")
                    pass

                class_dist = _value_counts_dict(y_full)
                baseline_accuracy = (max(class_dist.values()) / sum(class_dist.values())) if class_dist else 0.0
                missing_rate = float(X_full.isna().mean().mean()) if len(X_full.columns) else 0.0

                self.metrics = {
                    "accuracy": float(accuracy),
                    "f1": float(f1),
                    "precision": precision,
                    "recall": recall,
                    "confusion_matrix": cm.tolist(),
                    "classes": classes,
                    "schema": detected_schema,
                    "target_column": target_col,
                    "model_type": best_name,
                    "class_distribution": class_dist,
                    "baseline_accuracy": float(baseline_accuracy),
                    "avg_missing_rate": missing_rate,
                    "feature_importances": importances,
                    "timestamp": pd.Timestamp.now().isoformat(),
                    "version": "v5.0-Precision" if best_name == "stacking_ensemble" else ("v3.1-Boosted" if best_name == "hist_gradient_boosting" else "v2.8-Standard")
                }
                self.metrics_history.append({
                    "timestamp": self.metrics["timestamp"],
                    "accuracy": self.metrics["accuracy"],
                    "f1": self.metrics["f1"],
                    "model_type": best_name,
                    "version": self.metrics["version"]
                })
                # Keep last 10 runs
                self.metrics_history = self.metrics_history[-10:]
            else:
                # Legacy schema: metrics from UI model
                y_pred = self.model_ui.predict(X_ui_test)
                accuracy = accuracy_score(y_ui_test, y_pred)
                f1 = f1_score(y_ui_test, y_pred, average="weighted")
                precision = float(precision_score(y_ui_test, y_pred, average="weighted", zero_division=0))
                recall = float(recall_score(y_ui_test, y_pred, average="weighted", zero_division=0))
                classes = sorted(pd.Series(y_ui).dropna().astype(str).unique().tolist())
                cm = confusion_matrix(y_ui_test, y_pred, labels=classes)

                self.metrics = {
                    "accuracy": float(accuracy),
                    "f1": float(f1),
                    "precision": precision,
                    "recall": recall,
                    "confusion_matrix": cm.tolist(),
                    "classes": classes,
                    "schema": "legacy",
                    "target_column": "severity",
                    "class_distribution": _value_counts_dict(y_ui),
                    "baseline_accuracy": float(max(_value_counts_dict(y_ui).values()) / sum(_value_counts_dict(y_ui).values())) if _value_counts_dict(y_ui) else 0.0,
                    "avg_missing_rate": float(X_ui.isna().mean().mean()),
                }

            self.is_loaded = True
            
            # Persist to disk
            joblib.dump({
                "model_ui": self.model_ui,
                "model_full": self.model_full,
                "metrics": self.metrics,
                "metrics_history": self.metrics_history,
                "last_trained_schema": self.last_trained_schema,
                "last_target_column": self.last_target_column,
                # Backward compat keys (kept empty)
                "model": None,
                "encoders": {},
                "label_encoder": None,
            }, self.model_path)
            
            return {
                "success": True,
                "schema": detected_schema,
                "target_column": self.metrics.get("target_column"),
                "accuracy": round(float(self.metrics.get("accuracy", 0.0)), 4),
                "f1_score": round(float(self.metrics.get("f1", 0.0)), 4),
                "samples": int(len(df)),
                "class_distribution": self.metrics.get("class_distribution"),
                "avg_missing_rate": self.metrics.get("avg_missing_rate"),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def harvest_data(self) -> Tuple[Optional[pd.DataFrame], str]:
        """
        Scans the data/ folder, loads all valid CSVs, and merges them into a single training set.
        Returns: (combined_df, status_message)
        """
        data_dir = os.path.join(_project_root(), "data")
        if not os.path.exists(data_dir):
            return None, "Error: 'data/' directory not found."

        csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
        if not csv_files:
            return None, "Error: No CSV files found in 'data/' folder."

        valid_dfs = []
        new_count = 0
        legacy_count = 0
        
        for f in csv_files:
            try:
                fpath = os.path.join(data_dir, f)
                df = pd.read_csv(fpath)
                ok, schema, _ = validate_dataset_columns(df)
                if ok:
                    # If it's legacy, normalize it to new format if possible, 
                    # but for now we prioritize 'new' schema consistency.
                    if schema == "new":
                        valid_dfs.append(df)
                        new_count += 1
                    else:
                        # Normalize legacy to a structure that can be merged or used
                        # For simplicity in this automated pass, we focus on the rich 'new' schema
                        legacy_count += 1
            except:
                continue

        if not valid_dfs:
            if legacy_count > 0:
                return None, f"Found {legacy_count} legacy datasets, but automated training requires 'new' schema datasets for accuracy."
            return None, "No valid training datasets found."

        combined = pd.concat(valid_dfs, ignore_index=True, sort=False)
        msg = f"Harvested {len(combined)} records from {new_count} system datasets."
        return combined, msg

    def auto_train(self) -> Dict[str, Any]:
        """
        Autonomous training entry point: Harvests data, optimizes, and persists.
        """
        df, msg = self.harvest_data()
        if df is None:
            return {"success": False, "error": msg}
        
        # Determine best target and run training
        res = self.train(df, optimize_for="f1")
        if res["success"]:
            res["message"] = msg
        return res

    def predict(self, inputs):
        """
        Make a prediction using the trained model or fallback heuristic.
        inputs: dict with keys matching training features
        """
        # Fallback Heuristic if model not loaded
        # Prefer UI model (works with the prediction form inputs)
        if self.is_loaded and self.model_ui is not None:
            try:
                row = {
                    "incident_type": inputs.get("incident_type", "Other"),
                    "injuries": int(inputs.get("injuries", 0)),
                    "casualties": int(inputs.get("casualties", 0)),
                    "location_risk": int(inputs.get("location_risk", 1)),
                    "weather": inputs.get("weather", "Clear"),
                    "response_time": int(inputs.get("response_time", 5)),
                }
                X = pd.DataFrame([row])
                pred = self.model_ui.predict(X)[0]
                probs = self.model_ui.predict_proba(X)[0]
                confidence = float(max(probs) * 100) if len(probs) else 0.0

                return {
                    "severity_level": str(pred),
                    "confidence_score": round(confidence, 1),
                    "suggested_response": self._get_response_plan(str(pred)),
                }
            except Exception as e:
                print(f"Prediction error (ui model): {e}, falling back to heuristic.")
                return self._heuristic_predict(inputs)

        # Backward-compat fallback (older saved models)
        if not self.is_loaded or self.model is None:
            return self._heuristic_predict(inputs)
            
        try:
            # Prepare Input Vector
            type_enc = self._safe_transform(self.encoders["incident_type"], inputs.get("incident_type", "Other"))
            weather_enc = self._safe_transform(self.encoders["weather"], inputs.get("weather", "Clear"))
            
            features = [[
                type_enc,
                int(inputs.get("injuries", 0)),
                int(inputs.get("casualties", 0)),
                int(inputs.get("location_risk", 1)),
                weather_enc,
                int(inputs.get("response_time", 5))
            ]]
            
            # Predict
            pred_enc = self.model.predict(features)[0]
            severity = self.label_encoder.inverse_transform([pred_enc])[0]
            
            # Confidence (probability of the predicted class)
            probs = self.model.predict_proba(features)[0]
            confidence = max(probs) * 100
            
            return {
                "severity_level": severity,
                "confidence_score": round(confidence, 1),
                "suggested_response": self._get_response_plan(severity)
            }
            
        except Exception as e:
            print(f"Prediction error: {e}, falling back to heuristic.")
            return self._heuristic_predict(inputs)

    def _safe_transform(self, encoder, value):
        """Transform a label safely, handling unseen categories."""
        try:
            return encoder.transform([str(value)])[0]
        except ValueError:
            # If unseen, map to the most common or first class (a simple fallback)
            # Ideally, we should have an 'Unknown' category trained
            return 0 

    def _heuristic_predict(self, inputs):
        """Deterministic rule-based prediction for fallback when no trained model is available.

        This keeps overall behavior similar to the previous heuristic but removes
        randomness so that identical inputs always yield the same output.
        """
        risk_score = 0.0
        type_risk = {"Fire": 30.0, "Medical": 10.0, "Crime": 20.0, "Accident": 15.0}
        risk_score += type_risk.get(inputs.get("incident_type", "Medical"), 10.0)
        risk_score += float(int(inputs.get("injuries", 0))) * 10.0
        risk_score += float(int(inputs.get("casualties", 0))) * 30.0
        risk_score += float(int(inputs.get("location_risk", 1))) * 5.0

        # Normalize into a 0-100 range and keep it stable (no random jitter).
        probability = max(0.0, min(risk_score, 100.0))

        if probability < 30.0:
            level = "Low"
        elif probability < 60.0:
            level = "Medium"
        elif probability < 85.0:
            level = "High"
        else:
            level = "Critical"

        return {
            "severity_level": level,
            "confidence_score": round(probability, 1),
            "suggested_response": self._get_response_plan(level),
        }
        
    def _get_response_plan(self, level):
        plans = {
            "Low": "Dispatch standard patrol unit. Monitor situation.",
            "Medium": "Dispatch priority unit + ambulance if injuries reported.",
            "High": "Dispatch multiple units, fire/EMS support. Alert local command.",
            "Critical": "FULL EMERGENCY RESPONSE. Dispatch SWAT/Hazmat/Air support. Notify HQ."
        }
        return plans.get(level, "Assess situation.")

# Singleton instance
model_instance = IncidentModel()
