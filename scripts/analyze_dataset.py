import pandas as pd


def main() -> None:
    p = "data/Emergency_Service_Routing_Cleaned.csv"
    df = pd.read_csv(p)

    print("rows", len(df), "cols", len(df.columns))
    print("\ncolumns:")
    print(df.columns.tolist())

    print("\n--- dtypes ---")
    print(df.dtypes)

    cols_to_check = [
        "Incident_Severity",
        "Incident_Type",
        "Region_Type",
        "Traffic_Congestion",
        "Weather_Condition",
        "Drone_Availability",
        "Ambulance_Availability",
        "Air_Traffic",
        "Specialist_Availability",
        "Road_Type",
        "Emergency_Level",
        "Weather_Impact",
        "Dispatch_Coordinator",
        "Label",
        "Day_of_Week",
    ]
    for c in cols_to_check:
        if c not in df.columns:
            continue
        print(f"\n--- top values: {c} ---")
        print(df[c].astype(str).value_counts().head(20))

    numeric_cols = [
        "Battery_Life",
        "Response_Time",
        "Hospital_Capacity",
        "Distance_to_Incident",
        "Number_of_Injuries",
        "Drone_Speed",
        "Ambulance_Speed",
        "Payload_Weight",
        "Fuel_Level",
        "Hour",
    ]
    for c in numeric_cols:
        if c not in df.columns:
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        print(f"\n--- numeric summary: {c} ---")
        print("missing", int(s.isna().sum()), "min", s.min(), "max", s.max(), "mean", s.mean())


if __name__ == "__main__":
    main()

