import pandas as pd
import joblib
import os
from typing import Any, Dict, Literal, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix
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


DatasetSchema = Literal["legacy", "new"]


def _has_all_columns(df: pd.DataFrame, cols: list[str]) -> bool:
    df_cols = set(df.columns.astype(str))
    return all(c in df_cols for c in cols)


def detect_dataset_schema(df: pd.DataFrame) -> Optional[DatasetSchema]:
    if _has_all_columns(df, NEW_DATASET_COLUMNS):
        return "new"
    if _has_all_columns(df, LEGACY_DATASET_COLUMNS):
        return "legacy"
    return None


def validate_dataset_columns(df: pd.DataFrame) -> Tuple[bool, Optional[DatasetSchema], list[str]]:
    """
    Returns:
      (ok, schema, missing_columns)
    """
    schema = detect_dataset_schema(df)
    if schema == "new":
        missing = [c for c in NEW_DATASET_COLUMNS if c not in df.columns]
        return True, schema, missing
    if schema == "legacy":
        missing = [c for c in LEGACY_DATASET_COLUMNS if c not in df.columns]
        return True, schema, missing

    missing_new = [c for c in NEW_DATASET_COLUMNS if c not in df.columns]
    missing_legacy = [c for c in LEGACY_DATASET_COLUMNS if c not in df.columns]
    # Prefer reporting missing columns for the new schema (what the UI expects now),
    # but if legacy is "closer", report that instead.
    if len(missing_legacy) < len(missing_new):
        return False, "legacy", missing_legacy
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
    Preference: Label → Incident_Severity → Emergency_Level
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


def _make_preprocess_pipeline(categorical: list[str], numeric: list[str]) -> ColumnTransformer:
    cat_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    num_pipe = Pipeline(
        steps=[
            ("coerce", FunctionTransformer(coerce_numeric, feature_names_out="one-to-one")),
            # Use a robust numeric imputer that prefers per-feature medians but
            # safely falls back to a constant when a column becomes all-NaN
            # after coercion (e.g., values like \"Moderate\" in a numeric field).
            ("imputer", RobustNumericImputer(strategy="median", fill_value=0.0)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("cat", cat_pipe, categorical),
            ("num", num_pipe, numeric),
        ],
        remainder="drop",
    )


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

    if schema != "new":
        raise ValueError("Unsupported dataset schema. Expected legacy or new columns.")

    out = pd.DataFrame()
    out["incident_type"] = df["Incident_Type"].astype(str)
    out["injuries"] = pd.to_numeric(df["Number_of_Injuries"], errors="coerce").fillna(0).astype(int)
    out["casualties"] = 0

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
            scaled = 1 + 9 * ((risk - rmin) / (rmax - rmin))
            out["location_risk"] = scaled.clip(1, 10).fillna(5).round().astype(int)

    out["weather"] = df["Weather_Condition"].astype(str)
    out["response_time"] = pd.to_numeric(df["Response_Time"], errors="coerce").fillna(0).astype(int)
    out["severity"] = _choose_target_series_from_new_schema(df)
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

            # For the new schema, also train a full-feature model (better metrics)
            if detected_schema == "new":
                if target_column and _is_valid_target_column(df, target_column):
                    target_col = target_column
                else:
                    target_col = _choose_target_column_from_new_schema(df)
                self.last_target_column = target_col
                y_full = df[target_col].map(_normalize_severity_value).astype(str)

                # Avoid leakage, but don't unnecessarily drop useful signals.
                # If Label and Incident_Severity are (almost) identical, treat them as aliases (drop the non-target alias).
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

                X_full = df.drop(columns=[c for c in drop_cols if c in df.columns]).copy()

                # Infer feature types from the actual uploaded dataset to avoid
                # brittle hard-coded assumptions (e.g., "Moderate" in Traffic_Congestion).
                full_categorical = X_full.select_dtypes(include=["object"]).columns.tolist()
                full_numeric = [c for c in X_full.columns if c not in full_categorical]

                full_pre = _make_preprocess_pipeline(full_categorical, full_numeric)

                # Train two fast candidates and keep the better one on a held-out split.
                X_full_train, X_full_test, y_full_train, y_full_test = _safe_train_test_split(X_full, y_full)

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
                ]

                best_name = None
                best_model = None
                best_acc = -1.0
                best_f1 = -1.0

                # Try each candidate; if one fails to train (e.g. only one class in
                # the training split for LogisticRegression), skip it and move on.
                for name, clf in candidates:
                    try:
                        pipe = Pipeline(steps=[("preprocess", full_pre), ("model", clf)])
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

                self.model_full = best_model

                y_pred = self.model_full.predict(X_full_test)
                accuracy = best_acc
                f1 = best_f1
                precision = float(precision_score(y_full_test, y_pred, average="weighted", zero_division=0))
                recall = float(recall_score(y_full_test, y_pred, average="weighted", zero_division=0))
                classes = sorted(pd.Series(y_full).dropna().astype(str).unique().tolist())
                cm = confusion_matrix(y_full_test, y_pred, labels=classes)

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
                    "schema": "new",
                    "target_column": target_col,
                    "model_type": best_name,
                    "class_distribution": class_dist,
                    "baseline_accuracy": float(baseline_accuracy),
                    "avg_missing_rate": missing_rate,
                }
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

        # Normalize into a 0–100 range and keep it stable (no random jitter).
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
