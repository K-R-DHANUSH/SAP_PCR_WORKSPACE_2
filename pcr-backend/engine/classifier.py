import joblib
import os

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "../model/intent_model.pkl"
)

model = joblib.load(MODEL_PATH)

def classify(prompt: str):
    probs = model.predict_proba([prompt])[0]
    intent = model.classes_[probs.argmax()]
    confidence = float(probs.max())

    return intent, confidence