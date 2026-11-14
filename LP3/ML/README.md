# ML: Machine Learning

LP3 Group B. The code files contain only code. The problem statement,
approach, dataset notes and viva prep for each assignment are in its `.md`
file. Each notebook is the same code as its script, split into cells.

| # | Assignment | Write-up | Code | Dataset |
| --- | --- | --- | --- | --- |
| 1 | Uber ride price prediction: Linear Regression vs Random Forest | `1_UberRidePricePrediction.md` | `1_UberRidePricePrediction.py` / `.ipynb` | `data/uber.csv` |
| 2 | Email spam classification: KNN vs SVM | `2_EmailSpamClassification.md` | `2_EmailSpamClassification.py` / `.ipynb` | `data/emails.csv`, else `data/spambase.data` |
| 3 | Bank customer churn: neural network classifier | `3_BankCustomerChurnANN.md` | `3_BankCustomerChurnANN.py` / `.ipynb` | `data/Churn_Modelling.csv` |
| 4 | Gradient Descent to find the local minima of a function | `4_GradientDescent.md` | `4_GradientDescent.py` / `.ipynb` | none |
| 5 | K-Means clustering with the elbow method | `5_KMeansClustering.md` | `5_KMeansClustering.py` / `.ipynb` | `data/sales_data_sample.csv` |

## How to run

```bash
pip install -r requirements.txt
python 1_UberRidePricePrediction.py
```

The same pattern works for every script. A data file is read from `data/`, or
from next to the script if the `data/` copy is missing.
