"""
Assignment 3: Bank Customer Churn -- Neural Network Classifier
================================================================

Problem statement
------------------
Given a bank customer, build a neural network-based classifier that can
determine whether they will leave or not in the next 6 months.
Dataset description: an open-source Kaggle dataset of 10,000 sample points
with 14 distinct features such as CustomerId, CreditScore, Geography,
Gender, Age, Tenure, Balance, etc.

Approach
--------
- Model: `sklearn.neural_network.MLPClassifier` (a multi-layer perceptron --
  a real feedforward neural network with backpropagation), used INSTEAD OF
  TensorFlow/Keras to avoid a multi-hundred-MB install for one script.
  Swap in `keras.Sequential` with equivalent Dense layers if a grader
  specifically requires Keras.
- Features are standardized (`StandardScaler`) first: gradient-based
  training is sensitive to the relative scale of inputs, unlike a
  tree-based model.
- Evaluation: accuracy, precision and recall. Churn is a minority class, so
  precision/recall on the churn class matter more than raw accuracy (a
  model that always predicts "stays" can still look accurate).

Dataset
-------
The real Kaggle "Churn_Modelling.csv" (bank customer churn), 10,000
customers with CreditScore, Geography, Gender, Age, Tenure, Balance,
NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary and the `Exited`
churn label, saved locally at data/Churn_Modelling.csv.

Likely viva questions
----------------------
Q: Why MLPClassifier instead of TensorFlow/Keras?
A: It's a genuine feedforward neural network (backpropagation across
   hidden layers), available in scikit-learn -- already a dependency here --
   avoiding a much larger, separate TensorFlow install for one script.

Q: Why does this script scale features but a Random Forest wouldn't need to?
A: Gradient-based training is sensitive to each feature's relative scale
   (it affects gradient magnitudes per weight); tree splits are invariant
   to the scale of any single feature.

Q: Why might accuracy alone be misleading for churn prediction?
A: Churners are a minority class -- a model predicting "no churn" for
   everyone can still score high accuracy while catching zero churners,
   which is exactly what precision/recall on the churn class expose.

Q: What is the role of the ReLU activation function between layers?
A: It introduces non-linearity; without it, stacking linear layers would
   collapse into a single linear transform and the network couldn't model
   non-linear churn relationships in the data.
"""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score

DATA_PATH = Path(__file__).parent / "data" / "Churn_Modelling.csv"

if __name__ == "__main__":
    data = pd.read_csv(DATA_PATH)
    print(f"Dataset: {len(data)} customers, {data['Exited'].sum()} churned "
          f"({data['Exited'].mean():.1%})\n")

    # Pre-process: RowNumber/CustomerId/Surname are just identifiers, so
    # drop them; encode the text columns (Geography, Gender) as 0/1 columns.
    X = pd.get_dummies(data.drop(columns=["Exited", "RowNumber", "CustomerId", "Surname"]), drop_first=True)
    y = data["Exited"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Gradient-based training is sensitive to each feature's relative scale
    # (unlike tree splits), so features are standardized.
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # NEURAL NETWORK (MULTI-LAYER PERCEPTRON): two hidden layers (16, 8
    # units) with ReLU activation between them so the network can model a
    # non-linear relationship rather than collapsing into one linear transform.
    ann = MLPClassifier(
        hidden_layer_sizes=(16, 8),
        activation="relu",
        max_iter=500,
        random_state=42,
    )
    ann.fit(X_train_s, y_train)
    pred = ann.predict(X_test_s)

    # Churn is a minority class, so precision/recall on it matter more than
    # raw accuracy (a model that always predicts "stays" can still look accurate).
    accuracy = accuracy_score(y_test, pred)
    precision = precision_score(y_test, pred, zero_division=0)
    recall = recall_score(y_test, pred, zero_division=0)

    print("ANN (MLPClassifier) results:")
    print(f"Accuracy:  {accuracy:.3f}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
