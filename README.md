 # 📊 E-Commerce Customer Analytics & Strategic Revenue Optimization
> **An End-to-End Data Analytics Portfolio Project**  
> *Data Cleaning, RFM Customer Behavioral Segmentation, In-Memory SQL Analytics (DuckDB), and Enterprise Power BI Architecture.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Interactive%20Dashboard-FF4B4B.svg)](https://streamlit.io/)
[![DuckDB](https://img.shields.io/badge/DuckDB-In--Memory%20SQL-yellow.svg)](https://duckdb.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Wrangling-150458.svg)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Visuals-3F4F75.svg)](https://plotly.com/)
[![Status](https://img.shields.io/badge/Status-Completed%20%26%20Verified-success.svg)]()
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=Segn11/retail-sales-analytics&branch=main&mainModule=app.py)

---

## 📌 Executive Project Snapshot

| Strategic KPI | Benchmark Metric | Analytical & Business Context |
| :--- | :---: | :--- |
| **Gross Clean Sales Revenue** | **£8,911,407.90** | Net recognized revenue across 392,692 non-cancelled operational line items |
| **Operational Transactions** | **392,692** | Valid purchase records after deduplication and guest-checkout handling |
| **Active Customer Accounts** | **4,338** | Tracked individual customer profiles across 38 global markets |
| **Transaction Return Rate** | **14.81%** | 3,836 cancelled/returned invoices out of 25,900 registered order logs |
| **Average Customer Spend (CLV)** | **£2,048.69** | Right-skewed distribution (median: £668.57) reflecting heavy wholesale reliance |
| **Top Non-UK Export Market** | **Netherlands (£285.4k)** | Leading European territory by both gross revenue and volume (200k units) |

---

## 📖 Business Problem & Project Overview

This project analyzes the end-to-end transactional history of a UK-based non-store online retailer operating between **December 1, 2010, and December 9, 2011**. The business primarily retails giftware items, serving a dual clientele of everyday retail shoppers and high-volume commercial wholesalers.

### Key Business Challenges Addressed:
1. **Severe Revenue Seasonality:** Heavy dependence on Q4 pre-holiday restocking leaves the business exposed to cash-flow contractions earlier in the year.
2. **Margin Erosion via Returns:** A 14.81% order cancellation rate causes warehouse bottlenecks and courier cost leakage.
3. **Undifferentiated Marketing:** High-value wholesale buyers (generating up to £280k annually) receive the same treatment as one-time £20 retail buyers.

---

## 🏗️ Analytical Architecture & Methodology

```
┌─────────────────────────┐
│ Raw Data Ingestion      │ ──► 541,909 records loaded & schema-validated
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Data Cleaning & Audit   │ ──► Deduplication (-5,268 rows)
│                         │ ──► Isolation of Cancellations ('C%') into df_cancellations (8,872 rows)
│                         │ ──► Clean operational sales filtered into df_clean (392,692 rows)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Feature Engineering     │ ──► Revenue = Quantity * UnitPrice
│ & RFM Segmentation      │ ──► Temporal decomposition: Year, Month, Hour, DayOfWeek
│                         │ ──► Customer RFM Modeling (Recency, Frequency, Monetary)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Exploratory Analytics   │ ──► Monthly revenue/order trends & macro seasonality
│ & Data Storytelling     │ ──► International export corridor analysis (Netherlands, EIRE, Germany, France)
│                         │ ──► Return SKU forensics & RFM Pareto distribution analysis
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ DuckDB SQL Engine       │ ──► Serverless, in-memory analytical SQL executing 5 business queries
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Enterprise Power BI     │ ──► Star Schema data model (Fact_Sales, Fact_Cancellations, Dimensions)
│ Blueprint & Measures    │ ──► Production DAX measures & 3-page interactive dashboard wireframes
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Executive Action Plan   │ ──► Prioritized 30–60–90 day commercial & operational roadmap
└─────────────────────────┘
```

---

## 💡 Key Analytical Findings

1. **Macro Seasonality:** Revenue remains stable from Jan–Aug (£450k–£650k/mo), before surging exponentially in late autumn. **November 2011 reached the absolute peak of £1.13M+ across 2,657 orders**, driven by B2B wholesalers restocking ahead of consumer holiday shopping.
2. **Top European Export Corridor:** Four European nations generate over 80% of all international sales:
   - **Netherlands:** £285,446 (200,361 units)
   - **EIRE (Ireland):** £265,545 (140,418 units)
   - **Germany:** £228,867 (119,261 units)
   - **France:** £209,715 (111,472 units)
3. **Cancellation Drivers:** Two specific SKUs account for over 155,000 cancelled units: `"PAPER CRAFT , LITTLE BIRDIE"` (80,995 units) and `"MEDIUM CERAMIC TOP STORAGE JAR"` (74,494 units), indicating wholesale checkout double-entry errors or transit packaging fragility.
4. **Wholesale Concentration:** Customer **14646** (£280,206 spend / 73 orders) and Customer **18102** (£259,657 spend / 60 orders) represent massive individual revenue streams requiring dedicated Key Account Management.

---

## 🎯 Strategic Business Recommendations (30–60–90 Day Plan)

### 🟢 Immediate Tactical Wins (Days 0–30)
* **Checkout Quantity Modal:** Implement frontend validation requiring confirmation for bulk orders exceeding 250 units, instantly preventing accidental multi-thousand-unit returns.
* **Packaging Quality Audit:** Reinforce packaging standards for fragile ceramic items to mitigate transit breakage.

### 🟡 Mid-Term Commercial Expansion (Days 30–60)
* **European Fulfillment Node:** Contract a 3PL fulfillment partnership in the Netherlands or Germany to serve continental European customers with 24–48 hour delivery windows.
* **Algorithmic Product Bundling:** Create curated bundles for frequently co-purchased items (e.g., T-Light Holders & ceramic kitchenware) with a 7% bundle discount to increase consumer AOV.

### 🟣 Long-Term Transformation (Days 60–90)
* **VIP Wholesale Account Tier:** Formalize customized credit terms, automated EDI replenishment, and volume tiered discounts for the top 50 B2B buyers.
* **Automated RFM Churn Reactivation:** Configure automated CRM marketing triggers for customers entering the 'At Risk' segment (Recency > 90 days with historically high Frequency).

---

## 💻 Tech Stack & Environment Setup

### Prerequisites
* Python 3.10+
* Jupyter Notebook or Google Colab

### Installation
Clone this repository and install required packages:
```bash
pip install -r requirements.txt
```

### Execution

#### Option A: Launch Interactive Streamlit Web Dashboard
Run the interactive dashboard locally:
```bash
streamlit run app.py
```
*(Features dynamic KPI scorecards, date/country filters, RFM customer segment scatter plots, and return forensics).*

#### Option B: Run Analytical Notebook
Open the notebook in Jupyter or VS Code:
```bash
jupyter notebook Online_Retail_analytics.ipynb
```

---

## 📁 Repository Structure
```
├── app.py                          # Streamlit interactive web dashboard
├── Online_Retail_analytics.ipynb   # Main portfolio showcase notebook (Cleaned, fully executed)
├── Online Retail.xlsx               # Source transactional dataset (541k records)
├── requirements.txt                 # Python dependency specifications
└── README.md                        # Portfolio documentation & executive summary
```

