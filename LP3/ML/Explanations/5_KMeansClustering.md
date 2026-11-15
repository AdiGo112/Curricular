# Assignment 5: K-Means Clustering with the Elbow Method

## Problem statement
Cluster a sales-data-like dataset with K-Means, using the elbow method to
pick the number of clusters k.

## Approach
- K-Means partitions points into k clusters by repeatedly assigning each
  point to its nearest cluster center, then recomputing centers as the
  mean of their assigned points, until the assignments stop changing.
- `inertia_` (sum of squared distances from each point to its cluster
  center) is computed for k = 1..10. Inertia always decreases as k grows,
  so the "elbow" -- the k where the curve stops dropping sharply and
  starts flattening -- is used to pick a good k without overfitting to
  k = 10.
- The elbow is located with a simplified "kneedle" approach: normalize
  both axes to [0, 1] and pick the point furthest from the straight line
  joining the first and last points of the curve (a plain
  second-derivative check is biased toward the very first drop and picks
  too small a k).
- Features are standardized before clustering because `QUANTITYORDERED`
  and `SALES` are on very different numeric scales; without scaling,
  K-Means' distance metric would be dominated by `SALES` alone.

## Implementation notes
- Elbow in code: inertia is scaled to [0, 1] and k is spread evenly over
  [0, 1]. The straight line from the first to the last point is then
  `y = 1 - x`, so the gap below it is `1 - scaled - x`, and the k with the
  largest gap is the elbow.
- The elbow comes out at k = 3 and the plot is saved as `elbow_curve.png`.
- `kmeans_clusters.png` plots scaled quantity against scaled sales,
  coloured by K-Means cluster.
- `hierarchical_clusters.png` is the same plot for hierarchical
  (agglomerative, Ward linkage) clustering with the same k, for comparison.
  It merges the closest groups bottom-up instead of moving centroids, so
  the boundaries differ a little.
- The final table shows, per cluster, the number of orders and the mean
  quantity and sales in original units.

## Dataset
The real Kaggle "Sample Sales Data" (sales_data_sample.csv), 2,823
orders; `QUANTITYORDERED` and `SALES` are used as the two clustering
features, saved locally at `data/sales_data_sample.csv`. The file has a
couple of non-UTF-8 bytes in free-text columns (customer/address names),
hence `encoding="latin1"`.

## Viva prep

**Q: Why does inertia always decrease as k increases, and why not just
pick k = 10 (lowest inertia)?**
A: More clusters can only reduce or keep equal the distance from each
point to its nearest center, so inertia is monotonically non-increasing
in k. Always picking the largest k overfits -- every point could get its
own cluster (inertia = 0) but that's useless. The elbow finds where
adding more clusters stops meaningfully helping.

**Q: Why scale features before K-Means but not before a tree-based
model?**
A: K-Means clusters based on Euclidean distance, so a feature on a much
larger numeric scale would dominate that distance; tree splits are
invariant to the scale of any single feature.

**Q: What does a high vs low inertia value mean?**
A: Low inertia means points are tightly packed around their cluster
centers (good fit for that k); high inertia means points are spread far
from their assigned centers.

**Q: How is the elbow point actually chosen in this script, and why not a
simple second-derivative check?**
A: By normalizing the (k, inertia) curve to [0, 1] on both axes and
picking the point with the largest perpendicular distance from the line
joining its first and last points. A plain second-derivative check is
biased toward the very first, largest drop (e.g. k=1 to k=2) and can miss
the true knee further along the curve.
