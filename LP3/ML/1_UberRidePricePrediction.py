from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split

HERE = Path(__file__).parent
DATA = HERE / "data" / "uber.csv"
if not DATA.exists():
    DATA = HERE / "uber.csv"

df = pd.read_csv(DATA).dropna()
df = df[(df.fare_amount > 0) & df.passenger_count.between(1, 6)]
df = df[df.pickup_longitude.between(-75, -72) & df.dropoff_longitude.between(-75, -72)]
df = df[df.pickup_latitude.between(40, 42) & df.dropoff_latitude.between(40, 42)]

lat1, lon1 = np.radians(df.pickup_latitude), np.radians(df.pickup_longitude)
lat2, lon2 = np.radians(df.dropoff_latitude), np.radians(df.dropoff_longitude)
a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
df["distance_km"] = 6371 * 2 * np.arcsin(np.sqrt(a))
df["hour_of_day"] = pd.to_datetime(df.pickup_datetime).dt.hour
df = df[["distance_km", "passenger_count", "hour_of_day", "fare_amount"]]

q1, q3 = df.fare_amount.quantile([0.25, 0.75])
outliers = ~df.fare_amount.between(q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1))
print("Outliers removed:", outliers.sum())
df = df[~outliers]

print(df.corr().round(2))

X, y = df.drop(columns="fare_amount"), df.fare_amount
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

models = {"Linear Regression": LinearRegression(), "Random Forest": RandomForestRegressor(random_state=42)}
for name, model in models.items():
    pred = model.fit(X_train, y_train).predict(X_test)
    print(f"{name}: R2 = {r2_score(y_test, pred):.3f}, RMSE = {root_mean_squared_error(y_test, pred):.3f}")
