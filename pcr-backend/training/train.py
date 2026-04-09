"""
SAP PCR Intent Classifier — Training Script
Trains a TF-IDF + Logistic Regression pipeline on the expanded 14-intent dataset.
"""

import pandas as pd
import os
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report
import numpy as np

DATA_PATH  = os.path.join(os.path.dirname(__file__), "dataset.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../model/intent_model.pkl")


def train():
    df = pd.read_csv(DATA_PATH)
    print(f"Dataset: {len(df)} samples, {df['intent'].nunique()} intents")
    print(df["intent"].value_counts().to_string())
    print()

    X = df["prompt"]
    y = df["intent"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 3),       # unigrams, bigrams, trigrams
            stop_words="english",
            min_df=2,                 # ignore very rare terms
            sublinear_tf=True,        # log-scale TF (better for short texts)
            analyzer="word",
        )),
        ("clf", LogisticRegression(
            max_iter=3000,
            class_weight="balanced",  # handles uneven class sizes
            C=2.0,                    # slightly stronger regularisation
            solver="lbfgs",
        )),
    ])

    # ── Cross-validation first ──────────────────────────────
    cv     = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring="f1_macro")
    print(f"5-fold CV F1 (macro): {scores.mean():.3f} ± {scores.std():.3f}\n")

    # ── Final fit + evaluation ──────────────────────────────
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("Test Set Evaluation:")
    print(classification_report(y_test, y_pred, digits=3))

    # ── Confidence check on a few examples ──────────────────
    examples = [
        "Calculate overtime at 150% for hours above 8 in wage type 1000",
        "Copy wage type 2000 to 9000",
        "Multiply rate from 1000 by hours from 2000 into 3000",
        "Deduct 20% income tax from gross pay 1000, store in 8000",
        "Add housing allowance 5000 to pay",
        "Sum wage types 1000 2000 3000 into 9999",
        "If hours in 3000 exceed 8 pay 150% of 1000 into 9000",
    ]
    print("Confidence spot-check:")
    for ex in examples:
        proba  = model.predict_proba([ex])[0]
        intent = model.classes_[proba.argmax()]
        conf   = proba.max()
        print(f"  [{conf:.2f}] {intent:20s} | {ex}")

    # ── Save ────────────────────────────────────────────────
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved → {MODEL_PATH}")


if __name__ == "__main__":
    train()