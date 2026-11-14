# Assignment 1: Uber Ride Price Prediction

## Problem statement
Predict the fare of an Uber ride. Preprocess the dataset, identify outliers,
check correlation between features, implement Linear Regression and Random
Forest Regression, then evaluate and compare them with R2 and RMSE.

## Approach
- **Preprocessing**: drop rows with missing coordinates, drop physically
  impossible rows (non-positive fares, GPS coordinates far outside the NYC
  area, unrealistic passenger counts), then derive `distance_km` with the
  haversine formula (the raw data only has pickup/dropoff lat/long, no
  distance column) and `hour_of_day` from `pickup_datetime`. Outliers are
  then detected and dropped on `fare_amount` using the IQR rule (robust,
  doesn't assume a normal distribution).
- **Correlation**: pandas `.corr()` on the cleaned data, as a sanity check
  that distance is actually driving fare before modelling.
- **Two regressors are compared**: Linear Regression (fast, interpretable,
  but only fits a straight-line effect per feature) and Random Forest
  Regression (an ensemble of decision trees, able to capture non-linear
  effects such as rush-hour/night pricing patterns).
- **Evaluation**: R2 (fraction of variance explained) and RMSE (average
  error in the same units as the fare) on a held-out test split.

## Implementation notes
- Longitude -75 to -72 and latitude 40 to 42 is a rough bounding box around
  New York City. The raw data has GPS errors such as longitude -1340, and
  this filter drops them.
- `6371` in the haversine formula is the Earth's radius in km.
- IQR rule: a fare is an outlier if it is below `Q1 - 1.5 * IQR` or above
  `Q3 + 1.5 * IQR`, where `IQR = Q3 - Q1`.
- The data file is read from `data/uber.csv`, or from `uber.csv` next to the
  script if the `data/` copy is missing.

## Dataset
The real Kaggle "Uber Fares Dataset" (yasserh/uber-fares-dataset), 200,000
rides with fare, pickup/dropoff coordinates, pickup time and passenger
count, saved locally at `data/uber.csv`.

## Viva prep

**Q: Why use R2 and RMSE together instead of just one?**
A: R2 is relative (how much variance is explained); RMSE is absolute, in
real units. Together they avoid being misled by either framing alone.

**Q: Why detect outliers with the IQR rule instead of a fixed cutoff?**
A: IQR adapts to the actual spread of the data and doesn't assume a normal
distribution, unlike a fixed percentile or z-score cutoff.

**Q: Why might Random Forest outperform Linear Regression here?**
A: Real fares have non-linear effects (e.g. time-of-day pricing patterns).
Linear Regression can only fit a straight-line effect per feature; Random
Forest can split on `hour_of_day` and `distance_km` to model those patterns
directly.

**Q: Why drop rows with missing/invalid coordinates instead of imputing
them?**
A: A GPS coordinate can't be meaningfully imputed the way a plain numeric
feature can (there's no "typical" location); only a handful of rows are
affected, so dropping them loses negligible data while avoiding fabricated
pickup/dropoff points.
