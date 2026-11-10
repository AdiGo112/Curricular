"""
Assignment 2: Email Spam Classification
========================================

Problem statement
------------------
Classify emails as spam or not spam (binary classification) using
K-Nearest Neighbors (KNN) and Support Vector Machine (SVM), and compare the
two classifiers.

Approach
--------
- Both KNN and SVM are distance-based, so features are standardized first
  (`StandardScaler`) -- otherwise a large-magnitude feature like
  `email_length` would dominate the distance calculation over more
  informative small-magnitude features.
- KNN: a lazy, instance-based classifier -- classifies a new email by
  majority vote of its `k` nearest neighbors in the training set.
- SVM (RBF kernel): finds the maximum-margin boundary between the classes,
  using the kernel trick to separate classes that aren't linearly
  separable in the raw feature space.
- Evaluation: accuracy, precision, recall, F1 and a confusion matrix for
  each model, since for a spam filter false positives (real mail marked
  spam) and false negatives (spam that slips through) matter differently.

Synthetic dataset
------------------
Kaggle's real spam-email feature dataset is not reachable from this
environment (no internet access), so `build_dataset()` draws spam and ham
rows from different distributions (spam skewed toward high word_freq_free/
word_freq_win, many links, many capitalized words). Numbers below are
illustrative of the technique, not results on the real Kaggle data.

Likely viva questions
----------------------
Q: Why scale features for KNN/SVM but not for Random Forest (Assignment 1)?
A: KNN/SVM distance calculations treat raw numeric scale as meaningful, so
   an unscaled large feature would dominate. Tree-based splits are
   invariant to the scale of any single feature.

Q: Precision vs recall -- which matters more for a spam filter?
A: Usually precision: a false positive (real mail marked spam) is normally
   more costly to a user than an occasional spam email getting through.

Q: What does `stratify=y` do in `train_test_split`, and why use it?
A: It keeps the spam/ham ratio the same in both the train and test splits,
   so an unlucky random split doesn't skew one set toward one class.

Q: What is the "kernel trick" in SVM?
A: It lets the SVM compute similarity as if points had been mapped into a
   higher-dimensional space, without explicitly computing that mapping --
   making non-linear separation computationally feasible.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

RNG = np.random.default_rng(7)
N_SAMPLES = 800


# BUILD A SYNTHETIC SPAM/NOT-SPAM FEATURE TABLE

def build_dataset(n=N_SAMPLES):
    n_spam = n // 2
    n_ham = n - n_spam

    # Spam mail: lots of "free"/"win" words, many links, shouty capitals.
    spam = pd.DataFrame({
        "word_freq_free": RNG.gamma(3, 1.0, n_spam),
        "word_freq_win": RNG.gamma(2.5, 1.0, n_spam),
        "num_links": RNG.poisson(6, n_spam),
        "num_capital_words": RNG.poisson(8, n_spam),
        "email_length": RNG.normal(400, 100, n_spam),
    })
    spam["is_spam"] = 1

    # Ham mail: those words rare, few links, few capitals.
    ham = pd.DataFrame({
        "word_freq_free": RNG.gamma(0.5, 0.3, n_ham),
        "word_freq_win": RNG.gamma(0.4, 0.3, n_ham),
        "num_links": RNG.poisson(1, n_ham),
        "num_capital_words": RNG.poisson(1, n_ham),
        "email_length": RNG.normal(600, 150, n_ham),
    })
    ham["is_spam"] = 0

    df = pd.concat([spam, ham], ignore_index=True)
    df["email_length"] = df["email_length"].clip(lower=20)  # no negative lengths
    return df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle


def print_confusion_matrix(name, y_test, y_pred):
    cm = confusion_matrix(y_test, y_pred)
    print(f"{name} confusion matrix (rows=actual, cols=predicted [ham, spam]):")
    print(cm)


if __name__ == "__main__":
    data = build_dataset()
    print(f"Dataset: {len(data)} emails, {data['is_spam'].sum()} spam / {(data['is_spam'] == 0).sum()} ham\n")

    X = data.drop(columns=["is_spam"])
    y = data["is_spam"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    # KNN and SVM are distance-based, so features need scaling.
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # K-NEAREST NEIGHBORS
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(X_train_s, y_train)
    knn_pred = knn.predict(X_test_s)

    # SUPPORT VECTOR MACHINE
    svm = SVC(kernel="rbf", random_state=42)
    svm.fit(X_train_s, y_train)
    svm_pred = svm.predict(X_test_s)

    # EVALUATION
    results = {}
    for name, pred in [("KNN", knn_pred), ("SVM", svm_pred)]:
        results[name] = {
            "accuracy": accuracy_score(y_test, pred),
            "precision": precision_score(y_test, pred),
            "recall": recall_score(y_test, pred),
            "f1": f1_score(y_test, pred),
        }
        print_confusion_matrix(name, y_test, pred)
        print()

    print("Model comparison:")
    print(f"{'Model':<10}{'Accuracy':>10}{'Precision':>12}{'Recall':>10}{'F1':>10}")
    for name, m in results.items():
        print(f"{name:<10}{m['accuracy']:>10.3f}{m['precision']:>12.3f}{m['recall']:>10.3f}{m['f1']:>10.3f}")

    # SANITY CHECK: the two classes are deliberately well separated,
    # so both classifiers should comfortably beat a coin flip.
    for name, m in results.items():
        assert m["accuracy"] > 0.8, f"{name} accuracy too low: {m['accuracy']}"
    print("\nSanity check passed: both models reach accuracy > 0.8")
