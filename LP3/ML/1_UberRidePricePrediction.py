"""
Assignment 1: Uber Ride Price Prediction
=========================================

Problem statement
------------------
Predict the fare of an Uber ride. Preprocess the dataset, identify outliers,
check correlation between features, implement Linear Regression and Random
Forest Regression, then evaluate and compare them with R2 and RMSE.

Approach
--------
- Preprocessing: fill missing values (median imputation), then detect and
  drop outliers in `fare_amount` using the IQR rule (robust, doesn't assume
  a normal distribution).
- Correlation: pandas `.corr()` on the cleaned data, as a sanity check that
  distance is actually driving fare before modelling.
- Two regressors are compared: Linear Regression (fast, interpretable, but
  only fits a straight-line effect per feature) and Random Forest Regression
  (an ensemble of decision trees, able to capture non-linear effects such as
  the night-time surge multiplier built into this dataset).
- Evaluation: R2 (fraction of variance explained) and RMSE (average error in
  the same units as the fare) on a held-out test split.

Synthetic dataset
------------------
Kaggle's real "uber.csv" fare dataset is not reachable from this environment
(no internet access), so `build_dataset()` generates distance/passengers/hour
columns and a `fare_amount` from a realistic formula (base fare + per-km rate
with a 1.3x night surge + per-passenger charge + Gaussian noise), with a few
missing values and a few extreme-outlier fares injected on purpose. Numbers
below are illustrative of the technique, not results on the real Kaggle data.

Likely viva questions
----------------------
Q: Why use R2 and RMSE together instead of just one?
A: R2 is relative (how much variance is explained); RMSE is absolute, in real
   units. Together they avoid being misled by either framing alone.

Q: Why detect outliers with the IQR rule instead of a fixed cutoff?
A: IQR adapts to the actual spread of the data and doesn't assume a normal
   distribution, unlike a fixed percentile or z-score cutoff.

Q: Why might Random Forest outperform Linear Regression here?
A: The fare formula has a non-linear piece (the night surge). Linear
   Regression can only fit a straight-line effect per feature; Random Forest
   can split on `hour_of_day` and model the surge directly.

Q: Why fill missing distance with the median rather than the mean?
A: The median isn't pulled around by extreme values, so it's a more
   representative "typical" value when the data isn't symmetric.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, root_mean_squared_error

RNG = np.random.default_rng(42)
N_SAMPLES = 1000


# BUILD A SYNTHETIC "UBER FARES" DATASET

def build_dataset(n=N_SAMPLES):
    distance_km = RNG.uniform(0.5, 30, n)
    passenger_count = RNG.integers(1, 5, n)
    hour_of_day = RNG.integers(0, 24, n)

    # Real-world-ish fare formula: base fare + per-km rate + small surge at
    # night/rush hour + per-passenger charge + noise.
    night_surge = np.where((hour_of_day >= 22) | (hour_of_day <= 5), 1.3, 1.0)
    fare_amount = (
        2.5
        + 1.8 * distance_km * night_surge
        + 0.5 * passenger_count
        + RNG.normal(0, 2.0, n)
    )

    df = pd.DataFrame({
        "distance_km": distance_km,
        "passenger_count": passenger_count,
        "hour_of_day": hour_of_day,
        "fare_amount": fare_amount,
    })

    # Inject a few missing values, like a real scraped dataset would have.
    null_idx = RNG.choice(n, size=max(1, n // 100), replace=False)
    df.loc[null_idx, "distance_km"] = np.nan

    # Inject a handful of extreme outlier fares (e.g. bad GPS / fraud rides).
    outlier_idx = RNG.choice(n, size=max(1, n // 100), replace=False)
    df.loc[outlier_idx, "fare_amount"] *= 8

    return df


# PREPROCESSING: fill missing values

def preprocess(df):
    df = df.copy()
    df["distance_km"] = df["distance_km"].fillna(df["distance_km"].median())
    return df


# OUTLIER DETECTION ON fare_amount USING THE IQR RULE

def remove_outliers_iqr(df, column="fare_amount"):
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    is_outlier = (df[column] < lower) | (df[column] > upper)
    flagged = int(is_outlier.sum())

    cleaned = df.loc[~is_outlier].reset_index(drop=True)
    return cleaned, flagged


if __name__ == "__main__":
    data = build_dataset()
    print(f"Raw dataset: {len(data)} rows, {data.isna().sum().sum()} missing values")

    data = preprocess(data)
    data, n_flagged = remove_outliers_iqr(data)
    print(f"Outliers flagged and removed (IQR rule on fare_amount): {n_flagged}")
    print(f"Dataset after cleaning: {len(data)} rows\n")

    # CORRELATION MATRIX
    print("Correlation matrix:")
    print(data.corr().round(2))
    print()

    # TRAIN/TEST SPLIT
    X = data[["distance_km", "passenger_count", "hour_of_day"]]
    y = data["fare_amount"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # LINEAR REGRESSION
    lin_model = LinearRegression()
    lin_model.fit(X_train, y_train)
    lin_pred = lin_model.predict(X_test)

    # RANDOM FOREST REGRESSION
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)

    # EVALUATION: R2 and RMSE for both models
    results = {
        "Linear Regression": (r2_score(y_test, lin_pred), root_mean_squared_error(y_test, lin_pred)),
        "Random Forest": (r2_score(y_test, rf_pred), root_mean_squared_error(y_test, rf_pred)),
    }

    print("Model comparison:")
    print(f"{'Model':<20}{'R2':>10}{'RMSE':>10}")
    for name, (r2, rmse) in results.items():
        print(f"{name:<20}{r2:>10.3f}{rmse:>10.3f}")

    # SANITY CHECK: the synthetic relationship is strong by construction,
    # so a reasonable model should explain most of the variance.
    for name, (r2, _) in results.items():
        assert r2 > 0.5, f"{name} R2 too low: {r2}"
    print("\nSanity check passed: both models reach R2 > 0.5")
