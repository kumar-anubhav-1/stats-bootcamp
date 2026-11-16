# rcp_cluster — segments by K-Means with silhouette and profiles

**Navigator nodes:** `N-CLUST-KMEANS`, `N-CLUST-GMM` · **First used:** L8.1 · **Status:** working

Builds an entity feature table from rows (`aggregate`, `share_of`, `log`), scales it, runs K-Means over `k_range`, reports silhouette
by k, fits the chosen k and describes each cluster by its most distinctive features. Outputs `assignments.csv`, `profiles.csv`.
Weak silhouettes (< 0.25) are flagged: judge segments by actionability.
