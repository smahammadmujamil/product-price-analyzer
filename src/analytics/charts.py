"""Plotly figures for the dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PLATFORM_COLORS = {
    "Amazon": "#FF9900",
    "Flipkart": "#2874F0",
    "Mock": "#6366F1",
    "Croma": "#00E0D0",
    "Reliance Digital": "#E42529",
}


def historical_price_figure(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        fig = go.Figure()
        fig.update_layout(
            title={"text": "No historical observations yet", "font": {"size": 14}},
            template="plotly_white",
            height=360,
        )
        return fig

    fig = px.line(
        frame,
        x="recorded_at",
        y="price",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        markers=True,
        labels={"recorded_at": "Date", "price": "Price", "platform": "Platform"},
    )
    fig.update_traces(
        line={"width": 3},
        marker={"size": 8, "line": {"width": 1.5, "color": "white"}},
        hovertemplate="<b>%{data.name}</b><br>Price: ₹%{y:,.2f}<br>Date: %{x|%b %d, %Y}<extra></extra>",
    )
    fig.update_layout(
        title={
            "text": "<b>Price History Comparison</b>",
            "font": {"size": 15, "color": "#0f172a"},
        },
        template="plotly_white",
        height=380,
        margin={"l": 40, "r": 20, "t": 40, "b": 30},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "title": {"text": ""},
        },
        xaxis={
            "showgrid": True,
            "gridcolor": "#f1f5f9",
            "linecolor": "#cbd5e1",
        },
        yaxis={
            "showgrid": True,
            "gridcolor": "#f1f5f9",
            "linecolor": "#cbd5e1",
            "tickprefix": "₹",
            "tickformat": ",.0f",
        },
    )
    return fig


def platform_bar_figure(latest: pd.DataFrame) -> go.Figure:
    if latest.empty:
        fig = go.Figure()
        fig.update_layout(
            title={"text": "No current prices", "font": {"size": 14}},
            template="plotly_white",
            height=360,
        )
        return fig

    fig = px.bar(
        latest,
        x="platform",
        y="price",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        text="price",
        labels={"platform": "Marketplace", "price": "Price"},
    )
    fig.update_traces(
        texttemplate="<b>₹%{text:,.0f}</b>",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Price: ₹%{y:,.2f}<extra></extra>",
        marker={"line": {"width": 1, "color": "#cbd5e1"}},
        width=0.45,
    )
    fig.update_layout(
        title={
            "text": "<b>Current Price by Marketplace</b>",
            "font": {"size": 15, "color": "#0f172a"},
        },
        template="plotly_white",
        height=380,
        margin={"l": 40, "r": 20, "t": 40, "b": 30},
        showlegend=False,
        xaxis={
            "linecolor": "#cbd5e1",
            "title": {"text": ""},
        },
        yaxis={
            "showgrid": True,
            "gridcolor": "#f1f5f9",
            "linecolor": "#cbd5e1",
            "tickprefix": "₹",
            "tickformat": ",.0f",
        },
    )
    return fig
