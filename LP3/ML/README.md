# ML: Machine Learning

LP3 Group B. The mini project (item 6) is out of scope here; it's handled separately.

Assignments 1, 2, 3 and 5 run on the real public datasets under `data/` (downloaded
once, committed here so the scripts run offline afterwards); Assignment 4 needs no
dataset. Each script's docstring names its dataset and source.

Each script has a header comment block with the problem statement, approach,
dataset notes and a few likely viva questions, plus inline comments through
the code -- no separate notes folder.

| # | Assignment | File | Dataset |
| --- | --- | --- | --- |
| 1 | Uber ride price prediction: preprocessing, outliers, correlation, Linear Regression vs Random Forest | `1_UberRidePricePrediction.py` | `data/uber.csv` (Kaggle: yasserh/uber-fares-dataset) |
| 2 | Email spam classification: K-Nearest Neighbors vs Support Vector Machine | `2_EmailSpamClassification.py` | `data/spambase.data` (UCI Spambase) |
| 3 | Bank customer churn: neural-network classifier (`MLPClassifier`) | `3_BankCustomerChurnANN.py` | `data/Churn_Modelling.csv` (Kaggle) |
| 4 | Gradient Descent to find the local minima of a function | `4_GradientDescent.py` | none |
| 5 | K-Means clustering with the elbow method | `5_KMeansClustering.py` → `elbow_curve.png` | `data/sales_data_sample.csv` (Kaggle: Sample Sales Data) |

## How to run

```bash
pip install -r LP3/ML/requirements.txt
python LP3/ML/1_UberRidePricePrediction.py
python LP3/ML/2_EmailSpamClassification.py
python LP3/ML/3_BankCustomerChurnANN.py
python LP3/ML/4_GradientDescent.py
python LP3/ML/5_KMeansClustering.py
```

Each script prints its results to the console (and, for Assignment 5, also saves a plot).
