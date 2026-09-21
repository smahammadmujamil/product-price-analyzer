"""Streamlit dashboard for Product Price Analyzer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.charts import historical_price_figure, platform_bar_figure
from src.pipeline import analyze_group, run_search

# Modern Streamlit compatibility: use width='stretch' to avoid deprecation warnings
stretch_kwargs = {"width": "stretch"}

st.set_page_config(
    page_title="PricePulse • Multi-Marketplace Price Analyzer",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich aesthetics and modern typography
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

      html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      }

      .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 1280px;
      }

      /* Hero Banner */
      .hero-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #1d4ed8 100%);
        color: white;
        padding: 1.8rem 2.2rem;
        border-radius: 20px;
        margin-bottom: 1.4rem;
        box-shadow: 0 10px 30px -10px rgba(15, 23, 42, 0.4);
        position: relative;
        overflow: hidden;
      }
      .hero-card::after {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
      }
      .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin: 0 0 0.4rem 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
      }
      .hero-subtitle {
        font-size: 1rem;
        color: #cbd5e1;
        margin: 0 0 0.9rem 0;
        max-width: 700px;
        line-height: 1.5;
      }
      .badge-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
      .pill-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        color: #f1f5f9;
        border: 1px solid rgba(255, 255, 255, 0.15);
      }

      /* KPI Cards */
      .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.2rem;
      }
      .kpi-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 2px 8px -2px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
      }
      .kpi-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px -4px rgba(0, 0, 0, 0.08);
      }
      .kpi-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 0.35rem;
      }
      .kpi-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
      }
      .kpi-sub {
        font-size: 0.8rem;
        color: #059669;
        font-weight: 600;
        margin-top: 0.25rem;
      }

      /* Decision Card */
      .decision-card {
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.4rem;
        border: 1px solid transparent;
      }
      .decision-buy {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-color: #86efac;
        color: #14532d;
      }
      .decision-wait {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-color: #fcd34d;
        color: #78350f;
      }
      .decision-info {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border-color: #93c5fd;
        color: #1e3a8a;
      }
      .decision-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
      .decision-list {
        margin: 0;
        padding-left: 1.3rem;
        font-size: 0.9rem;
        line-height: 1.6;
      }

      /* Product Mini-Cards */
      .store-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin-bottom: 1.4rem;
      }
      .store-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
      }
      .store-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
      }
      .badge-amazon {
        background: #fff7ed;
        color: #c2410c;
        border: 1px solid #ffedd5;
        font-weight: 700;
        padding: 0.2rem 0.65rem;
        border-radius: 8px;
        font-size: 0.8rem;
      }
      .badge-flipkart {
        background: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #dbeafe;
        font-weight: 700;
        padding: 0.2rem 0.65rem;
        border-radius: 8px;
        font-size: 0.8rem;
      }
      .price-big {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
      }
      .mrp-cut {
        font-size: 0.95rem;
        color: #94a3b8;
        text-decoration: line-through;
        margin-left: 0.5rem;
      }
      .discount-tag {
        font-size: 0.8rem;
        font-weight: 700;
        color: #16a34a;
        background: #dcfce7;
        padding: 0.15rem 0.45rem;
        border-radius: 6px;
        margin-left: 0.5rem;
      }

      /* Origin Banner */
      .origin-banner-synthetic {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #475569;
        padding: 0.6rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0 1rem 0;
        font-size: 0.82rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .chart-container {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 2px 8px -2px rgba(0, 0, 0, 0.04);
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_inr(value: float | None) -> str:
    if value is None:
        return "—"
    return f"₹{value:,.2f}"


def origin_banner(origin: str) -> None:
    if origin == "synthetic":
        st.markdown(
            '<div class="origin-banner-synthetic">'
            "<span>🧪</span>"
            "<div><strong>Demo Mode:</strong> Displaying deterministic synthetic catalog records for demonstration. "
            "Marketplace brand names are used for structural layout; data does not reflect real-time live scrapers.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    elif origin == "mixed":
        st.warning("Mixed observations: contains both synthetic catalog rows and permitted live responses.")
    else:
        st.info("Live data: observations gathered through permitted public access channels.")


def render_analysis(analysis: dict) -> None:
    origin_banner(analysis.get("data_origin", "synthetic"))
    comparison = analysis.get("comparison", {})
    latest = pd.DataFrame(analysis.get("latest", []))
    rec = analysis.get("recommendation", {})
    stats = analysis.get("stats_by_platform", {})

    cheapest_plat = comparison.get("cheapest_platform") or "—"
    cheapest_pr = comparison.get("cheapest_price")
    diff = comparison.get("amazon_minus_flipkart")
    pct_diff = comparison.get("percentage_difference_vs_mean")

    # 4 Quick KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="kpi-box">
              <div class="kpi-label">Best Available Price</div>
              <div class="kpi-value">{format_inr(cheapest_pr)}</div>
              <div class="kpi-sub">on {cheapest_plat}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        diff_label = "Amazon − Flipkart"
        diff_val = format_inr(diff) if diff is not None else "—"
        sub_text = "Flipkart cheaper" if diff and diff > 0 else ("Amazon cheaper" if diff and diff < 0 else "Equal pricing")
        st.markdown(
            f"""
            <div class="kpi-box">
              <div class="kpi-label">{diff_label}</div>
              <div class="kpi-value">{diff_val}</div>
              <div class="kpi-sub" style="color: #6366f1;">{sub_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        pct_val = f"{pct_diff:.2f}%" if pct_diff is not None else "—"
        st.markdown(
            f"""
            <div class="kpi-box">
              <div class="kpi-label">Spread vs Mean</div>
              <div class="kpi-value">{pct_val}</div>
              <div class="kpi-sub" style="color: #64748b;">Cross-platform delta</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        platforms_tracked = comparison.get("platform_count", len(latest))
        st.markdown(
            f"""
            <div class="kpi-box">
              <div class="kpi-label">Marketplaces Tracked</div>
              <div class="kpi-value">{platforms_tracked} Stores</div>
              <div class="kpi-sub" style="color: #059669;">Verified Active</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

    # Smart Decision Card
    action = rec.get("action", "Notice")
    headline = rec.get("headline", "")
    card_class = "decision-buy" if action in {"Buy now", "Buy on cheapest platform"} else ("decision-wait" if action == "Wait" else "decision-info")
    icon = "⚡" if action == "Buy now" else ("⏳" if action == "Wait" else "🛍️")

    reasons_html = "".join([f"<li>{r}</li>" for r in rec.get("reasons", [])])
    st.markdown(
        f"""
        <div class="decision-card {card_class}">
          <div class="decision-header">{icon} {action}: {headline}</div>
          <ul class="decision-list">{reasons_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if latest.empty:
        st.info("No current observations found for this product group.")
        return

    # Visual Store Cards
    st.subheader("Marketplace Overview")
    cols = st.columns(len(latest))
    for idx, (_, row) in enumerate(latest.iterrows()):
        platform = row.get("platform", "Unknown")
        badge_class = "badge-amazon" if platform.lower() == "amazon" else "badge-flipkart"
        price_str = format_inr(row.get("price"))
        mrp = row.get("mrp")
        mrp_html = f'<span class="mrp-cut">{format_inr(mrp)}</span>' if mrp and mrp > row.get("price", 0) else ""
        disc = row.get("discount_percentage")
        disc_html = f'<span class="discount-tag">{disc:.0f}% OFF</span>' if disc else ""
        rating = row.get("rating")
        rating_str = f"⭐ {rating:.1f}/5.0" if rating else "No rating"
        reviews = row.get("review_count")
        reviews_str = f"({reviews:,} reviews)" if reviews else ""
        seller = row.get("seller") or "Official Store"
        stock = row.get("availability") or "In Stock"
        url = row.get("product_url", "#")

        with cols[idx]:
            st.markdown(
                f"""
                <div class="store-card">
                  <div>
                    <div class="store-header">
                      <span class="{badge_class}">{platform}</span>
                      <span style="font-size: 0.8rem; font-weight: 600; color: #16a34a;">● {stock}</span>
                    </div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #1e293b; margin-bottom: 0.4rem; min-height: 2.4rem;">
                      {row.get("product_name", "")}
                    </div>
                    <div style="margin-bottom: 0.6rem;">
                      <span class="price-big">{price_str}</span>
                      {mrp_html}
                      {disc_html}
                    </div>
                    <div style="font-size: 0.82rem; color: #64748b; margin-bottom: 0.4rem;">
                      {rating_str} <span style="opacity: 0.7;">{reviews_str}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #475569;">
                      Sold by: <strong>{seller}</strong>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.link_button(f"Visit {platform} Listing ↗", url, **stretch_kwargs)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Interactive Charts
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(platform_bar_figure(latest), **stretch_kwargs)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(historical_price_figure(analysis.get("history_frame", pd.DataFrame())), **stretch_kwargs)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    # Tabs for detailed tables and formulas
    t1, t2, t3 = st.tabs(["📋 Detailed Comparison Table", "📈 Historical Analytics", "📐 Methodology & Formulas"])

    with t1:
        display = latest.copy()
        display["origin"] = display["data_origin"].map(
            {"synthetic": "Synthetic Demo", "live": "Live Access"}
        ).fillna(display["data_origin"])

        column_order = [
            "platform",
            "product_name",
            "price",
            "mrp",
            "discount_percentage",
            "rating",
            "review_count",
            "seller",
            "availability",
            "origin",
            "product_url",
        ]
        for col in column_order:
            if col not in display.columns:
                display[col] = None
        display = display[column_order]

        st.dataframe(
            display,
            hide_index=True,
            column_config={
                "platform": st.column_config.TextColumn("Platform", width="small"),
                "product_name": st.column_config.TextColumn("Product Name", width="medium"),
                "price": st.column_config.NumberColumn("Current Price", format="₹%,.2f"),
                "mrp": st.column_config.NumberColumn("Original Price (MRP)", format="₹%,.2f"),
                "discount_percentage": st.column_config.ProgressColumn(
                    "Discount", min_value=0, max_value=100, format="%d%%"
                ),
                "rating": st.column_config.NumberColumn("Rating", format="⭐ %.1f"),
                "review_count": st.column_config.NumberColumn("Reviews", format="%,d"),
                "seller": st.column_config.TextColumn("Seller"),
                "availability": st.column_config.TextColumn("Status"),
                "origin": st.column_config.TextColumn("Source"),
                "product_url": st.column_config.LinkColumn("Product Link", display_text="Open Listing ↗"),
            },
            **stretch_kwargs,
        )

    with t2:
        stat_rows = []
        for platform, values in stats.items():
            stat_rows.append(
                {
                    "Platform": platform,
                    "Current": values.get("current_price"),
                    "Tracked Low": values.get("min_historical_price"),
                    "Tracked High": values.get("max_historical_price"),
                    "Average": values.get("average_historical_price"),
                    "Price Change": values.get("price_change"),
                    "Change %": values.get("price_change_percentage"),
                    "Volatility (CV)": values.get("price_volatility"),
                    "Data Points": values.get("observation_count"),
                }
            )
        st.dataframe(
            pd.DataFrame(stat_rows),
            hide_index=True,
            column_config={
                "Platform": st.column_config.TextColumn("Platform"),
                "Current": st.column_config.NumberColumn("Current Price", format="₹%,.2f"),
                "Tracked Low": st.column_config.NumberColumn("Tracked Low", format="₹%,.2f"),
                "Tracked High": st.column_config.NumberColumn("Tracked High", format="₹%,.2f"),
                "Average": st.column_config.NumberColumn("Average", format="₹%,.2f"),
                "Price Change": st.column_config.NumberColumn("Price Change", format="₹%,.2f"),
                "Change %": st.column_config.NumberColumn("Change %", format="%.2f%%"),
                "Volatility (CV)": st.column_config.NumberColumn("Volatility (CV)", format="%.4f"),
                "Data Points": st.column_config.NumberColumn("Data Points", format="%d"),
            },
            **stretch_kwargs,
        )

    with t3:
        st.markdown(
            """
#### Quantitative Formulas

- **Absolute Price Delta:** $\\text{Amazon Price} - \\text{Flipkart Price}$  
  *(Positive indicates Amazon is more expensive)*
- **Percentage Spread:** $\\frac{\\text{Amazon} - \\text{Flipkart}}{(\\text{Amazon} + \\text{Flipkart}) / 2} \\times 100$
- **Discount Percentage:** $\\frac{\\text{MRP} - \\text{Current Price}}{\\text{MRP}} \\times 100$
- **Coefficient of Variation (Volatility):** $\\frac{\\sigma}{\\mu}$ (Sample standard deviation divided by mean)

#### Ethical Web Compliance Notice
This application adheres to strict data retrieval standards:
1. `robots.txt` compliance is evaluated and cached per domain before requests.
2. Rate limits and intentional request back-offs are maintained.
3. No CAPTCHA bypassing, session hijacking, or anti-bot circumvention is practiced.
            """
        )


def main() -> None:
    st.markdown(
        """
        <div class="hero-card">
          <div class="hero-title">🛒 PricePulse Analyzer</div>
          <div class="hero-subtitle">
            Real-time cross-platform price comparison, historical analytics, and automated buying recommendations.
          </div>
          <div class="badge-strip">
            <span class="pill-badge">⚡ Real-time Comparison</span>
            <span class="pill-badge">📊 Historical Tracking</span>
            <span class="pill-badge">🛡️ Robots.txt Compliant</span>
            <span class="pill-badge">🇮🇳 INR Currency Standardized</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Search & Filters")
        data_source = st.radio(
            "Data Source",
            options=["mock", "live"],
            format_func=lambda value: "🧪 Demo (Synthetic Catalog)" if value == "mock" else "🌐 Live Attempt (Permitted Access)",
            index=0,
            help="Demo mode guarantees instant, clean comparative data. Live mode respects robots.txt and public limits.",
        )

        st.markdown("#### Quick Catalog Picks")
        quick_picks = [
            "Sony WH-1000XM5",
            "iPhone 15",
            "Galaxy S24",
            "Nike Air Max 270",
            "Apple iPad",
            "Kindle Paperwhite",
        ]
        cols_q = st.columns(2)
        for i, q in enumerate(quick_picks):
            with cols_q[i % 2]:
                if st.button(q, key=f"quick_{i}", **stretch_kwargs):
                    st.session_state["query_input"] = q
                    st.session_state["trigger_search"] = True

        default_query = st.session_state.get("query_input", "Sony WH-1000XM5")
        query = st.text_input(
            "Product Name or URL",
            value=default_query,
            placeholder="e.g. Sony WH-1000XM5 or paste URL",
        )
        submitted = st.button("🔍 Analyze Prices", type="primary", **stretch_kwargs)

        st.markdown("---")
        st.markdown(
            "<div style='font-size: 0.8rem; color: #64748b; line-height: 1.4;'>"
            "<strong>Ethics & API Note:</strong> HTML requests are politely delayed and rate-limited. "
            "Partner APIs (Amazon PA-API / Flipkart Affiliate) can be integrated via <code>.env</code>."
            "</div>",
            unsafe_allow_html=True,
        )

    # Check if a search should execute
    execute_search = submitted or st.session_state.get("trigger_search", False)
    if "trigger_search" in st.session_state:
        del st.session_state["trigger_search"]

    # If first load and no search yet, run default search so page isn't empty
    if "last_result" not in st.session_state and not execute_search:
        execute_search = True
        query = "Sony WH-1000XM5"

    if execute_search:
        cleaned_query = query.strip()
        if not cleaned_query:
            st.warning("Please enter a product name or product URL.")
            return

        with st.spinner("Collecting marketplace listings and computing metrics..."):
            result = run_search(cleaned_query, data_source=data_source)
        st.session_state["last_result"] = result

    result = st.session_state.get("last_result")
    if not result:
        st.info("Enter a product query or click a quick pick from the sidebar.")
        return

    if result.get("message"):
        st.warning(result["message"])
        if data_source == "live":
            st.info("Marketplaces often challenge direct headless requests. Switch to Demo mode to explore full features.")
        return

    if not result.get("analysis"):
        st.warning("No analysis could be generated for this search.")
        return

    groups = result.get("groups") or []
    current_key = result["analysis"].get("group_key")
    if len(groups) > 1:
        default_index = groups.index(current_key) if current_key in groups else 0
        selected_group = st.selectbox("Matched Product Family", groups, index=default_index)
        if selected_group != current_key:
            result["analysis"] = analyze_group(selected_group)

    render_analysis(result["analysis"])


if __name__ == "__main__":
    main()
