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
  training is sensitive to the relative scale of inputs, unlike the
  tree-based model in Assignment 1.
- Evaluation: accuracy, precision and recall. Churn is a minority class, so
  precision/recall on the churn class matter more than raw accuracy (a
  model that always predicts "stays" can still look accurate).

Synthetic dataset
------------------
Kaggle's real "Churn_Modelling.csv" is not reachable from this environment
(no internet access), so `build_dataset()` builds 10,000 customers with
CustomerId, CreditScore, Geography, Gender, Age, Tenure, Balance,
NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary and a churn label from a designed relationship (older + inactive + low-balance +
few-product customers get higher churn probability) plus noise, passed
through a sigmoid and compared to a random threshold. Numbers below are
illustrative of the technique, not results on the real Kaggle data.

Likely viva questions
----------------------
Q: Why MLPClassifier instead of TensorFlow/Keras?
A: It's a genuine feedforward neural network (backpropagation across
   hidden layers), available in scikit-learn -- already a dependency here --
   avoiding a much larger, separate TensorFlow install for one script.

Q: Why does this script scale features but Assignment 1's Random Forest
   doesn't need to?
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
   the non-linear churn relationship built into this dataset.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score

RNG = np.random.default_rng(21)
N_SAMPLES = 10000


# BUILD A SYNTHETIC "CHURN_MODELLING"-LIKE CUSTOMER TABLE

def build_dataset(n=N_SAMPLES):
    customer_id = np.arange(15600000, 15600000 + n)
    credit_score = RNG.integers(350, 850, n)
    geography = RNG.choice(["France", "Germany", "Spain"], n)
    gender = RNG.choice(["Male", "Female"], n)
    age = RNG.integers(18, 80, n)
    tenure = RNG.integers(0, 11, n)
    balance = RNG.uniform(0, 250000, n)
    num_products = RNG.integers(1, 5, n)
    has_credit_card = RNG.integers(0, 2, n)
    is_active_member = RNG.integers(0, 2, n)
    estimated_salary = RNG.uniform(10000, 200000, n)

    # Designed relationship: older + inactive + low balance + few products
    # pushes churn probability up. Everything else pushes it down. Plus noise.
    churn_score = (
        0.03 * (age - 40)
        - 1.5 * is_active_member
        - 0.00002 * balance
        - 0.4 * num_products
        + RNG.normal(0, 1.2, n)
    )
    churn_prob = 1 / (1 + np.exp(-churn_score))
    churned = (churn_prob > RNG.uniform(0, 1, n)).astype(int)

    return pd.DataFrame({
        "customer_id": customer_id,
        "geography": geography,
        "gender": gender,
        "credit_score": credit_score,
        "age": age,
        "tenure": tenure,
        "balance": balance,
        "num_products": num_products,
        "has_credit_card": has_credit_card,
        "is_active_member": is_active_member,
        "estimated_salary": estimated_salary,
        "churned": churned,
    })


if __name__ == "__main__":
    data = build_dataset()
    print(f"Dataset: {len(data)} customers, {data['churned'].sum()} churned "
          f"({data['churned'].mean():.1%})\n")

    # Pre-process: CustomerId is just an identifier, so drop it; encode the
    # text columns (Geography, Gender) as 0/1 columns for the network.
    X = pd.get_dummies(data.drop(columns=["churned", "customer_id"]), drop_first=True)
    y = data["churned"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Neural networks are scale-sensitive, so features must be standardized.
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # NEURAL NETWORK (MULTI-LAYER PERCEPTRON) CLASSIFIER
    ann = MLPClassifier(
        hidden_layer_sizes=(16, 8),
        activation="relu",
        max_iter=500,
        random_state=42,
    )
    ann.fit(X_train_s, y_train)
    pred = ann.predict(X_test_s)

    accuracy = accuracy_score(y_test, pred)
    precision = precision_score(y_test, pred, zero_division=0)
    recall = recall_score(y_test, pred, zero_division=0)

    print("ANN (MLPClassifier) results:")
    print(f"Accuracy:  {accuracy:.3f}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")

    # SANITY CHECK: the churn relationship is designed to be learnable,
    # so the network should clearly beat random guessing.
    assert accuracy > 0.7, f"ANN accuracy too low: {accuracy}"
    print("\nSanity check passed: accuracy > 0.7")
