from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).parent
DATA = HERE / "data" / "Churn_Modelling.csv"
if not DATA.exists():
    DATA = HERE / "Churn_Modelling.csv"

df = pd.read_csv(DATA)
X = pd.get_dummies(df.drop(columns=["RowNumber", "CustomerId", "Surname", "Exited"]), drop_first=True)
y = df.Exited
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

model = MLPClassifier(hidden_layer_sizes=(16, 8), max_iter=500, random_state=42)
pred = model.fit(X_train, y_train).predict(X_test)

print("Accuracy:", round(accuracy_score(y_test, pred), 3))
print(confusion_matrix(y_test, pred))

ConfusionMatrixDisplay.from_predictions(y_test, pred, display_labels=["Stayed", "Churned"])
plt.savefig(HERE / "confusion_matrix.png")
