#!/usr/bin/env python3
"""
Daily trading signal email sender.

Replicates the live portfolio tracker (notebooks/live_portfolio_tracker.ipynb)
and sends the rebalancing signal via email.

Requires environment variables:
    SMTP_HOST: SMTP server hostname
    SMTP_PORT: SMTP server port (default 465 for SSL)
    SMTP_USER: SMTP login username (usually your email address)
    SMTP_PASSWORD: SMTP login password (app-specific password)
    EMAIL_TO: Recipient email address
"""

import os
import smtplib
import ssl
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.portfolio_tracker import Portfolio

# ── Portfolio configuration (mirrored from live_portfolio_tracker.ipynb) ──

TRADABLE_ETFS = [
    '510300.SH',  # CSI 300
    '510500.SH',  # CSI 500
    '513500.SH',  # S&P 500
    '511260.SH',  # 10Y Treasury
    '518880.SH',  # Gold
    '513100.SH',  # Nasdaq-100
]

ETF_NAMES = {
    '510300.SH': 'CSI 300',
    '510500.SH': 'CSI 500',
    '513500.SH': 'S&P 500',
    '511260.SH': '10Y Treasury',
    '518880.SH': 'Gold',
    '513100.SH': 'Nasdaq-100',
}


def build_portfolio() -> Portfolio:
    """Build portfolio with the same trades as the live tracker notebook."""
    portfolio = Portfolio(
        tradable_etfs=TRADABLE_ETFS,
        initial_cash=30000,
        commission_rate=0.0003,
        trim_threshold=0.03,
        buy_threshold=0.10,
        lookback=252,
    )

    # Entry trades from 2026-01-30
    portfolio.trade(qty=700,  price=4.681,   side='buy', day='2026-01-30', etf='510300.SH')
    portfolio.trade(qty=300,  price=8.364,   side='buy', day='2026-01-30', etf='510500.SH')
    portfolio.trade(qty=1100, price=2.404,   side='buy', day='2026-01-30', etf='513500.SH')
    portfolio.trade(qty=100,  price=135.096, side='buy', day='2026-01-30', etf='511260.SH')
    portfolio.trade(qty=300,  price=10.686,  side='buy', day='2026-01-30', etf='518880.SH')
    portfolio.trade(qty=1100, price=1.843,   side='buy', day='2026-01-30', etf='513100.SH')

    return portfolio


def format_email_html(portfolio: Portfolio) -> str:
    """Generate HTML email body from portfolio state."""
    signal = portfolio.signal
    positions_df = portfolio.positions
    total_value = portfolio.calc_value()
    pnl_df = portfolio.pnl

    today = datetime.now().strftime('%Y-%m-%d')

    # PnL summary
    if not pnl_df.empty:
        latest_pnl = pnl_df['PnL'].iloc[-1]
        latest_pnl_pct = pnl_df['PnL %'].iloc[-1]
    else:
        latest_pnl = 0
        latest_pnl_pct = 0

    # Determine action banner
    if signal['should_rebalance']:
        banner_color = '#e74c3c'
        banner_text = 'REBALANCING NEEDED'
    else:
        banner_color = '#27ae60'
        banner_text = 'NO ACTION NEEDED'

    # Build positions table rows
    position_rows = ''
    for _, row in positions_df.iterrows():
        etf = row['ETF']
        name = ETF_NAMES.get(etf, etf)
        pnl_color = '#27ae60' if row['Unrealized PnL'] >= 0 else '#e74c3c'
        position_rows += f"""
        <tr>
            <td style="padding:6px 10px">{name}<br><small style="color:#888">{etf}</small></td>
            <td style="padding:6px 10px;text-align:right">{int(row['Shares']):,}</td>
            <td style="padding:6px 10px;text-align:right">{row['Current Price']:.3f}</td>
            <td style="padding:6px 10px;text-align:right">¥{row['Market Value']:,.0f}</td>
            <td style="padding:6px 10px;text-align:right;color:{pnl_color}">
                ¥{row['Unrealized PnL']:+,.0f} ({row['Unrealized PnL %']:+.2f}%)
            </td>
            <td style="padding:6px 10px;text-align:right">{row['Weight %']:.1f}%</td>
        </tr>"""

    # Build weight comparison rows
    weight_rows = ''
    for etf in TRADABLE_ETFS:
        name = ETF_NAMES.get(etf, etf)
        current_w = signal['current_weights'][etf]
        target_w = signal['target_weights'][etf]
        diff = current_w - target_w

        if diff > signal['trim_threshold']:
            action = '<span style="color:#e74c3c;font-weight:bold">TRIM</span>'
        elif diff < -signal['buy_threshold']:
            action = '<span style="color:#27ae60;font-weight:bold">BUY</span>'
        else:
            action = '<span style="color:#888">-</span>'

        diff_color = '#e74c3c' if abs(diff) > 0.03 else '#333'
        weight_rows += f"""
        <tr>
            <td style="padding:4px 10px">{name}</td>
            <td style="padding:4px 10px;text-align:right">{current_w:.1%}</td>
            <td style="padding:4px 10px;text-align:right">{target_w:.1%}</td>
            <td style="padding:4px 10px;text-align:right;color:{diff_color}">{diff:+.1%}</td>
            <td style="padding:4px 10px;text-align:center">{action}</td>
        </tr>"""

    # Build trades section (only if rebalancing needed)
    trades_html = ''
    if signal['should_rebalance'] and signal.get('trades_needed'):
        trade_rows = ''
        for trade in signal['trades_needed']:
            name = ETF_NAMES.get(trade['etf'], trade['etf'])
            action_color = '#27ae60' if trade['action'] == 'BUY' else '#e74c3c'
            trade_value = trade['shares'] * trade['price']
            trade_rows += f"""
            <tr>
                <td style="padding:4px 10px">{name}</td>
                <td style="padding:4px 10px;text-align:center;color:{action_color};font-weight:bold">
                    {trade['action']}
                </td>
                <td style="padding:4px 10px;text-align:right">{trade['shares']:,} shares</td>
                <td style="padding:4px 10px;text-align:right">¥{trade['price']:.3f}</td>
                <td style="padding:4px 10px;text-align:right">¥{trade_value:,.0f}</td>
            </tr>"""

        trades_html = f"""
        <h3 style="color:#e74c3c;margin-top:24px">Required Trades</h3>
        <table style="border-collapse:collapse;width:100%;font-size:14px">
            <tr style="background:#ffeaea">
                <th style="padding:6px 10px;text-align:left">ETF</th>
                <th style="padding:6px 10px;text-align:center">Action</th>
                <th style="padding:6px 10px;text-align:right">Quantity</th>
                <th style="padding:6px 10px;text-align:right">Price</th>
                <th style="padding:6px 10px;text-align:right">Value</th>
            </tr>
            {trade_rows}
        </table>"""

    pnl_color = '#27ae60' if latest_pnl >= 0 else '#e74c3c'

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto">
        <div style="background:{banner_color};color:white;padding:16px;text-align:center;
                    border-radius:8px 8px 0 0;font-size:20px;font-weight:bold">
            {banner_text}
        </div>
        <div style="background:#f8f9fa;padding:16px;border:1px solid #dee2e6">
            <p style="margin:0;color:#555">All Weather v2.1 &mdash; {today}</p>
            <p style="margin:8px 0 0;font-size:18px">
                Portfolio: <strong>¥{total_value:,.0f}</strong>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                PnL: <strong style="color:{pnl_color}">¥{latest_pnl:+,.0f} ({latest_pnl_pct:+.2f}%)</strong>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                Max drift: <strong>{signal['drift']:.2%}</strong>
            </p>
        </div>

        <h3 style="margin-top:24px">Current Positions</h3>
        <table style="border-collapse:collapse;width:100%;font-size:14px">
            <tr style="background:#eee">
                <th style="padding:6px 10px;text-align:left">ETF</th>
                <th style="padding:6px 10px;text-align:right">Shares</th>
                <th style="padding:6px 10px;text-align:right">Price</th>
                <th style="padding:6px 10px;text-align:right">Value</th>
                <th style="padding:6px 10px;text-align:right">PnL</th>
                <th style="padding:6px 10px;text-align:right">Weight</th>
            </tr>
            {position_rows}
            <tr style="background:#eee;font-weight:bold">
                <td style="padding:6px 10px">Cash</td>
                <td colspan="2"></td>
                <td style="padding:6px 10px;text-align:right">¥{portfolio._cash:,.0f}</td>
                <td colspan="2"></td>
            </tr>
        </table>

        <h3 style="margin-top:24px">Weight Analysis</h3>
        <p style="color:#555;font-size:13px">
            Trim threshold: {signal['trim_threshold']:.0%} &nbsp;|&nbsp;
            Buy threshold: {signal['buy_threshold']:.0%}
        </p>
        <table style="border-collapse:collapse;width:100%;font-size:14px">
            <tr style="background:#eee">
                <th style="padding:4px 10px;text-align:left">ETF</th>
                <th style="padding:4px 10px;text-align:right">Current</th>
                <th style="padding:4px 10px;text-align:right">Target</th>
                <th style="padding:4px 10px;text-align:right">Diff</th>
                <th style="padding:4px 10px;text-align:center">Action</th>
            </tr>
            {weight_rows}
        </table>

        {trades_html}

        <p style="margin-top:24px;font-size:12px;color:#999;border-top:1px solid #eee;padding-top:12px">
            Generated by All Weather GitHub Actions &bull;
            Strategy: v2.1 Asymmetric Mean-Reversion + Ledoit-Wolf Shrinkage &bull;
            Thresholds: 3% trim / 10% buy
        </p>
    </div>
    """
    return html


def send_email(subject: str, html_body: str) -> None:
    """Send email via SMTP with SSL."""
    smtp_host = os.environ['SMTP_HOST']
    smtp_port = int(os.environ.get('SMTP_PORT', '465'))
    smtp_user = os.environ['SMTP_USER']
    smtp_password = os.environ['SMTP_PASSWORD']
    email_to = os.environ['EMAIL_TO']

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = email_to
    msg.attach(MIMEText(html_body, 'html'))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, email_to, msg.as_string())

    print(f"Email sent to {email_to}")


def main():
    print("Building portfolio...")
    portfolio = build_portfolio()

    print("Fetching live prices and computing signal...")
    signal = portfolio.signal

    if signal['should_rebalance']:
        action_summary = "REBALANCE NEEDED"
    else:
        action_summary = "No action"

    today = datetime.now().strftime('%Y-%m-%d')
    subject = f"[All Weather] {today} - {action_summary} (drift {signal['drift']:.1%})"

    print(f"Subject: {subject}")

    html_body = format_email_html(portfolio)

    # If SMTP is configured, send email; otherwise just print
    if os.environ.get('SMTP_HOST'):
        send_email(subject, html_body)
    else:
        print("SMTP not configured - printing HTML to stdout")
        print(html_body)


if __name__ == '__main__':
    main()
