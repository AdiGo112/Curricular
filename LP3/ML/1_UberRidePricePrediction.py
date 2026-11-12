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
- Preprocessing: drop rows with missing coordinates, drop physically
  impossible rows (non-positive fares, GPS coordinates far outside the NYC
  area, unrealistic passenger counts), then derive `distance_km` with the
  haversine formula (the raw data only has pickup/dropoff lat/long, no
  distance column) and `hour_of_day` from `pickup_datetime`. Outliers are
  then detected and dropped on `fare_amount` using the IQR rule (robust,
  doesn't assume a normal distribution).
- Correlation: pandas `.corr()` on the cleaned data, as a sanity check that
  distance is actually driving fare before modelling.
- Two regressors are compared: Linear Regression (fast, interpretable, but
  only fits a straight-line effect per feature) and Random Forest Regression
  (an ensemble of decision trees, able to capture non-linear effects such as
  rush-hour/night pricing patterns).
- Evaluation: R2 (fraction of variance explained) and RMSE (average error in
  the same units as the fare) on a held-out test split.

Dataset
-------
The real Kaggle "Uber Fares Dataset" (yasserh/uber-fares-dataset), 200,000
rides with fare, pickup/dropoff coordinates, pickup time and passenger
count, saved locally at data/uber.csv.

Likely viva questions
----------------------
Q: Why use R2 and RMSE together instead of just one?
A: R2 is relative (how much variance is explained); RMSE is absolute, in real
   units. Together they avoid being misled by either framing alone.

Q: Why detect outliers with the IQR rule instead of a fixed cutoff?
A: IQR adapts to the actual spread of the data and doesn't assume a normal
   distribution, unlike a fixed percentile or z-score cutoff.

Q: Why might Random Forest outperform Linear Regression here?
A: Real fares have non-linear effects (e.g. time-of-day pricing patterns).
   Linear Regression can only fit a straight-line effect per feature;
   Random Forest can split on `hour_of_day` and `distance_km` to model
   those patterns directly.

Q: Why drop rows with missing/invalid coordinates instead of imputing them?
A: A GPS coordinate can't be meaningfully imputed the way a plain numeric
   feature can (there's no "typical" location); only a handful of rows are
   affected, so dropping them loses negligible data while avoiding
   fabricated pickup/dropoff points.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, root_mean_squared_error

DATA_PATH = Path(__file__).parent / "data" / "uber.csv"

# Rough bounding box around NYC, used to drop GPS-error rows (the raw data
# has coordinates like longitude=-1340 or latitude=872, which are nonsense).
LON_RANGE = (-75.0, -72.0)
LAT_RANGE = (40.0, 42.0)


# HAVERSINE DISTANCE (km) BETWEEN TWO LAT/LONG POINTS ON EARTH'S SURFACE
def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return r * 2 * np.arcsin(np.sqrt(a))


# PREPROCESSING: drop unusable rows, then derive distance_km and hour_of_day
def preprocess(df):
    df = df.copy()

    # Drop rows with missing coordinates (a handful in this dataset).
    coord_cols = ["pickup_longitude", "pickup_latitude", "dropoff_longitude", "dropoff_latitude"]
    df = df.dropna(subset=coord_cols)

    # Drop physically impossible rows: non-positive fares, bad GPS fixes
    # outside the NYC area, and unrealistic passenger counts.
    df = df[df["fare_amount"] > 0]
    df = df[df["pickup_longitude"].between(*LON_RANGE) & df["dropoff_longitude"].between(*LON_RANGE)]
    df = df[df["pickup_latitude"].between(*LAT_RANGE) & df["dropoff_latitude"].between(*LAT_RANGE)]
    df = df[df["passenger_count"].between(1, 6)]

    df["distance_km"] = haversine_km(
        df["pickup_latitude"], df["pickup_longitude"], df["dropoff_latitude"], df["dropoff_longitude"]
    )
    df["hour_of_day"] = pd.to_datetime(df["pickup_datetime"]).dt.hour

    return df[["distance_km", "passenger_count", "hour_of_day", "fare_amount"]].reset_index(drop=True)


# OUTLIER DETECTION ON fare_amount USING THE IQR RULE: anything more than
# 1.5x the interquartile range outside the middle 50% of fares is dropped.
# IQR adapts to the data's actual spread, unlike a fixed cutoff.
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
    data = pd.read_csv(DATA_PATH)
    print(f"Raw dataset: {len(data)} rows")

    data = preprocess(data)
    print(f"After dropping missing/invalid rows: {len(data)} rows")

    data, n_flagged = remove_outliers_iqr(data)
    print(f"Outliers flagged and removed (IQR rule on fare_amount): {n_flagged}")
    print(f"Dataset after cleaning: {len(data)} rows\n")

    # CORRELATION MATRIX
    print("Correlation matrix:")
    print(data.corr().round(2))
    print()

    # TRAIN/TEST SPLIT: hold out 20% of rows, unseen by training, to evaluate on
    X = data[["distance_km", "passenger_count", "hour_of_day"]]
    y = data["fare_amount"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # LINEAR REGRESSION: fast, interpretable, but only fits a straight-line
    # effect per feature.
    lin_model = LinearRegression()
    lin_model.fit(X_train, y_train)
    lin_pred = lin_model.predict(X_test)

    # RANDOM FOREST REGRESSION: an ensemble of 100 decision trees (each on a
    # bootstrap sample, predictions averaged), able to capture non-linear
    # effects such as rush-hour/night pricing patterns.
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)

    # EVALUATION: R2 (fraction of variance explained, relative) and RMSE
    # (average error in the same units as the fare, absolute) for both models
    results = {
        "Linear Regression": (r2_score(y_test, lin_pred), root_mean_squared_error(y_test, lin_pred)),
        "Random Forest": (r2_score(y_test, rf_pred), root_mean_squared_error(y_test, rf_pred)),
    }

    print("Model comparison:")
    print(f"{'Model':<20}{'R2':>10}{'RMSE':>10}")
    for name, (r2, rmse) in results.items():
        print(f"{name:<20}{r2:>10.3f}{rmse:>10.3f}")
