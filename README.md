# Seller Reliability Analysis for the SmartCommerce Marketplace

TCX3901 Industrial Practice (NUS) · Group 5 · Dhita Yasaningrum

Two related tasks on the public Olist Brazilian e-commerce data (SmartCommerce is the hypothetical marketplace context):

- **Regression:** predict a seller's average delivery lead time (purchase date to customer delivery date).
- **Classification:** flag sellers at risk of poor customer ratings in the following month.

## Live dashboard

Streamlit app: **[add the Streamlit Community Cloud URL here after deploying]**

Run locally:

```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Repository contents

| Path | What it is |
|---|---|
| `streamlit_app.py` | EDA dashboard (lead-time distribution, review scores, orders per seller, category lead time, with filters). Reads the CSVs in `data/`. |
| `data/` | The five Olist tables used in the project, plus the category name translation table. |
| `notebooks/v1_Report1_2026-09-12/` | **Version 1:** the notebook as submitted with Report 1 (HTML export): TCX3901_Group5_DY_Report1_Notebook_v1.html |
| `notebooks/v2_2026-10-08/` | **Version 2:** the current notebook (`TCX3901_Group5_DY_SellerReliabilityNotebook_v2.ipynb`), used for Presentation 1. |
| `docs/NB_EditPostR1.pdf` | Change log: every change from version 1 to version 2. |

## Notebook versions

- **v1 (12 Sep 2026):** Report 1 submission. Baselines A (overall mean) and B (seller's own mean), order-level classification baseline, four EDA figures.
- **v2 (8 Oct 2026):** adds Baseline C (median of the last 30 training days, MAE 2.81 / RMSE 3.99) with a 30/60/90-day sensitivity check, a leakage check, the drop-not-impute step (2,945 sellers), extra reconciliation cells for the order and seller counts, Figure 3b (slide 7 chart) and Figure 4b. No Report 1 number changed. Details: `docs/NB_EditPostR1.pdf`.

To run the notebook, set `DATA_DIR` in Section 1 to the `data/` folder of this repository.

## Data

Olist Brazilian E-Commerce Public Dataset (Kaggle), licensed CC BY-NC-SA 4.0. Used here for non-commercial academic purposes.
