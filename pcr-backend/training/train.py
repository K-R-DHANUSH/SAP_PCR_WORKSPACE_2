import pandas as pd
import os
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

DATA_PATH = os.path.join(os.path.dirname(__file__), "dataset.csv")
MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "../model/intent_model.pkl"
)

def train():
    df = pd.read_csv(DATA_PATH)

    X = df["prompt"]
    y = df["intent"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 3),
            stop_words="english"
        )),
        ("clf", LogisticRegression(
            max_iter=2000,
            class_weight="balanced"
        ))
    ])

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("\nModel Evaluation:\n")
    print(classification_report(y_test, y_pred))

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()