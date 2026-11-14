from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).parent
DATA = HERE / "data" / "sales_data_sample.csv"
if not DATA.exists():
    DATA = HERE / "sales_data_sample.csv"

df = pd.read_csv(DATA, encoding="latin1")[["QUANTITYORDERED", "SALES"]]
X = StandardScaler().fit_transform(df)

ks = range(1, 11)
inertias = np.array([KMeans(n_clusters=k, n_init=10, random_state=42).fit(X).inertia_ for k in ks])

scaled = (inertias - inertias.min()) / (inertias.max() - inertias.min())
k = ks[np.argmax(1 - scaled - np.linspace(0, 1, len(ks)))]
print("Elbow at k =", k)

plt.plot(ks, inertias, marker="o")
plt.axvline(k, color="red", linestyle="--")
plt.xlabel("k")
plt.ylabel("Inertia")
plt.savefig(HERE / "elbow_curve.png")

df["cluster"] = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
print(df.groupby("cluster").agg(orders=("SALES", "size"), quantity=("QUANTITYORDERED", "mean"), sales=("SALES", "mean")).round(1))
