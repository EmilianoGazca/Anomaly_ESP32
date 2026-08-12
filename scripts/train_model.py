import os
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

#1. Import the dataset
DATASET_PATH = os.path.join("data", "telemetry_dataset.csv")
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "vibration_anomaly_model.pkl")

print("Loading dataset...")
df = pd.read_csv(DATASET_PATH)

#2. Clasify features(x) and labels(y)
#Ignore 'timestamp', it doesn't changue on the vibration physics
x = df[["rms_x", "rms_y", "rms_z", "std_x", "std_y", "std_z"]]
y = df["label"]

#3. Clasify in Training set (80%) and Test set(20%)
x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42, stratify=y
)
#4. Train the Model(Random Forest)
print("Training Random Forest Model...")
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(x_train, y_train)

#5. Evaluate accuracy
y_pred = clf.predict(x_test)
accuracy = accuracy_score(y_test, y_pred)

print("\n" + "="*40)
print(f"Accuracy Model: {accuracy * 100:.2f}")
print("="*40)
print("\n Classification report")
print(classification_report(y_test, y_pred))

#6. Save the trained model
os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(clf, MODEL_PATH)
print(f"\n Model saved succesfully on {MODEL_PATH}")
