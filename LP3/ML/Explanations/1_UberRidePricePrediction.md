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
  distance column), and `hour_of_day` and `year` from `pickup_datetime`.
  Rides with zero distance (pickup and dropoff at the same point) are
  dropped, since a fare with no trip is noise.
- **Outliers**: a boxplot of `fare_amount` and `distance_km` shows them
  visually. They are then detected and dropped from both columns using the
  IQR rule (robust, doesn't assume a normal distribution).
- **Correlation**: pandas `.corr()` on the cleaned data, shown as a table
  and a heatmap, as a sanity check that distance is actually driving fare
  before modelling.
- **Two regressors are compared**: Linear Regression (fast, interpretable,
  but only fits a straight-line effect per feature) and Random Forest
  Regression (an ensemble of decision trees, able to capture non-linear
  effects such as rush-hour/night pricing patterns). The trees are limited
  to `max_depth=10` so they don't memorise the training data.
- **Evaluation**: R2 (fraction of variance explained) and RMSE (average
  error in the same units as the fare) on a held-out test split.

## Implementation notes
- Longitude -75 to -72 and latitude 40 to 42 is a rough bounding box around
  New York City. The raw data has GPS errors such as longitude -1340, and
  this filter drops them.
- `6371` in the haversine formula is the Earth's radius in km.
- IQR rule: a value is an outlier if it is below `Q1 - 1.5 * IQR` or above
  `Q3 + 1.5 * IQR`, where `IQR = Q3 - Q1`.
- Distance outliers matter as much as fare outliers: the raw data has rides
  of 60 to 100 km with fares of a few dollars, and they pulled Linear
  Regression into predicting fares of 140.
- Without a depth limit the forest scored R2 0.95 on the training data but
  0.64 on the test data, which is overfitting. With `max_depth=10` the two
  are 0.72 and 0.69.
- The data file is read from `data/uber.csv`, or from `uber.csv` next to the
  script if the `data/` copy is missing.

## Graphs

| File | What it shows |
| --- | --- |
| `outlier_boxplot.png` | Boxplots of fare and distance. Points beyond the whiskers are the outliers, and the whiskers sit at the same `1.5 * IQR` limits the code uses. |
| `correlation_heatmap.png` | The correlation matrix as colours, with each value written in its cell. Red is positive, blue is negative. |
| `distance_vs_fare.png` | Fare against distance after cleaning, for a random sample of 2,000 rides. Fare rises with distance. |
| `predicted_vs_actual.png` | Predicted against actual fare for both models, for the first 2,000 test rides. Points on the red diagonal are perfect predictions. |

Reading the scatter plots: only 2,000 rides are drawn so the dots stay
separate; the models still train and score on all rides. Fares only come
in fixed steps, so dots line up in rows.
The sharp edges at fare 22 and distance 6.5 km are where the outlier rule
cut the data.

## Results
24,262 rows are removed as fare or distance outliers. Correlation with fare:
distance 0.80, year 0.17, passenger count 0.02, hour 0.01.

| Model | R2 | RMSE |
| --- | --- | --- |
| Linear Regression | 0.663 | 2.150 |
| Random Forest | 0.694 | 2.049 |

Random Forest explains slightly more of the variance and is off by about
2.05 dollars on average, against 2.15 for Linear Regression. The gap is small
because, once outliers are gone, fare depends on distance almost linearly.

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

**Q: Why is the gap between the two models so small?**
A: After cleaning, distance explains most of the fare and the relationship
is close to a straight line, which Linear Regression fits well. Random
Forest only adds the smaller non-linear effects.

**Q: Why limit the depth of the trees?**
A: Fully grown trees fit the noise in the training data: R2 was 0.95 on
training data but 0.64 on test data. A depth limit forces each tree to
learn only the broad pattern, which generalises better.

**Q: Why is `year` a useful feature?**
A: Fares rose over the years the data covers (2009 to 2015), so the same
trip costs more in a later year. Its correlation with fare is 0.17, the
second highest after distance.

**Q: How do you read outliers from a boxplot?**
A: The box spans Q1 to Q3, the whiskers extend to `1.5 * IQR` beyond the
box, and every point drawn outside the whiskers is an outlier.

**Q: Why drop rows with missing/invalid coordinates instead of imputing
them?**
A: A GPS coordinate can't be meaningfully imputed the way a plain numeric
feature can (there's no "typical" location); only a handful of rows are
affected, so dropping them loses negligible data while avoiding fabricated
pickup/dropoff points.
