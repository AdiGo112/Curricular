"""
Assignment 5: K-Means Clustering with the Elbow Method
========================================================

Problem statement
------------------
Cluster a sales-data-like dataset with K-Means, using the elbow method to
pick the number of clusters k.

Approach
--------
- K-Means partitions points into k clusters by repeatedly assigning each
  point to its nearest cluster center, then recomputing centers as the
  mean of their assigned points, until the assignments stop changing.
- `inertia_` (sum of squared distances from each point to its cluster
  center) is computed for k = 1..10. Inertia always decreases as k grows,
  so the "elbow" -- the k where the curve stops dropping sharply and starts
  flattening -- is used to pick a good k without overfitting to k = 10.
- The elbow is located with a simplified "kneedle" approach: normalize both
  axes to [0, 1] and pick the point furthest from the straight line joining
  the first and last points of the curve (a plain second-derivative check
  is biased toward the very first drop and picks too small a k).
- Features are standardized before clustering because `quantity_ordered`
  and `sales_amount` are on very different numeric scales; without scaling,
  K-Means' distance metric would be dominated by sales_amount alone.

Synthetic dataset
------------------
Kaggle's real "sales_data_sample.csv" is not reachable from this
environment (no internet access), so `build_dataset()` generates points
from a KNOWN number of underlying clusters (`make_blobs`, TRUE_N_CLUSTERS =
4), so the elbow method's pick can be checked against that ground truth.
Numbers below are illustrative of the technique, not results on the real
Kaggle data.

Likely viva questions
----------------------
Q: Why does inertia always decrease as k increases, and why not just pick
   k = 10 (lowest inertia)?
A: More clusters can only reduce or keep equal the distance from each point
   to its nearest center, so inertia is monotonically non-increasing in k.
   Always picking the largest k overfits -- every point could get its own
   cluster (inertia = 0) but that's useless. The elbow finds where adding
   more clusters stops meaningfully helping.

Q: Why scale features before K-Means but not before Random Forest
   (Assignment 1)?
A: K-Means clusters based on Euclidean distance, so a feature on a much
   larger numeric scale would dominate that distance; tree splits are
   invariant to the scale of any single feature.

Q: What does a high vs low inertia value mean?
A: Low inertia means points are tightly packed around their cluster
   centers (good fit for that k); high inertia means points are spread far
   from their assigned centers.

Q: How is the elbow point actually chosen in this script, and why not a
   simple second-derivative check?
A: By normalizing the (k, inertia) curve to [0, 1] on both axes and picking
   the point with the largest perpendicular distance from the line joining
   its first and last points. A plain second-derivative check is biased
   toward the very first, largest drop (e.g. k=1 to k=2) and can miss the
   true knee further along the curve.
"""

import matplotlib
matplotlib.use("Agg")  # no display needed; just save the plot to a file
import matplotlib.pyplot as plt

import numpy as np
from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

RNG_SEED = 13
TRUE_N_CLUSTERS = 4
OUTPUT_PNG = "elbow_curve.png"


# BUILD A SYNTHETIC SALES DATASET: quantity_ordered vs sales_amount,
# generated from TRUE_N_CLUSTERS known customer segments.

def build_dataset():
    # Equal, well-separated blobs so the elbow method has a clear knee.
    X, _ = make_blobs(
        n_samples=400,
        centers=TRUE_N_CLUSTERS,
        n_features=2,
        cluster_std=1.0,
        center_box=(-12.0, 12.0),
        random_state=RNG_SEED,
    )
    # Stretch into quantity_ordered / sales_amount-like ranges. A uniform
    # per-axis scale keeps the relative cluster separation unchanged.
    quantity_ordered = 10 * X[:, 0] + 80
    sales_amount = 700 * X[:, 1] + 6000
    X = np.column_stack([quantity_ordered, sales_amount])
    # Clip negative values -- quantity/amount can't go below zero.
    return np.clip(X, a_min=0, a_max=None)


# ELBOW METHOD: compute inertia for k=1..10, pick the "knee" as the k whose
# point is furthest from the straight line joining the first and last points
# of the (k, inertia) curve -- the standard way to locate a knee on a convex,
# decreasing curve (a simplified "kneedle" approach).

def find_elbow(inertias):
    k_values = np.arange(1, len(inertias) + 1)

    # Normalize both axes to [0, 1] so scale doesn't bias the distances.
    k_norm = (k_values - k_values.min()) / (k_values.max() - k_values.min())
    inertia = np.asarray(inertias, dtype=float)
    inertia_norm = (inertia - inertia.min()) / (inertia.max() - inertia.min())

    # Perpendicular distance of each point from the line through the first
    # and last points (both on the normalized curve, which runs (0,1)->(1,0)).
    distances = np.abs(inertia_norm + k_norm - 1) / np.sqrt(2)
    elbow_k = int(k_values[np.argmax(distances)])
    return elbow_k


if __name__ == "__main__":
    X = build_dataset()
    print(f"Dataset: {len(X)} points, generated from {TRUE_N_CLUSTERS} true clusters\n")

    # quantity_ordered and sales_amount are on very different scales; without
    # scaling, KMeans distances would be dominated by sales_amount alone.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    k_values = range(1, 11)
    inertias = []
    for k in k_values:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    chosen_k = find_elbow(inertias)
    print("Inertia per k:")
    for k, inertia in zip(k_values, inertias):
        marker = "  <- elbow" if k == chosen_k else ""
        print(f"k={k:<3} inertia={inertia:>14,.1f}{marker}")

    # SAVE ELBOW CURVE PLOT
    plt.figure(figsize=(6, 4))
    plt.plot(list(k_values), inertias, marker="o")
    plt.axvline(chosen_k, color="red", linestyle="--", label=f"chosen k={chosen_k}")
    plt.xlabel("k (number of clusters)")
    plt.ylabel("Inertia")
    plt.title("Elbow Method for K-Means")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG)
    print(f"\nElbow curve saved to {OUTPUT_PNG}")

    # FINAL K-MEANS FIT AT THE CHOSEN k
    final_km = KMeans(n_clusters=chosen_k, random_state=42, n_init=10)
    labels = final_km.fit_predict(X_scaled)
    centers = scaler.inverse_transform(final_km.cluster_centers_)  # back to original units

    print(f"\nFinal K-Means fit with k={chosen_k}:")
    print("Cluster centers (quantity_ordered, sales_amount):")
    print(np.round(centers, 1))
    print("Cluster sizes:", np.bincount(labels).tolist())

    # SANITY CHECK: the elbow method should land close to the true
    # number of generated clusters.
    assert abs(chosen_k - TRUE_N_CLUSTERS) <= 1, f"Elbow pick {chosen_k} far from true {TRUE_N_CLUSTERS}"
    print(f"\nSanity check passed: chosen k={chosen_k} is within 1 of the true {TRUE_N_CLUSTERS}")
