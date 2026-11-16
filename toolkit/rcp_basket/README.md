# rcp_basket — association rules with support, confidence, lift

**Navigator node:** `N-SEG-BASKET` · **First used:** L8.3 · **Status:** working

Pairwise rules between items (e.g. subcategories) within baskets; filters by `min_support` and `min_lift`; flags high-confidence rules
whose consequent is simply popular (`common_share`). `item_map` derives the item from a lookup (sku → subcategory). Output `rules.csv`.
