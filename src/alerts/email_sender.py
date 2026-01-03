"""
Email sender using Resend API for alert notifications.
"""
import os
from typing import List, Dict, Optional
from datetime import datetime

try:
    from src.utils.logger import setup_logger
except ModuleNotFoundError:
    from utils.logger import setup_logger

logger = setup_logger(__name__)

# Try to import resend, gracefully handle if not installed
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend package not installed. Email alerts will be disabled.")


class EmailSender:
    """Send alert emails using Resend API."""

    def __init__(self, api_key: Optional[str] = None, from_email: Optional[str] = None):
        """
        Initialize the email sender.

        Args:
            api_key: Resend API key (defaults to RESEND_API_KEY env var)
            from_email: From email address (defaults to RESEND_FROM_EMAIL or onboarding@resend.dev)
        """
        self.api_key = api_key or os.getenv('RESEND_API_KEY')
        self.from_email = from_email or os.getenv('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
        self.dashboard_url = os.getenv('DASHBOARD_URL', 'https://your-dashboard-url.github.io')

        if self.api_key and RESEND_AVAILABLE:
            resend.api_key = self.api_key
            self.enabled = True
            logger.info("Email sender initialized with Resend API")
        else:
            self.enabled = False
            if not self.api_key:
                logger.warning("RESEND_API_KEY not set. Email alerts disabled.")

    def _format_price_alerts_html(self, alerts: List[Dict]) -> str:
        """Format price alerts as HTML."""
        if not alerts:
            return ""

        html = """
        <h2 style="color: #333; border-bottom: 2px solid #4CAF50;">📈 Price Move Alerts</h2>
        <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Ticker</th>
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Company</th>
                <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">Change</th>
                <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">Price</th>
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Link</th>
            </tr>
        """

        for alert in alerts:
            pct = alert.get('pct_change', 0)
            color = '#4CAF50' if pct > 0 else '#f44336'
            arrow = '↑' if pct > 0 else '↓'

            html += f"""
            <tr>
                <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">{alert.get('ticker', 'N/A')}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">{alert.get('company_name', 'N/A')}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: right; color: {color}; font-weight: bold;">
                    {arrow} {pct:+.2f}%
                </td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: right;">
                    ${alert.get('current_price', 'N/A'):.2f}
                </td>
                <td style="padding: 12px; border: 1px solid #ddd;">
                    <a href="{alert.get('stockanalysis_link', '#')}" style="color: #2196F3;">View</a>
                </td>
            </tr>
            """

        html += "</table>"
        return html

    def _format_cross_source_alerts_html(self, alerts: List[Dict]) -> str:
        """Format cross-source alerts as HTML."""
        if not alerts:
            return ""

        html = """
        <h2 style="color: #333; border-bottom: 2px solid #2196F3;">🔗 Cross-Source Confirmations</h2>
        <p style="color: #666;">Stocks appearing in both Dataroma (superinvestors) and Substack (analysts):</p>
        <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Ticker</th>
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Company</th>
                <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Investors</th>
                <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Mentions</th>
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Link</th>
            </tr>
        """

        for alert in alerts:
            investors = ', '.join(alert.get('investors', [])[:3])
            if len(alert.get('investors', [])) > 3:
                investors += f" +{len(alert.get('investors', [])) - 3} more"

            html += f"""
            <tr>
                <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">{alert.get('ticker', 'N/A')}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">{alert.get('company_name', 'N/A')}</td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">
                    {alert.get('investor_count', 0)}
                    <br><small style="color: #666;">{investors}</small>
                </td>
                <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">{alert.get('mention_count', 0)}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">
                    <a href="{alert.get('stockanalysis_link', '#')}" style="color: #2196F3;">View</a>
                </td>
            </tr>
            """

        html += "</table>"
        return html

    def _format_custom_alerts_html(self, alerts: List[Dict]) -> str:
        """Format custom rule alerts as HTML."""
        if not alerts:
            return ""

        html = """
        <h2 style="color: #333; border-bottom: 2px solid #FF9800;">⚡ Custom Rule Alerts</h2>
        """

        for alert in alerts:
            rule_name = alert.get('rule_name', 'Custom Rule')
            stocks = alert.get('matching_stocks', [])

            html += f"""
            <h3 style="color: #FF9800; margin-top: 15px;">{rule_name}</h3>
            <p style="color: #666; font-size: 12px;">Condition: {alert.get('condition', 'N/A')}</p>
            <ul style="margin: 10px 0;">
            """

            for stock in stocks[:10]:
                html += f"""
                <li>
                    <strong>{stock.get('ticker', 'N/A')}</strong> - {stock.get('company_name', 'N/A')}
                    ({stock.get('investor_count', 0)} investors, {stock.get('mention_count', 0)} mentions)
                    <a href="{stock.get('stockanalysis_link', '#')}" style="color: #2196F3;">View</a>
                </li>
                """

            if len(stocks) > 10:
                html += f"<li>...and {len(stocks) - 10} more</li>"

            html += "</ul>"

        return html

    def build_alert_email(self, all_alerts: Dict[str, List[Dict]]) -> Dict[str, str]:
        """
        Build email content from all alerts.

        Args:
            all_alerts: Dictionary with alert types and their alerts

        Returns:
            Dictionary with 'subject' and 'html' keys
        """
        price_alerts = all_alerts.get('price_alerts', [])
        cross_source_alerts = all_alerts.get('cross_source_alerts', [])
        custom_alerts = all_alerts.get('custom_alerts', [])

        total_count = len(price_alerts) + len(cross_source_alerts) + len(custom_alerts)

        if total_count == 0:
            return {'subject': '', 'html': ''}

        # Build subject
        parts = []
        if price_alerts:
            parts.append(f"{len(price_alerts)} price moves")
        if cross_source_alerts:
            parts.append(f"{len(cross_source_alerts)} cross-source")
        if custom_alerts:
            parts.append(f"{len(custom_alerts)} custom rules")

        subject = f"📊 Investment Alert: {', '.join(parts)}"

        # Build HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
            <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h1 style="color: #333; margin-bottom: 5px;">Investment Alert Summary</h1>
                <p style="color: #666; margin-top: 0;">{datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}</p>

                {self._format_price_alerts_html(price_alerts)}
                {self._format_cross_source_alerts_html(cross_source_alerts)}
                {self._format_custom_alerts_html(custom_alerts)}

                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

                <p style="text-align: center;">
                    <a href="{self.dashboard_url}" style="display: inline-block; padding: 12px 24px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        View Full Dashboard
                    </a>
                </p>

                <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                    This alert was generated by your Investment Automation tool.
                    <br>Configure alerts in your Google Sheets settings.
                </p>
            </div>
        </body>
        </html>
        """

        return {'subject': subject, 'html': html}

    def send_email(self, to_email: str, subject: str, html: str) -> bool:
        """
        Send an email using Resend API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html: HTML email content

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email sending is disabled (no API key or resend not installed)")
            return False

        if not to_email or not subject or not html:
            logger.warning("Missing required email parameters")
            return False

        try:
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html
            }

            response = resend.Emails.send(params)
            logger.info(f"Email sent successfully to {to_email}: {response.get('id', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_alerts(self, all_alerts: Dict[str, List[Dict]],
                    default_email: Optional[str] = None) -> int:
        """
        Send alert emails for all alerts.

        Args:
            all_alerts: Dictionary with alert types and their alerts
            default_email: Default email address for alerts

        Returns:
            Number of emails sent successfully
        """
        if not self.enabled:
            logger.warning("Email sending is disabled")
            return 0

        # Get default email from env if not provided
        if not default_email:
            default_email = os.getenv('ALERT_EMAIL', os.getenv('DEFAULT_EMAIL'))

        if not default_email:
            logger.warning("No default email configured for alerts")
            return 0

        # Build and send main alert email
        email_content = self.build_alert_email(all_alerts)

        if not email_content['subject']:
            logger.info("No alerts to send")
            return 0

        sent_count = 0

        if self.send_email(default_email, email_content['subject'], email_content['html']):
            sent_count += 1

        # Handle custom alert emails (might have different recipients)
        custom_alerts = all_alerts.get('custom_alerts', [])
        for alert in custom_alerts:
            custom_email = alert.get('email')
            if custom_email and custom_email != default_email:
                # Send individual custom alert
                custom_content = self.build_alert_email({'custom_alerts': [alert]})
                if custom_content['subject'] and self.send_email(
                    custom_email,
                    custom_content['subject'],
                    custom_content['html']
                ):
                    sent_count += 1

        logger.info(f"Sent {sent_count} alert email(s)")
        return sent_count


def send_alert_email(all_alerts: Dict[str, List[Dict]],
                     default_email: Optional[str] = None) -> int:
    """
    Convenience function to send alert emails.

    Args:
        all_alerts: Dictionary with alert types and their alerts
        default_email: Default email address for alerts

    Returns:
        Number of emails sent successfully
    """
    sender = EmailSender()
    return sender.send_alerts(all_alerts, default_email)
