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
  (`StandardScaler`) -- otherwise a large-magnitude feature would dominate
  the distance calculation over more informative small-magnitude features.
- KNN: a lazy, instance-based classifier -- classifies a new email by
  majority vote of its `k` nearest neighbors in the training set.
- SVM (RBF kernel): finds the maximum-margin boundary between the classes,
  using the kernel trick to separate classes that aren't linearly
  separable in the raw feature space.
- Evaluation: accuracy, precision, recall, F1 and a confusion matrix for
  each model, since for a spam filter false positives (real mail marked
  spam) and false negatives (spam that slips through) matter differently.

Dataset
-------
The real UCI Spambase dataset (archive.ics.uci.edu/dataset/94), 4601 emails
with 57 features (48 word frequencies, 6 character frequencies, 3 capital-
run-length stats) and a spam/not-spam label, saved locally at
data/spambase.data (no header row -- column names are assigned in code).

Likely viva questions
----------------------
Q: Why scale features for KNN/SVM but not for a tree-based model?
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

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Falls back to a file dropped next to the script (e.g. exam machine) if the
# dev-layout data/ copy isn't there.
DATA_PATH = next(
    (p for p in (Path(__file__).parent / "data" / "spambase.data", Path(__file__).parent / "spambase.data") if p.exists()),
    Path(__file__).parent / "data" / "spambase.data",
)

# Spambase has no header row; these are the 57 feature names (in the exact
# order given in spambase.names) plus the spam/not-spam label.
WORD_FREQ_COLS = [
    "make", "address", "all", "3d", "our", "over", "remove", "internet", "order", "mail",
    "receive", "will", "people", "report", "addresses", "free", "business", "email", "you",
    "credit", "your", "font", "000", "money", "hp", "hpl", "george", "650", "lab", "labs",
    "telnet", "857", "data", "415", "85", "technology", "1999", "parts", "pm", "direct", "cs",
    "meeting", "original", "project", "re", "edu", "table", "conference",
]
COLUMNS = (
    [f"word_freq_{w}" for w in WORD_FREQ_COLS]
    + ["char_freq_semicolon", "char_freq_paren", "char_freq_bracket", "char_freq_bang", "char_freq_dollar", "char_freq_hash"]
    + ["capital_run_length_average", "capital_run_length_longest", "capital_run_length_total"]
    + ["is_spam"]
)


def print_confusion_matrix(name, y_test, y_pred):
    cm = confusion_matrix(y_test, y_pred)
    print(f"{name} confusion matrix (rows=actual, cols=predicted [ham, spam]):")
    print(cm)


if __name__ == "__main__":
    data = pd.read_csv(DATA_PATH, header=None, names=COLUMNS)
    print(f"Dataset: {len(data)} emails, {data['is_spam'].sum()} spam / {(data['is_spam'] == 0).sum()} ham\n")

    X = data.drop(columns=["is_spam"])
    y = data["is_spam"]
    # stratify=y keeps the spam/ham ratio the same in both splits
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    # KNN and SVM both classify by distance between points, so an unscaled
    # large-magnitude feature would dominate that distance.
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # K-NEAREST NEIGHBORS: classifies a new email by majority vote of its
    # 5 nearest neighbors in the training set (lazy, no real "training").
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(X_train_s, y_train)
    knn_pred = knn.predict(X_test_s)

    # SUPPORT VECTOR MACHINE: finds the max-margin boundary between classes;
    # the RBF kernel lets it separate classes that aren't linearly separable.
    svm = SVC(kernel="rbf", random_state=42)
    svm.fit(X_train_s, y_train)
    svm_pred = svm.predict(X_test_s)

    # EVALUATION: accuracy/precision/recall/F1 + confusion matrix for each --
    # for a spam filter, false positives (real mail marked spam) and false
    # negatives (spam that slips through) matter differently, so one number
    # isn't enough.
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
