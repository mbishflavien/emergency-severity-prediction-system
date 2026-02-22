"""
Fast Emergency Response Model Trainer
Optimized for quick training with good accuracy
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    classification_report
)
import joblib
import warnings
import json
warnings.filterwarnings('ignore')

print("=" * 80, flush=True)
print("Fast Emergency Response Model Training", flush=True)
print("=" * 80, flush=True)

try:
    # Load data
    print("\n[1/6] Loading data...", flush=True)
    df = pd.read_csv('data/Emergency_Service_Routing_Cleaned.csv')
    print(f"Dataset shape: {df.shape}", flush=True)
    
    # Feature preprocessing
    print("\n[2/6] Preparing features...", flush=True)
    df_processed = df.copy()
    
    # Drop timestamp
    if 'Timestamp' in df_processed.columns:
        df_processed = df_processed.drop('Timestamp', axis=1)
    
    # Store target
    target = df_processed['Label'].copy()
    X = df_processed.drop('Label', axis=1)
    
    # Encode categorical variables using One-Hot Encoding
    print("  - One-hot encoding categorical features", flush=True)
    categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
    X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # Encode target
    target_encoder = LabelEncoder()
    y = target_encoder.fit_transform(target)
    
    print(f"  - Features: {X.shape[1]}", flush=True)
    print(f"  - Classes: {list(target_encoder.classes_)}", flush=True)
    
    # Normalize features
    print("  - Normalizing features", flush=True)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split data
    print("\n[3/6] Splitting data...", flush=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.15, random_state=42, stratify=y
    )
    print(f"  - Train set: {X_train.shape}", flush=True)
    print(f"  - Test set: {X_test.shape}", flush=True)
    
    # Train Random Forest
    print("\n[4/6] Training Random Forest...", flush=True)
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features='sqrt',
        n_jobs=-1,
        random_state=42,
        class_weight='balanced'
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    test_acc = accuracy_score(y_test, rf_pred)
    
    print(f"  - Test Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)", flush=True)
    
    # Cross-validation
    print("\n[5/6] Cross-validation...", flush=True)
    cv_scores = cross_val_score(
        rf, X_train, y_train,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        scoring='accuracy', n_jobs=-1
    )
    print(f"  - CV Mean: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})", flush=True)
    
    # Results
    print("\n[6/6] Final Results:", flush=True)
    print("=" * 80, flush=True)
    test_prec = precision_score(y_test, rf_pred, average='weighted', zero_division=0)
    test_rec = recall_score(y_test, rf_pred, average='weighted', zero_division=0)
    test_f1 = f1_score(y_test, rf_pred, average='weighted', zero_division=0)
    
    print(f"✓ TEST ACCURACY: {test_acc:.4f} ({test_acc*100:.2f}%)", flush=True)
    print(f"✓ Precision: {test_prec:.4f}", flush=True)
    print(f"✓ Recall: {test_rec:.4f}", flush=True)
    print(f"✓ F1-Score: {test_f1:.4f}", flush=True)
    print(f"✓ CV Mean: {cv_scores.mean():.4f}", flush=True)
    
    print("\nClassification Report:", flush=True)
    print(classification_report(y_test, rf_pred, target_names=target_encoder.classes_, zero_division=0))
    
    if test_acc >= 0.90:
        print("\n✓✓✓ SUCCESS: Model achieves 90%+ accuracy! ✓✓✓", flush=True)
    elif test_acc >= 0.80:
        print("\n✓ Good accuracy achieved (80%+)", flush=True)
    
    # Save model
    print("\nSaving model...", flush=True)
    model_data = {
        'model': rf,
        'scaler': scaler,
        'target_encoder': target_encoder,
        'feature_names': X.columns.tolist(),
        'accuracy': test_acc
    }
    
    joblib.dump(model_data, 'models/incident_model.pkl')
    print("✓ Model saved", flush=True)
    
    # Save metadata
    metadata = {
        'test_accuracy': float(test_acc),
        'test_precision': float(test_prec),
        'test_recall': float(test_rec),
        'test_f1': float(test_f1),
        'cv_mean': float(cv_scores.mean()),
        'cv_std': float(cv_scores.std()),
        'classes': target_encoder.classes_.tolist(),
        'feature_count': X_scaled.shape[1],
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'model_type': 'Random Forest Classifier',
        'status': 'success',
        'encoding_type': 'one-hot'
    }
    
    with open('models/model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print("✓ Metadata saved", flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("✓ Training Complete!", flush=True)
    print("=" * 80 + "\n", flush=True)

except Exception as e:
    print(f"\nERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
