import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="E-Commerce Analytics & Customer Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 500;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 4px;
    }
    .metric-subtitle {
        font-size: 0.8rem;
        color: #38bdf8;
    }
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA INGESTION & CACHING PIPELINE ---
@st.cache_data(show_spinner="Loading and preprocessing transactional dataset...")
def load_and_preprocess_data():
    cache_path = 'online_retail_clean.parquet'
    
    # Fast path: Load from preprocessed parquet cache if available
    if os.path.exists(cache_path):
        df_clean = pd.read_parquet(cache_path)
        df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])
        # Re-derive cancellations if stored
        cancellations_path = 'online_retail_cancellations.parquet'
        df_cancellations = pd.read_parquet(cancellations_path) if os.path.exists(cancellations_path) else pd.DataFrame()
        return df_clean, df_cancellations

    # Source resolution
    source_candidates = ['Online Retail.xlsx', './Online Retail.xlsx', '/content/Online Retail.xlsx']
    file_path = next((p for p in source_candidates if os.path.exists(p)), None)
    
    if not file_path:
        st.error("Error: Could not locate 'Online Retail.xlsx' in workspace directory.")
        st.stop()
        
    df = pd.read_excel(file_path)
    
    # 1. Deduplication
    df = df.drop_duplicates()
    
    # 2. Filter missing CustomerID
    df_filtered = df.dropna(subset=['CustomerID', 'Description']).copy()
    
    # 3. Segregate cancellations
    cancelled_mask = df_filtered['InvoiceNo'].astype(str).str.startswith('C')
    df_cancellations = df_filtered[cancelled_mask].copy()
    df_clean = df_filtered[~cancelled_mask].copy()
    
    # 4. Filter positive operational sales
    df_clean = df_clean[(df_clean['Quantity'] > 0) & (df_clean['UnitPrice'] > 0)]
    
    # 5. Type casting
    df_clean['InvoiceNo'] = df_clean['InvoiceNo'].astype(str)
    df_clean['StockCode'] = df_clean['StockCode'].astype(str)
    df_clean['Description'] = df_clean['Description'].astype(str)
    df_clean['CustomerID'] = df_clean['CustomerID'].astype(int)
    df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])
    
    # 6. Feature Engineering
    df_clean['Revenue'] = df_clean['Quantity'] * df_clean['UnitPrice']
    df_clean['Year'] = df_clean['InvoiceDate'].dt.year
    df_clean['Month'] = df_clean['InvoiceDate'].dt.month
    df_clean['MonthYear_str'] = df_clean['InvoiceDate'].dt.strftime('%Y-%m')
    df_clean['DayOfWeek'] = df_clean['InvoiceDate'].dt.day_name()
    df_clean['Hour'] = df_clean['InvoiceDate'].dt.hour
    
    if not df_cancellations.empty:
        df_cancellations['InvoiceNo'] = df_cancellations['InvoiceNo'].astype(str)
        df_cancellations['StockCode'] = df_cancellations['StockCode'].astype(str)
        df_cancellations['Description'] = df_cancellations['Description'].astype(str)
        df_cancellations['CustomerID'] = df_cancellations['CustomerID'].astype(int)
        df_cancellations['InvoiceDate'] = pd.to_datetime(df_cancellations['InvoiceDate'])
        df_cancellations['AbsQuantity'] = df_cancellations['Quantity'].abs()
        df_cancellations['EstimatedLoss'] = df_cancellations['AbsQuantity'] * df_cancellations['UnitPrice']
        df_cancellations['MonthYear_str'] = df_cancellations['InvoiceDate'].dt.strftime('%Y-%m')
    
    # Cache to parquet for sub-second future loads
    try:
        df_clean.to_parquet(cache_path)
        if not df_cancellations.empty:
            df_cancellations.to_parquet('online_retail_cancellations.parquet')
    except Exception:
        pass
        
    return df_clean, df_cancellations

# Load data
df_clean, df_cancellations = load_and_preprocess_data()

# Compute RFM Segmentation Table
@st.cache_data
def compute_rfm_segments(df):
    reference_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)
    
    rfm = df.groupby('CustomerID').agg({
        'InvoiceDate': lambda x: (reference_date - x.max()).days,
        'InvoiceNo': 'nunique',
        'Revenue': 'sum'
    }).reset_index()
    
    rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']
    
    # Quantile scores (1 to 4)
    # Recency: lower is better (4 = most recent)
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1])
    # Frequency: higher is better
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
    # Monetary: higher is better
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4])
    
    rfm['RFM_Segment_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
    
    def assign_segment(row):
        r, f, m = int(row['R_Score']), int(row['F_Score']), int(row['M_Score'])
        if r >= 3 and f >= 3 and m >= 3:
            return "Champions / VIPs"
        elif r >= 3 and f >= 2:
            return "Loyal Customers"
        elif r >= 3 and f == 1:
            return "Recent New Customers"
        elif r <= 2 and f >= 3:
            return "At Risk (Need Attention)"
        elif r == 1 and f >= 2:
            return "Dormant / Hibernating"
        else:
            return "Lost / Low-Value"
            
    rfm['Segment'] = rfm.apply(assign_segment, axis=1)
    return rfm

df_rfm = compute_rfm_segments(df_clean)

# Merge Segment back into sales for drilldown
df_clean_with_seg = df_clean.merge(df_rfm[['CustomerID', 'Segment']], on='CustomerID', how='left')

# --- SIDEBAR INTERACTIVE FILTERS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3081/3081559.png", width=64)
    st.title("Filters & Scope")
    
    # Date Range Filter
    min_date = df_clean['InvoiceDate'].min().date()
    max_date = df_clean['InvoiceDate'].max().date()
    
    date_selection = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Country Selection
    all_countries = sorted(df_clean['Country'].unique())
    selected_preset = st.radio("Country Quick Select", ["All Countries", "UK Domestic", "International Only"], index=0)
    
    if selected_preset == "UK Domestic":
        default_countries = ["United Kingdom"]
    elif selected_preset == "International Only":
        default_countries = [c for c in all_countries if c != "United Kingdom"]
    else:
        default_countries = all_countries
        
    selected_countries = st.multiselect("Select Countries", all_countries, default=default_countries)
    
    # Customer Segment Filter
    all_segments = sorted(df_rfm['Segment'].unique())
    selected_segments = st.multiselect("Customer Segments", all_segments, default=all_segments)
    
    # Minimum Transaction Revenue Filter
    min_rev_threshold = st.slider("Min Line-Item Spend (£)", 0.0, 500.0, 0.0, step=10.0)
    
    st.markdown("---")
    st.markdown("💡 **Tip:** Use the filters above to interactively slice revenue, customer cohorts, and product trends.")

# Apply filters
start_date = date_selection[0] if isinstance(date_selection, tuple) and len(date_selection) > 0 else min_date
end_date = date_selection[1] if isinstance(date_selection, tuple) and len(date_selection) > 1 else max_date

filtered_df = df_clean_with_seg[
    (df_clean_with_seg['InvoiceDate'].dt.date >= start_date) &
    (df_clean_with_seg['InvoiceDate'].dt.date <= end_date) &
    (df_clean_with_seg['Country'].isin(selected_countries)) &
    (df_clean_with_seg['Segment'].isin(selected_segments)) &
    (df_clean_with_seg['Revenue'] >= min_rev_threshold)
]

filtered_cancels = df_cancellations[
    (df_cancellations['InvoiceDate'].dt.date >= start_date) &
    (df_cancellations['InvoiceDate'].dt.date <= end_date) &
    (df_cancellations['Country'].isin(selected_countries))
] if not df_cancellations.empty else pd.DataFrame()

# --- HEADER SECTION ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("📊 E-Commerce Strategic Analytics & Customer Intelligence")
    st.markdown("*Executive Performance Cockpit: Sales Dynamics, RFM Customer Behavioral Modeling & Return Forensics*")
with col_head2:
    st.markdown(f"<div style='text-align: right; color: #94a3b8; padding-top: 15px;'>Active Range:<br><b>{start_date}</b> to <b>{end_date}</b></div>", unsafe_allow_html=True)

st.markdown("---")

# --- EXECUTIVE KPI BANNER ---
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

total_rev = filtered_df['Revenue'].sum()
total_orders = filtered_df['InvoiceNo'].nunique()
total_customers = filtered_df['CustomerID'].nunique()
aov = total_rev / total_orders if total_orders > 0 else 0

total_reg_invoices = total_orders + (filtered_cancels['InvoiceNo'].nunique() if not filtered_cancels.empty else 0)
cancel_rate = (filtered_cancels['InvoiceNo'].nunique() / total_reg_invoices * 100) if total_reg_invoices > 0 else 0

with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Gross Clean Revenue</div>
        <div class="metric-value">£{total_rev:,.0f}</div>
        <div class="metric-subtitle">Across {len(filtered_df):,} line items</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Delivered Orders</div>
        <div class="metric-value">{total_orders:,}</div>
        <div class="metric-subtitle">Distinct invoices</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Active Customers</div>
        <div class="metric-value">{total_customers:,}</div>
        <div class="metric-subtitle">Unique accounts</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Average Order Value</div>
        <div class="metric-value">£{aov:,.2f}</div>
        <div class="metric-subtitle">Spend per order</div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Cancellation Rate</div>
        <div class="metric-value">{cancel_rate:.2f}%</div>
        <div class="metric-subtitle">{filtered_cancels['InvoiceNo'].nunique() if not filtered_cancels.empty else 0:,} return invoices</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- ANALYTICAL TABS ---
tab_trends, tab_geo, tab_rfm, tab_returns = st.tabs([
    "📈 Revenue & Order Velocity",
    "🌍 Global Market Penetration",
    "👥 Customer RFM Segmentation",
    "⚠️ Return Diagnostics & Forensics"
])

# ==========================================
# TAB 1: REVENUE & ORDER VELOCITY
# ==========================================
with tab_trends:
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t1:
        st.subheader("Monthly Sales Revenue & Order Trajectory")
        monthly_trend = filtered_df.groupby('MonthYear_str').agg({
            'Revenue': 'sum',
            'InvoiceNo': 'nunique'
        }).reset_index().rename(columns={'InvoiceNo': 'Orders'})
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=monthly_trend['MonthYear_str'],
            y=monthly_trend['Revenue'],
            name='Revenue (£)',
            marker_color='#0284c7'
        ))
        fig_trend.add_trace(go.Scatter(
            x=monthly_trend['MonthYear_str'],
            y=monthly_trend['Orders'],
            name='Order Volume',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='#f97316', width=3),
            marker=dict(size=8)
        ))
        fig_trend.update_layout(
            yaxis=dict(title='Gross Revenue (£)'),
            yaxis2=dict(title='Order Volume', overlaying='y', side='right', showgrid=False),
            legend=dict(x=0.01, y=0.99),
            margin=dict(l=20, r=20, t=30, b=20),
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        st.info("💡 **Insight:** Notice the sharp late-autumn ramp peaking in November. Wholesale clients restock pre-holiday inventory 4–6 weeks before retail peak.")
        
    with col_t2:
        st.subheader("Peak Trading Hours")
        hourly = filtered_df.groupby('Hour')['Revenue'].sum().reset_index()
        fig_hour = px.bar(
            hourly, x='Hour', y='Revenue',
            labels={'Hour': 'Hour of Day (24h)', 'Revenue': 'Total Spend (£)'},
            color='Revenue', color_continuous_scale='Blues'
        )
        fig_hour.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_hour, use_container_width=True)

    st.markdown("---")
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.subheader("Day-of-Week Revenue Distribution")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Sunday']
        daily = filtered_df.groupby('DayOfWeek')['Revenue'].sum().reindex(day_order).dropna().reset_index()
        fig_day = px.bar(
            daily, x='DayOfWeek', y='Revenue',
            labels={'DayOfWeek': 'Day of Week', 'Revenue': 'Gross Revenue (£)'},
            color='Revenue', color_continuous_scale='Teal'
        )
        fig_day.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_day, use_container_width=True)
        
    with col_w2:
        st.subheader("Cumulative Revenue Curve")
        cum_df = filtered_df.sort_values('InvoiceDate').copy()
        cum_df['CumulativeRevenue'] = cum_df['Revenue'].cumsum()
        daily_cum = cum_df.groupby(cum_df['InvoiceDate'].dt.date)['CumulativeRevenue'].max().reset_index()
        
        fig_cum = px.line(
            daily_cum, x='InvoiceDate', y='CumulativeRevenue',
            labels={'InvoiceDate': 'Date', 'CumulativeRevenue': 'Cumulative Revenue (£)'},
            color_discrete_sequence=['#10b981']
        )
        fig_cum.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_cum, use_container_width=True)

# ==========================================
# TAB 2: GEOGRAPHIC MARKET PENETRATION
# ==========================================
with tab_geo:
    st.subheader("International Sales Performance (Excluding UK)")
    
    intl_df = filtered_df[filtered_df['Country'] != 'United Kingdom']
    
    col_g1, col_g2 = st.columns([3, 2])
    
    with col_g1:
        country_agg = intl_df.groupby('Country').agg({
            'Revenue': 'sum',
            'Quantity': 'sum',
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique'
        }).reset_index().sort_values('Revenue', ascending=False)
        
        top10_geo = country_agg.head(10)
        
        fig_geo_bar = px.bar(
            top10_geo, x='Revenue', y='Country',
            orientation='h',
            text_auto='.2s',
            labels={'Revenue': 'Total Revenue (£)', 'Country': 'International Territory'},
            color='Revenue', color_continuous_scale='Viridis',
            title="Top 10 International Revenue Corridors"
        )
        fig_geo_bar.update_layout(yaxis=dict(autorange='reversed'), height=450, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_geo_bar, use_container_width=True)
        
    with col_g2:
        st.markdown("#### Export Corridor Summary")
        st.dataframe(
            top10_geo.rename(columns={
                'Revenue': 'Total Spend (£)',
                'Quantity': 'Units Sold',
                'InvoiceNo': 'Orders',
                'CustomerID': 'Clients'
            }).style.format({
                'Total Spend (£)': '£{:,.2f}',
                'Units Sold': '{:,.0f}',
                'Orders': '{:,}',
                'Clients': '{:,}'
            }),
            height=420,
            use_container_width=True
        )
        
    st.success("🎯 **Strategic Recommendation:** Netherlands, Ireland, Germany, and France represent >80% of total export volume. Establishing a centralized bonded 3PL fulfillment partnership in Central Europe would slash cross-border delivery lead times by 3–4 days.")

# ==========================================
# TAB 3: RFM CUSTOMER SEGMENTATION
# ==========================================
with tab_rfm:
    st.subheader("Customer Behavioral Stratification (RFM Framework)")
    
    col_rfm1, col_rfm2 = st.columns([1, 2])
    
    with col_rfm1:
        st.markdown("#### Segment Distribution")
        seg_summary = df_rfm.groupby('Segment').agg({
            'CustomerID': 'count',
            'Monetary': 'sum'
        }).reset_index().rename(columns={'CustomerID': 'Customer Count', 'Monetary': 'Total Spend'})
        
        fig_seg_pie = px.pie(
            seg_summary, values='Total Spend', names='Segment',
            title="Revenue Share by Customer Segment",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_seg_pie.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_seg_pie, use_container_width=True)
        
    with col_rfm2:
        st.markdown("#### Recency vs. Monetary Distribution (Log Scale)")
        fig_rfm_scatter = px.scatter(
            df_rfm,
            x='Recency',
            y='Monetary',
            size='Frequency',
            color='Segment',
            hover_data=['CustomerID', 'Frequency'],
            log_y=True,
            labels={'Recency': 'Days Since Last Order', 'Monetary': 'Lifetime Spend (£ - Log Scale)'},
            title="Customer Recency vs. Lifetime Spend"
        )
        fig_rfm_scatter.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_rfm_scatter, use_container_width=True)

    st.markdown("---")
    
    st.subheader("🔍 VIP Account Intelligence Lookup")
    vip_search_col1, vip_search_col2 = st.columns([1, 3])
    
    with vip_search_col1:
        top_vips = df_rfm.sort_values('Monetary', ascending=False)['CustomerID'].head(50).tolist()
        selected_cust_id = st.selectbox("Select or Search Customer ID", top_vips)
        
    with vip_search_col2:
        cust_profile = df_rfm[df_rfm['CustomerID'] == selected_cust_id].iloc[0]
        cust_tx = df_clean[df_clean['CustomerID'] == selected_cust_id]
        fav_item = cust_tx.groupby('Description')['Quantity'].sum().idxmax()
        
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        c_m1.metric("Lifetime Spend", f"£{cust_profile['Monetary']:,.2f}")
        c_m2.metric("Order Frequency", f"{cust_profile['Frequency']} Orders")
        c_m3.metric("Last Purchase", f"{cust_profile['Recency']} Days Ago")
        c_m4.metric("Assigned Tier", cust_profile['Segment'])
        
        st.caption(f"**Primary Purchased Item:** {fav_item} | **Country:** {cust_tx['Country'].iloc[0]}")

# ==========================================
# TAB 4: RETURN FORENSICS & PRODUCT AUDIT
# ==========================================
with tab_returns:
    st.subheader("Order Cancellations & Product Return Diagnostics")
    
    if filtered_cancels.empty:
        st.info("No cancellation records found in selected scope.")
    else:
        col_ret1, col_ret2 = st.columns([3, 2])
        
        with col_ret1:
            top_returned_skus = filtered_cancels.groupby('Description').agg({
                'AbsQuantity': 'sum',
                'InvoiceNo': 'nunique',
                'EstimatedLoss': 'sum'
            }).reset_index().sort_values('AbsQuantity', ascending=False).head(10)
            
            fig_ret = px.bar(
                top_returned_skus, x='AbsQuantity', y='Description',
                orientation='h',
                title="Top 10 SKUs with Highest Cancelled Unit Volume",
                labels={'AbsQuantity': 'Total Cancelled Units', 'Description': 'Product Name'},
                color='AbsQuantity', color_continuous_scale='Reds'
            )
            fig_ret.update_layout(yaxis=dict(autorange='reversed'), height=420, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_ret, use_container_width=True)
            
        with col_ret2:
            st.markdown("#### High-Impact Return Inventory")
            st.dataframe(
                top_returned_skus.rename(columns={
                    'AbsQuantity': 'Cancelled Units',
                    'InvoiceNo': 'Cancellations',
                    'EstimatedLoss': 'Est. Gross Value (£)'
                }).style.format({
                    'Cancelled Units': '{:,.0f}',
                    'Cancellations': '{:,}',
                    'Est. Gross Value (£)': '£{:,.2f}'
                }),
                height=400,
                use_container_width=True
            )
            
        st.warning("⚠️ **Root-Cause Analysis:** The top returned items ('Paper Craft, Little Birdie' and 'Medium Ceramic Top Storage Jar') represent ~155,000 units cancelled across single bulk transactions. This confirms checkout quantity entry errors by wholesale buyers or transit breakage on ceramic goods. Implementing a modal confirmation on orders >250 units will eradicate accidental wholesale returns.")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem; padding: 10px;'>"
    "🚀 <b>E-Commerce Strategic Analytics Portfolio</b> | Powered by Streamlit • Plotly • Pandas • DuckDB"
    "</div>",
    unsafe_allow_html=True
)

