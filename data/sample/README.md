# Olist sample (CI / demo only)

This is a **deterministic 8,000-order sample** of the Olist tables the experiment reads
(orders, order_items, order_payments, customers), produced by `scripts/build_sample.py`
(seed 42). It exists so CI and the hosted dashboard can run without the full dataset.

**This is not the full dataset.** Headline results in `reports/experiment_001.md`/`.json`
come from the full data. Download the full dataset:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
