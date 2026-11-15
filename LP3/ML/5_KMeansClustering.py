from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
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

plt.figure()
plt.plot(ks, inertias, marker="o")
plt.axvline(k, color="red", linestyle="--")
plt.xlabel("k")
plt.ylabel("Inertia")
plt.savefig(HERE / "elbow_curve.png")
plt.show()

df["cluster"] = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
print(df.groupby("cluster").agg(orders=("SALES", "size"), quantity=("QUANTITYORDERED", "mean"), sales=("SALES", "mean")).round(1))

clusterings = {"K-Means Clustering": df.cluster, "Hierarchical Clustering": AgglomerativeClustering(n_clusters=k).fit_predict(X)}
for title, labels in clusterings.items():
    plt.figure()
    plt.scatter(X[:, 0], X[:, 1], c=labels, cmap="rainbow")
    plt.title(title)
    plt.xlabel("Quantity Ordered (Scaled)")
    plt.ylabel("Sales (Scaled)")
    plt.savefig(HERE / f"{title.split()[0].lower().replace('-', '')}_clusters.png")
    plt.show()
