# rcp_anomaly_scan — entity anomaly scores, graph rings, threshold bunching

**Navigator nodes:** `N-ANOM-MULTI`, `N-ANOM-GRAPH`, `N-ANOM-STRUCT` · **First used:** L8.5 · **Status:** working

Three modes: `score` (robust z on a chosen metric with a mean-absolute-deviation fallback when MAD = 0, plus Isolation Forest, flagged
counts and overlap at several contamination levels), `graph` (connected components of entities sharing links; label rates), and
`bunching` (counts just below vs above a threshold, histogram).
