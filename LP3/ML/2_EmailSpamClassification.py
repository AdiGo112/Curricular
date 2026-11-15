from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import PrecisionRecallDisplay, RocCurveDisplay, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

HERE = Path(__file__).parent
DATA = HERE / "data"
if not DATA.exists():
    DATA = HERE

if (DATA / "emails.csv").exists():
    df = pd.read_csv(DATA / "emails.csv").drop(columns="Email No.")
else:
    df = pd.read_csv(DATA / "spambase.data", header=None)

X, y = df.iloc[:, :-1], df.iloc[:, -1]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

models = {"KNN": KNeighborsClassifier(), "SVM": SVC()}
for name, model in models.items():
    pred = model.fit(X_train, y_train).predict(X_test)
    print(name)
    print(confusion_matrix(y_test, pred))
    print(classification_report(y_test, pred))

plots = {"roc_curve.png": RocCurveDisplay, "precision_recall_curve.png": PrecisionRecallDisplay}
for file, display in plots.items():
    ax = plt.subplots()[1]
    for name, model in models.items():
        display.from_estimator(model, X_test, y_test, name=name, ax=ax)
    plt.savefig(HERE / file)
    plt.show()
