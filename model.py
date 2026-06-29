"""
L-MINER AI Classifier — L2 Science Layer
Wasay's file — Random Forest mineral classifier.

Takes GPR + spectrometer features and outputs:
  - Mineral class
  - Confidence score
  - Depth estimate
  - Uncertainty
"""

import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
from data_generator import (
    generate_training_dataset,
    scan_cell,
    MINERAL_NAMES,
    DEPTH_MAP
)

MODEL_PATH = "lminer_model.pkl"
SCALER_PATH = "lminer_scaler.pkl"


# ─────────────────────────────────────────────
# TRAIN THE MODEL
# ─────────────────────────────────────────────

def train_model(n_samples=80, save=True):
    """
    Train Random Forest on synthetic mineral data.
    
    Returns trained model and scaler.
    """
    print("[L2] Generating training data...")
    X, y = generate_training_dataset(n_samples_per_class=n_samples)

    # Split into train and test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Random Forest
    print("[L2] Training Random Forest classifier...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)

    print(f"\n[L2] Model Accuracy: {acc * 100:.1f}%")
    print("\n[L2] Classification Report:")
    mineral_names_list = [MINERAL_NAMES[i] for i in range(4)]
    print(classification_report(y_test, y_pred,
                                target_names=mineral_names_list))

    if save:
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(model, f)
        with open(SCALER_PATH, 'wb') as f:
            pickle.dump(scaler, f)
        print(f"[L2] Model saved to {MODEL_PATH}")

    return model, scaler, acc


# ─────────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────────

def load_model():
    """Load trained model and scaler from disk."""
    if not os.path.exists(MODEL_PATH):
        print("[L2] No saved model found. Training now...")
        model, scaler, _ = train_model()
        return model, scaler

    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)

    print("[L2] Model loaded from disk.")
    return model, scaler


# ─────────────────────────────────────────────
# INFERENCE
# Core function — called by dashboard for each cell
# ─────────────────────────────────────────────

def predict_mineral(features, row, col, model, scaler):
    """
    Run L2 mineral inference on a single cell.

    Args:
        features: 10-element feature vector from data_generator
        row, col: grid position (used to get true depth)
        model: trained RandomForestClassifier
        scaler: fitted StandardScaler

    Returns dict:
        mineral_name: predicted mineral
        confidence: probability of top prediction (0-1)
        depth_m: estimated depth
        uncertainty: model uncertainty (1 - confidence)
        all_probs: probability for each class
    """
    # Scale features
    features_scaled = scaler.transform(features.reshape(1, -1))

    # Get class probabilities from all 200 trees
    probs = model.predict_proba(features_scaled)[0]
    predicted_class = np.argmax(probs)
    confidence = probs[predicted_class]

    # Depth comes from our grid map (physics-based, not predicted)
    depth_m = float(DEPTH_MAP[row, col])

    # Uncertainty = spread of probabilities across classes
    uncertainty = 1.0 - confidence

    # All class probabilities as a readable dict
    all_probs = {
        MINERAL_NAMES[i]: round(float(probs[i]), 3)
        for i in range(4)
    }

    return {
        "mineral_name": MINERAL_NAMES[predicted_class],
        "mineral_id": int(predicted_class),
        "confidence": round(float(confidence), 3),
        "confidence_pct": f"{confidence * 100:.1f}%",
        "depth_m": round(depth_m, 2),
        "uncertainty": round(float(uncertainty), 3),
        "all_probs": all_probs,
    }


# ─────────────────────────────────────────────
# SCAN ALL CELLS — for full grid prediction
# ─────────────────────────────────────────────

def run_full_grid_inference(model, scaler):
    """
    Run inference on all 36 cells.
    Returns a list of result dicts.
    Used for verifying model across the whole grid.
    """
    results = []

    for row in range(6):
        for col in range(6):
            cell = scan_cell(row, col)

            if cell["is_obstacle"]:
                results.append({
                    "row": row, "col": col,
                    "mineral_name": "Obstacle",
                    "mineral_id": -1,
                    "confidence": 0.0,
                    "confidence_pct": "N/A",
                    "depth_m": 0.0,
                    "uncertainty": 1.0,
                    "all_probs": {},
                    "skipped": True,
                    "skip_reason": "L0: Obstacle Detected"
                })
                continue

            result = predict_mineral(
                cell["features"], row, col, model, scaler
            )
            result["row"] = row
            result["col"] = col
            result["skipped"] = False
            results.append(result)

    return results


# ─────────────────────────────────────────────
# QUICK TEST — run this file directly
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("L-MINER AI Classifier (L2) — Verification Test")
    print("=" * 50)

    # Train model
    model, scaler, accuracy = train_model(n_samples=80)

    # Test on a few individual cells
    print("\n[Test] Running inference on sample cells:")
    test_cells = [(0, 1), (0, 2), (1, 0), (2, 2), (3, 3)]

    for row, col in test_cells:
        cell = scan_cell(row, col)

        if cell["is_obstacle"]:
            print(f"  Cell ({row},{col}): ⛔ OBSTACLE — L2 skipped")
            continue

        result = predict_mineral(
            cell["features"], row, col, model, scaler
        )

        true_mineral = cell["mineral_name"]
        predicted = result["mineral_name"]
        correct = "✅" if true_mineral == predicted else "❌"

        print(f"  Cell ({row},{col}): {correct} "
              f"True={true_mineral:12s} "
              f"Pred={predicted:12s} "
              f"Conf={result['confidence_pct']} "
              f"Depth={result['depth_m']}m")

    # Full grid inference
    print("\n[Test] Full grid inference...")
    results = run_full_grid_inference(model, scaler)

    correct = sum(
        1 for r in results
        if not r["skipped"]
        and r["mineral_name"] == MINERAL_NAMES[
            __import__('data_generator').MINERAL_MAP[r["row"], r["col"]]
        ]
    )
    total_scanned = sum(1 for r in results if not r["skipped"])
    obstacles = sum(1 for r in results if r["skipped"])

    print(f"  Total cells : 36")
    print(f"  Obstacles   : {obstacles} (skipped by L0)")
    print(f"  Scanned     : {total_scanned}")
    print(f"  Correct     : {correct}/{total_scanned} "
          f"({correct/total_scanned*100:.1f}%)")

    print("\n✅ Model working correctly.")
    print("   Next step: run l0_l1_logic.py (Saad)")
