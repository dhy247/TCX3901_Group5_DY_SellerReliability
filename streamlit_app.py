"""
TCX3901 Seller Reliability — Report 1 EDA Dashboard
Run locally with:  streamlit run streamlit_app.py

This is a STANDALONE script — Streamlit apps don't run inside Jupyter, so it
reloads and re-cleans the raw Olist CSVs itself rather than reusing dhy.ipynb's
in-memory variables. The cleaning steps below mirror dhy.ipynb as closely as
possible (same sections referenced in comments) so the numbers here should
match your notebook's own printed numbers — check that once it's running.

DATA: reads the Olist CSVs from the data/ folder in this repository.
"""

from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

# ---------------------------------------------------------------------------
# Color palette — inspired by the Microsoft Edge logo (teal-green fading to
# blue, plus a deep navy accent)
# ---------------------------------------------------------------------------
EDGE_BLUE = "#0F5FBF"
EDGE_NAVY = "#0B3D91"
EDGE_TEAL = "#1DB884"

# ---------------------------------------------------------------------------
# 0. CONFIG — adjust this path to match your Section 1 DATA_DIR
# ---------------------------------------------------------------------------
# Repo version: the five Olist CSVs are in the "data" folder next to this file,
# so the app runs both locally and on Streamlit Community Cloud.
DATA_DIR = Path(__file__).resolve().parent / "data"

st.set_page_config(page_title="Seller Reliability — Report 1 EDA", layout="wide")


# ---------------------------------------------------------------------------
# 1. LOAD + CLEAN DATA (cached so it only runs once per session)
#    Mirrors dhy.ipynb Sections 1, 6, 8, 9
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    orders = pd.read_csv(f"{DATA_DIR}/olist_orders_dataset.csv")
    order_items = pd.read_csv(f"{DATA_DIR}/olist_order_items_dataset.csv")
    order_reviews = pd.read_csv(f"{DATA_DIR}/olist_order_reviews_dataset.csv")
    sellers = pd.read_csv(f"{DATA_DIR}/olist_sellers_dataset.csv")
    products = pd.read_csv(f"{DATA_DIR}/olist_products_dataset.csv")

    # Parse timestamps
    ts_cols = [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in ts_cols:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")
    order_reviews["review_creation_date"] = pd.to_datetime(
        order_reviews["review_creation_date"], errors="coerce"
    )

    # --- Section 6: order-level lead_time_days (delivered orders only) ---
    delivered = orders[orders["order_status"] == "delivered"].copy()
    delivered["lead_time_days"] = (
        delivered["order_delivered_customer_date"] - delivered["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    delivered = delivered.dropna(subset=["lead_time_days"])
    orders["lead_time_days"] = (
        orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    # --- Section 9 Fix 1: dedupe reviews, keep most-recent-by-date per order ---
    reviews_sorted = order_reviews.sort_values(["order_id", "review_creation_date"])
    review_per_order = reviews_sorted.groupby("order_id").last().reset_index()
    review_per_order["poor_rating"] = review_per_order["review_score"] <= 2

    # --- Section 8: order_seller (all distinct order-seller pairs, all sellers) ---
    order_seller = order_items[["order_id", "seller_id"]].drop_duplicates()
    orders_per_seller = order_seller.groupby("seller_id").size().rename("n_orders")

    # --- Figure 4 prep: item-level category + lead time ---
    item_cat = order_items.merge(
        products[["product_id", "product_category_name"]], on="product_id", how="left"
    )
    item_cat = item_cat.merge(
        orders[["order_id", "lead_time_days"]], on="order_id", how="left"
    )

    return delivered, review_per_order, orders_per_seller, item_cat


delivered, review_per_order, orders_per_seller, item_cat = load_data()


# ---------------------------------------------------------------------------
# 2. SIDEBAR — shared filters that link all four views together
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

all_categories = (
    item_cat["product_category_name"].value_counts().head(15).index.tolist()
)
selected_categories = st.sidebar.multiselect(
    "Product category (top 15 by item volume)",
    options=all_categories,
    default=all_categories,  # all selected = no filter, so the defaults match the slides
)

min_orders = st.sidebar.slider(
    "Minimum orders per seller (for the seller-volume view)",
    min_value=1, max_value=50, value=1,
)

# Apply the category filter to the item-level table once, reuse everywhere
filtered_items = item_cat[item_cat["product_category_name"].isin(selected_categories)]
filtered_order_ids = filtered_items["order_id"].dropna().unique()


# ---------------------------------------------------------------------------
# 3. HEADER + KPIs
# ---------------------------------------------------------------------------
st.title("Seller Reliability — EDA Dashboard (Report 1)")
st.caption(
    "Four linked views over the same descriptive findings reported in Report 1's "
    "Exploratory Analysis section. Use the sidebar filters to drill into specific "
    "product categories or seller-volume ranges — all views update together."
)

col1, col2, col3 = st.columns(3)
col1.metric("Delivered orders (all)", f"{len(delivered):,}")
col2.metric("Reviews after dedup", f"{len(review_per_order):,}")
col3.metric("Sellers", f"{len(orders_per_seller):,}")

st.divider()


# ---------------------------------------------------------------------------
# 4. VIEW 1 — Lead-time distribution (filtered by selected categories)
# ---------------------------------------------------------------------------
st.subheader("1. Lead time is right-skewed")

lt_subset = delivered[
    delivered["order_id"].isin(filtered_order_ids)
] if len(selected_categories) < len(all_categories) else delivered

mean_lt = lt_subset["lead_time_days"].mean()
median_lt = lt_subset["lead_time_days"].median()

fig1 = px.histogram(
    lt_subset[lt_subset["lead_time_days"] <= 60],
    x="lead_time_days", nbins=60,
    labels={"lead_time_days": "End-to-end lead time (days, capped at 60)"},
    title=f"Lead time distribution — mean {mean_lt:.1f}d, median {median_lt:.1f}d",
    color_discrete_sequence=[EDGE_BLUE],
)
fig1.add_vline(x=mean_lt, line_dash="dash", line_color=EDGE_NAVY,
                annotation_text=f"Mean = {mean_lt:.1f}d",
                annotation_position="top right")
fig1.add_vline(x=median_lt, line_dash="dash", line_color=EDGE_TEAL,
                annotation_text=f"Median = {median_lt:.1f}d",
                annotation_position="top left")
st.plotly_chart(fig1, width="stretch")


# ---------------------------------------------------------------------------
# 5. VIEW 2 — Review score / poor-rating distribution (same category filter)
# ---------------------------------------------------------------------------
st.subheader("2. Poor ratings are a minority class")

rev_subset = review_per_order[
    review_per_order["order_id"].isin(filtered_order_ids)
] if len(selected_categories) < len(all_categories) else review_per_order

score_counts = rev_subset["review_score"].value_counts().sort_index().reset_index()
score_counts.columns = ["review_score", "count"]
score_counts["pct"] = score_counts["count"] / score_counts["count"].sum() * 100
score_counts["is_poor"] = score_counts["review_score"] <= 2

fig2 = px.bar(
    score_counts, x="review_score", y="count", color="is_poor",
    color_discrete_map={True: EDGE_NAVY, False: EDGE_TEAL},
    text=score_counts["pct"].round(1).astype(str) + "%",
    labels={"review_score": "Review score (1 = worst, 5 = best)", "count": "Number of orders"},
    title="Review score distribution (navy = poor rating, score ≤ 2)",
)
fig2.update_traces(textposition="outside")
st.plotly_chart(fig2, width="stretch")


# ---------------------------------------------------------------------------
# 6. VIEW 3 — Orders per seller (linked to the min-orders slider)
# ---------------------------------------------------------------------------
st.subheader("3. Most sellers are low-volume")

ops_subset = orders_per_seller[orders_per_seller >= min_orders]
pct_under_10 = (orders_per_seller < 10).mean() * 100

fig3 = px.histogram(
    ops_subset.clip(upper=200), nbins=50,
    labels={"value": "Distinct orders per seller (capped at 200)"},
    title=f"Orders per seller — {pct_under_10:.0f}% of all sellers have fewer than 10 orders",
    color_discrete_sequence=[EDGE_TEAL],
)
fig3.add_vline(x=orders_per_seller.median(), line_dash="dash", line_color=EDGE_NAVY,
                annotation_text=f"Median = {orders_per_seller.median():.0f}")
st.plotly_chart(fig3, width="stretch")


# ---------------------------------------------------------------------------
# 6b. VIEW 3b - Orders per seller, grouped (same chart as slide 7 / Figure 3b)
# ---------------------------------------------------------------------------
st.subheader("3b. Orders per seller, grouped (as on slide 7)")

group_labels = ["1", "2", "3", "4-5", "6-9", "10-19", "20-49", "50-99", "100-199", "200+"]
grouped = pd.cut(
    orders_per_seller, bins=[0, 1, 2, 3, 5, 9, 19, 49, 99, 199, float("inf")],
    labels=group_labels,
).value_counts(sort=False).reset_index()
grouped.columns = ["group", "sellers"]
grouped["volume"] = grouped["group"].isin(group_labels[:5]).map(
    {True: "Fewer than 10 orders", False: "10+ orders"}
)
n_low = int((orders_per_seller < 10).sum())
n_high = int((orders_per_seller >= 10).sum())

fig3b = px.bar(
    grouped, x="group", y="sellers", color="volume", text="sellers",
    color_discrete_map={"Fewer than 10 orders": EDGE_NAVY, "10+ orders": EDGE_TEAL},
    labels={"group": "Distinct orders per seller (grouped)", "sellers": "Number of sellers", "volume": ""},
    title=(f"Fewer than 10 orders: {n_low:,} sellers ({n_low / len(orders_per_seller):.0%})  |  "
           f"10+ orders: {n_high:,} sellers ({n_high / len(orders_per_seller):.0%})"),
)
fig3b.update_traces(textposition="outside")
fig3b.update_xaxes(type="category", categoryorder="array", categoryarray=group_labels)
st.plotly_chart(fig3b, width="stretch")


# ---------------------------------------------------------------------------
# 7. VIEW 4 — Mean lead time by category (highlights selected categories)
# ---------------------------------------------------------------------------
st.subheader("4a. Lead time varies by product category")

cat_summary = (
    item_cat.groupby("product_category_name")
    .agg(n_items=("order_id", "count"), mean_lead_time=("lead_time_days", "mean"))
    .sort_values("n_items", ascending=False)
    .head(10)
    .reset_index()
)
cat_summary["selected"] = cat_summary["product_category_name"].isin(selected_categories)
overall_mean = delivered["lead_time_days"].mean()

fig4 = px.bar(
    cat_summary.sort_values("mean_lead_time"),
    x="mean_lead_time", y="product_category_name", orientation="h",
    color="selected",
    color_discrete_map={True: EDGE_NAVY, False: EDGE_TEAL},
    labels={"mean_lead_time": "Mean end-to-end lead time (days)", "product_category_name": ""},
    title="Mean lead time by category (top 10 by item volume; navy = currently selected)",
)
fig4.add_vline(x=overall_mean, line_dash="dash", line_color="gray",
                annotation_text=f"Overall mean = {overall_mean:.1f}d")
st.plotly_chart(fig4, width="stretch")

st.divider()
st.caption(
    "Data: Olist e-commerce dataset."
    
)

st.subheader("4b. Lead time distribution by category (companion to Figure 4a.)")
box_data = item_cat[item_cat["product_category_name"].isin(cat_summary["product_category_name"])]
fig4b = px.box(
    box_data, x="lead_time_days", y="product_category_name",
    orientation="h",
    category_orders={
        "product_category_name": cat_summary.sort_values("mean_lead_time")["product_category_name"].tolist()
    },
    labels={"lead_time_days": "Lead time (days)", "product_category_name": ""},
    title="Lead Time Distribution by Category (shows spread behind Figure 4's means)",
    color_discrete_sequence=[EDGE_TEAL],
)
st.plotly_chart(fig4b, width="stretch")