# ML: Machine Learning

LP3 Group B. The mini project (item 6) is out of scope here; it's handled separately.

**No internet / Kaggle access was available**, so every script generates its own small
synthetic dataset in-code (fixed random seed, shaped like the real Kaggle dataset's
columns) instead of downloading one. Results are illustrative of the technique, not
numbers from the real Kaggle data.

Each script has a header comment block with the problem statement, approach,
synthetic-dataset notes and a few likely viva questions, plus inline comments
through the code -- no separate notes folder.

| # | Assignment | File |
| --- | --- | --- |
| 1 | Uber ride price prediction: preprocessing, outliers, correlation, Linear Regression vs Random Forest | `1_UberRidePricePrediction.py` |
| 2 | Email spam classification: K-Nearest Neighbors vs Support Vector Machine | `2_EmailSpamClassification.py` |
| 3 | Bank customer churn: neural-network classifier (`MLPClassifier`) | `3_BankCustomerChurnANN.py` |
| 4 | Gradient Descent to find the local minima of a function | `4_GradientDescent.py` |
| 5 | K-Means clustering with the elbow method | `5_KMeansClustering.py` → `elbow_curve.png` |

## How to run

```bash
pip install -r LP3/ML/requirements.txt
python LP3/ML/1_UberRidePricePrediction.py
python LP3/ML/2_EmailSpamClassification.py
python LP3/ML/3_BankCustomerChurnANN.py
python LP3/ML/4_GradientDescent.py
python LP3/ML/5_KMeansClustering.py
```

Each script prints its results and ends with an assert-based sanity check, so a clean
run with no traceback means the pipeline worked.
