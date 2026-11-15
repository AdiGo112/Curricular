from pathlib import Path

import matplotlib.pyplot as plt
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
pickup_time = pd.to_datetime(df.pickup_datetime)
df["hour_of_day"] = pickup_time.dt.hour
df["year"] = pickup_time.dt.year
df = df[df.distance_km > 0][["distance_km", "passenger_count", "hour_of_day", "year", "fare_amount"]]

df.boxplot(column=["fare_amount", "distance_km"])
plt.savefig(HERE / "outlier_boxplot.png")

rows = len(df)
for column in ["fare_amount", "distance_km"]:
    q1, q3 = df[column].quantile([0.25, 0.75])
    df = df[df[column].between(q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1))]
print("Outliers removed:", rows - len(df))

corr = df.corr()
print(corr.round(2))
plt.figure()
plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
plt.xticks(range(len(corr)), corr.columns, rotation=45)
plt.yticks(range(len(corr)), corr.columns)
plt.colorbar()
plt.savefig(HERE / "correlation_heatmap.png", bbox_inches="tight")

df.plot.scatter("distance_km", "fare_amount", s=1, alpha=0.05)
plt.savefig(HERE / "distance_vs_fare.png")

X, y = df.drop(columns="fare_amount"), df.fare_amount
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

models = {"Linear Regression": LinearRegression(), "Random Forest": RandomForestRegressor(max_depth=10, random_state=42)}
axes = plt.subplots(1, 2, figsize=(10, 4))[1]
for ax, (name, model) in zip(axes, models.items()):
    pred = model.fit(X_train, y_train).predict(X_test)
    print(f"{name}: R2 = {r2_score(y_test, pred):.3f}, RMSE = {root_mean_squared_error(y_test, pred):.3f}")
    ax.scatter(y_test, pred, s=1, alpha=0.05)
    ax.plot([0, y_test.max()], [0, y_test.max()], color="red")
    ax.set(title=name, xlabel="Actual fare", ylabel="Predicted fare")
plt.savefig(HERE / "predicted_vs_actual.png")
