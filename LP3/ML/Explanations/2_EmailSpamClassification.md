# Assignment 2: Email Spam Classification

## Problem statement
Classify emails as spam or not spam (binary classification) using
K-Nearest Neighbors (KNN) and Support Vector Machine (SVM), and compare the
two classifiers.

## Approach
- Both KNN and SVM are distance-based, so features are standardized first
  (`StandardScaler`) -- otherwise a large-magnitude feature would dominate
  the distance calculation over more informative small-magnitude features.
- **KNN**: a lazy, instance-based classifier -- classifies a new email by
  majority vote of its `k` nearest neighbors in the training set.
- **SVM (RBF kernel)**: finds the maximum-margin boundary between the
  classes, using the kernel trick to separate classes that aren't linearly
  separable in the raw feature space.
- **Evaluation**: accuracy, precision, recall, F1 and a confusion matrix
  for each model, since for a spam filter false positives (real mail
  marked spam) and false negatives (spam that slips through) matter
  differently. ROC and Precision-Recall curves (with AUC / average
  precision) are also plotted for both models together, since those are
  threshold-independent -- the metrics above all assume the default 0.5
  cutoff.

## Dataset
Prefers the Kaggle "Email Spam Classification Dataset" (`emails.csv`) if
it's present -- 5172 emails x 3000 raw word-count columns plus a
`Prediction` label -- since that's the file actually handed out for this
assignment in some cohorts. Falls back to the real UCI Spambase dataset
(archive.ics.uci.edu/dataset/94), 4601 emails with 57 pre-computed
frequency features, saved locally at `data/spambase.data`, if `emails.csv`
isn't found.

## Implementation notes
- In both datasets the last column is the label and every other column is a
  feature, so the code selects them by position. `emails.csv` also has an
  `Email No.` row-label column, which is dropped first. Spambase has no
  header row, hence `header=None`.
- `KNeighborsClassifier()` defaults to `k = 5` and `SVC()` defaults to the RBF
  kernel.
- `classification_report` prints accuracy, precision, recall and F1 together.
- `SVC` has no probability output by default; the ROC and Precision-Recall
  curves use its `decision_function` scores instead.
- The curves are saved as `roc_curve.png` and `precision_recall_curve.png`.

## Viva prep

**Q: Why scale features for KNN/SVM but not for a tree-based model?**
A: KNN/SVM distance calculations treat raw numeric scale as meaningful, so
an unscaled large feature would dominate. Tree-based splits are invariant
to the scale of any single feature.

**Q: Precision vs recall -- which matters more for a spam filter?**
A: Usually precision: a false positive (real mail marked spam) is normally
more costly to a user than an occasional spam email getting through.

**Q: What does `stratify=y` do in `train_test_split`, and why use it?**
A: It keeps the spam/ham ratio the same in both the train and test splits,
so an unlucky random split doesn't skew one set toward one class.

**Q: What is the "kernel trick" in SVM?**
A: It lets the SVM compute similarity as if points had been mapped into a
higher-dimensional space, without explicitly computing that mapping --
making non-linear separation computationally feasible.

**Q: Why plot ROC and Precision-Recall curves instead of just reporting
one accuracy/precision/recall number?**
A: Accuracy/precision/recall/F1 are all computed at one fixed decision
threshold (0.5). ROC (AUC) and Precision-Recall (average precision) sweep
every possible threshold, so they summarize how good the model's ranking
is overall -- useful if the spam cutoff might later be tuned.

**Q: Why is Precision-Recall often preferred over ROC for an imbalanced
dataset like spam detection?**
A: ROC's false-positive rate is diluted by the large number of true
negatives (ham), so it can look good even when precision on the minority
(spam) class is mediocre. Precision-Recall focuses entirely on the
positive class, making it more sensitive to that imbalance.
