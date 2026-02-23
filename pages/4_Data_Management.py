import streamlit as st
import pandas as pd
from utils.auth import require_login
from utils.ui_components import load_css, render_header, icon_header
from utils.icon_library import get_icon
from utils.model_loader import (
    model_instance,
    NEW_DATASET_COLUMNS,
    LEGACY_DATASET_COLUMNS,
    validate_dataset_columns,
)

st.set_page_config(page_title="Data | EMS", page_icon="", layout="wide")
load_css()
require_login()

# Header
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
        {get_icon("dashboard", size=36, color="#f59e0b")}
        <div>
            <h1 style="margin: 0; font-size: 2rem;">Data Management</h1>
            <p style="margin: 0; color: #94a3b8;">System Records & Logs</p>
        </div>
    </div>
    <hr style="border-color: rgba(148, 163, 184, 0.1); margin-bottom: 30px;">
    """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    icon_header("Upload New Dataset", "activity", level=3)
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Validate columns
            ok, schema, missing = validate_dataset_columns(df)

            if not ok:
                st.error(f"Missing required columns for `{schema}` schema: {', '.join(missing)}")
                st.info("Check 'Expected Format' below for the correct structure.")
            else:
                st.session_state['uploaded_data'] = df
                st.success(f"File Uploaded & Validated Successfully! (Detected: `{schema}` schema)")
                
        except Exception as e:
            st.error(f"Error reading file: {e}")
        
    st.markdown("---")
    icon_header("Model Maintenance", "analytics", level=3)
    
    if st.button("Trigger Model Retraining"):
        if 'uploaded_data' in st.session_state:
            with st.status("Retraining Model...", expanded=True) as status:
                st.write("Preprocessing data...")
                # Call real training method
                target_choice = st.session_state.get("training_target_choice", "Auto")
                target_column = None
                if target_choice == "Incident_Severity":
                    target_column = "Incident_Severity"
                elif target_choice == "Label":
                    target_column = "Label"

                optimize_for = "accuracy" if st.session_state.get("optimize_for_choice", "Accuracy") == "Accuracy" else "f1"
                max_train_rows = int(st.session_state.get("max_train_rows", 50000))

                result = model_instance.train(
                    st.session_state["uploaded_data"],
                    target_column=target_column,
                    optimize_for=optimize_for,
                    max_train_rows=max_train_rows,
                )
                
                if result.get("success"):
                    st.write(f"Training Complete! Accuracy: {result['accuracy']:.2%}")
                    st.write(f"F1 Score: {result['f1_score']:.2%}")
                    st.write(f"Schema: `{result.get('schema')}` | Target: `{result.get('target_column')}`")
                    if result.get("avg_missing_rate") is not None:
                        st.caption(f"Avg missing rate (features): {float(result['avg_missing_rate'])*100:.1f}%")
                    if result.get("class_distribution"):
                        st.caption(f"Class distribution: {result['class_distribution']}")
                    status.update(label="Retraining Complete!", state="complete", expanded=False)
                    st.success(f"Model v2.5 deployed successfully (Acc: {result['accuracy']:.2%})")
                else:
                    status.update(label="Retraining Failed!", state="error", expanded=False)
                    st.error(f"Training failed: {result.get('error')}")
        else:
            st.warning("Please upload a dataset first.")

    st.markdown("###")
    st.caption("Training target (new schema only):")
    st.selectbox(
        "Target column",
        options=["Auto", "Incident_Severity", "Label"],
        index=0,
        key="training_target_choice",
        help="Auto uses severity classes if detected. Choose Label to train a dispatch-decision model.",
        label_visibility="collapsed",
    )

    st.caption("Optimize for:")
    st.selectbox(
        "Optimize for",
        options=["Accuracy", "F1"],
        index=0,
        key="optimize_for_choice",
        help="Accuracy favors overall correctness; F1 is more balanced across classes.",
        label_visibility="collapsed",
    )

    st.caption("Max training rows (speed vs quality):")
    st.slider(
        "Max training rows",
        min_value=10_000,
        max_value=200_000,
        value=50_000,
        step=10_000,
        key="max_train_rows",
        label_visibility="collapsed",
        help="If your dataset is larger, training will sample this many rows to keep retraining responsive.",
    )

with col2:
    icon_header("Dataset Preview", "list", level=3)
    if 'uploaded_data' in st.session_state:
        df_preview = st.session_state["uploaded_data"]
        max_preview_rows = 5000
        if len(df_preview) > max_preview_rows:
            st.info(f"Showing first {max_preview_rows:,} rows of {len(df_preview):,} (preview limited for performance).")
            st.dataframe(df_preview.head(max_preview_rows), use_container_width=True)
        else:
            st.dataframe(df_preview, use_container_width=True)
    else:
        st.info("Upload a CSV file to preview data.")
        st.markdown("Expected Format (New Dataset Columns):")
        sample_new = pd.DataFrame(
            [
                {
                    "Timestamp": "2026-01-15 13:05:00",
                    "Incident_Severity": "High",
                    "Incident_Type": "Fire",
                    "Region_Type": "Urban",
                    "Traffic_Congestion": 7,
                    "Weather_Condition": "Rain",
                    "Drone_Availability": 1,
                    "Ambulance_Availability": 1,
                    "Battery_Life": 82,
                    "Air_Traffic": 3,
                    "Response_Time": 9,
                    "Hospital_Capacity": 65,
                    "Distance_to_Incident": 4.2,
                    "Number_of_Injuries": 2,
                    "Specialist_Availability": 1,
                    "Road_Type": "Paved",
                    "Emergency_Level": "High",
                    "Drone_Speed": 55,
                    "Ambulance_Speed": 45,
                    "Payload_Weight": 2.5,
                    "Fuel_Level": 73,
                    "Weather_Impact": 6,
                    "Dispatch_Coordinator": "Operator-A",
                    "Label": "High",
                    "Hour": 13,
                    "Day_of_Week": "Wednesday",
                },
                {
                    "Timestamp": "2026-01-16 22:40:00",
                    "Incident_Severity": "Low",
                    "Incident_Type": "Medical",
                    "Region_Type": "Suburban",
                    "Traffic_Congestion": 2,
                    "Weather_Condition": "Clear",
                    "Drone_Availability": 1,
                    "Ambulance_Availability": 0,
                    "Battery_Life": 41,
                    "Air_Traffic": 1,
                    "Response_Time": 14,
                    "Hospital_Capacity": 40,
                    "Distance_to_Incident": 12.7,
                    "Number_of_Injuries": 0,
                    "Specialist_Availability": 0,
                    "Road_Type": "Unpaved",
                    "Emergency_Level": "Low",
                    "Drone_Speed": 45,
                    "Ambulance_Speed": 35,
                    "Payload_Weight": 1.2,
                    "Fuel_Level": 25,
                    "Weather_Impact": 1,
                    "Dispatch_Coordinator": "Operator-B",
                    "Label": "Low",
                    "Hour": 22,
                    "Day_of_Week": "Thursday",
                },
            ]
        )
        # Ensure column order matches expectation
        sample_new = sample_new[NEW_DATASET_COLUMNS]
        st.dataframe(sample_new, hide_index=True)

        with st.expander("Legacy Dataset Columns (also accepted)"):
            st.code(", ".join(LEGACY_DATASET_COLUMNS))
