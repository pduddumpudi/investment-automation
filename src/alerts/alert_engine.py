"""
Alert engine for evaluating price moves and cross-source confirmations.
Supports configurable rules from Google Sheets.
"""
import os
import re
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    from src.utils.logger import setup_logger
    from src.utils.sheets_reader import SheetsReader
except ModuleNotFoundError:
    from utils.logger import setup_logger
    try:
        from utils.sheets_reader import SheetsReader
    except ModuleNotFoundError:
        SheetsReader = None

logger = setup_logger(__name__)


class AlertEngine:
    """Evaluate alert conditions and generate alerts."""

    def __init__(self, price_threshold: float = 10.0):
        """
        Initialize the alert engine.

        Args:
            price_threshold: Default percentage threshold for price alerts (default 10%)
        """
        self.price_threshold = price_threshold
        self.alerts = []

    def evaluate_price_alerts(self, stocks: List[Dict]) -> List[Dict]:
        """
        Evaluate price move alerts for all stocks.
        Compares current_price vs previous_close.

        Args:
            stocks: List of stock dictionaries with fundamentals

        Returns:
            List of alert dictionaries for stocks with significant moves
        """
        alerts = []

        for stock in stocks:
            ticker = stock.get('ticker', '')
            fundamentals = stock.get('fundamentals', {})

            current_price = fundamentals.get('current_price')
            previous_close = fundamentals.get('previous_close')

            # Skip if missing data or N/A values
            if not current_price or not previous_close:
                continue
            if current_price == 'N/A' or previous_close == 'N/A':
                continue

            try:
                current_price = float(current_price)
                previous_close = float(previous_close)
            except (ValueError, TypeError):
                continue

            if previous_close == 0:
                continue

            # Calculate percentage change
            pct_change = ((current_price - previous_close) / previous_close) * 100
            pct_change = round(pct_change, 2)

            # Check if exceeds threshold
            if abs(pct_change) >= self.price_threshold:
                direction = "up" if pct_change > 0 else "down"
                alert = {
                    'type': 'price_move',
                    'ticker': ticker,
                    'company_name': stock.get('company_name', ticker),
                    'pct_change': pct_change,
                    'direction': direction,
                    'current_price': current_price,
                    'previous_close': previous_close,
                    'sources': stock.get('sources', []),
                    'stockanalysis_link': stock.get('stockanalysis_link', ''),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                alerts.append(alert)
                logger.info(f"Price alert: {ticker} moved {pct_change:+.2f}%")

        logger.info(f"Found {len(alerts)} price move alerts (threshold: {self.price_threshold}%)")
        return alerts

    def evaluate_cross_source_alerts(self, stocks: List[Dict],
                                      min_dataroma: int = 2,
                                      min_substack: int = 1) -> List[Dict]:
        """
        Evaluate cross-source confirmation alerts.
        Finds stocks that appear in multiple sources.

        Args:
            stocks: List of stock dictionaries
            min_dataroma: Minimum Dataroma investor count
            min_substack: Minimum Substack mention count

        Returns:
            List of alert dictionaries for cross-source confirmations
        """
        alerts = []

        for stock in stocks:
            ticker = stock.get('ticker', '')
            sources = stock.get('sources', [])
            investor_count = stock.get('investor_count', 0)
            mention_count = stock.get('mention_count', 0)

            # Check if meets cross-source criteria
            has_dataroma = 'Dataroma' in sources and investor_count >= min_dataroma
            has_substack = 'Substack' in sources and mention_count >= min_substack

            if has_dataroma and has_substack:
                # Get investor names
                investors = stock.get('dataroma_data', {}).get('investors', [])
                investor_names = [inv.get('name', '') for inv in investors[:5]]

                # Get Substack mentions
                mentions = stock.get('substack_data', {}).get('mentions', [])
                publications = list(set([m.get('publication', '') for m in mentions[:5]]))

                alert = {
                    'type': 'cross_source',
                    'ticker': ticker,
                    'company_name': stock.get('company_name', ticker),
                    'sources': sources,
                    'investor_count': investor_count,
                    'mention_count': mention_count,
                    'investors': investor_names,
                    'publications': publications,
                    'stockanalysis_link': stock.get('stockanalysis_link', ''),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                alerts.append(alert)
                logger.info(f"Cross-source alert: {ticker} ({investor_count} investors, {mention_count} mentions)")

        logger.info(f"Found {len(alerts)} cross-source alerts")
        return alerts

    def evaluate_custom_rule(self, stock: Dict, condition: str) -> bool:
        """
        Evaluate a custom alert rule condition.
        Supports simple conditions like: dataroma_count>=2 AND substack_count>=1

        Args:
            stock: Stock dictionary
            condition: Condition string (Google Sheets formula-like)

        Returns:
            True if condition is met
        """
        if not condition:
            return False

        # Clean up condition string
        condition = condition.strip()
        if condition.startswith('='):
            condition = condition[1:]

        # Replace variable names with actual values
        investor_count = stock.get('investor_count', 0)
        mention_count = stock.get('mention_count', 0)
        sources = stock.get('sources', [])
        fundamentals = stock.get('fundamentals', {})

        # Build variable mapping
        variables = {
            'dataroma_count': investor_count,
            'investor_count': investor_count,
            'substack_count': mention_count,
            'mention_count': mention_count,
            'has_dataroma': 1 if 'Dataroma' in sources else 0,
            'has_substack': 1 if 'Substack' in sources else 0,
            'pe_ratio': self._safe_float(fundamentals.get('pe_ratio')),
            'pct_above_52w_low': self._safe_float(fundamentals.get('pct_above_52w_low')),
            'pct_below_52w_high': self._safe_float(fundamentals.get('pct_below_52w_high')),
        }

        try:
            # Replace variable names with values
            eval_condition = condition
            for var_name, var_value in variables.items():
                eval_condition = re.sub(
                    rf'\b{var_name}\b',
                    str(var_value) if var_value is not None else '0',
                    eval_condition,
                    flags=re.IGNORECASE
                )

            # Replace AND/OR with Python operators
            eval_condition = re.sub(r'\bAND\b', 'and', eval_condition, flags=re.IGNORECASE)
            eval_condition = re.sub(r'\bOR\b', 'or', eval_condition, flags=re.IGNORECASE)

            # Evaluate (with restricted builtins for safety)
            result = eval(eval_condition, {"__builtins__": {}}, {})
            return bool(result)

        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert value to float."""
        if value is None or value == 'N/A':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def evaluate_custom_rules(self, stocks: List[Dict], rules: List[Dict]) -> List[Dict]:
        """
        Evaluate custom alert rules from Google Sheets.

        Args:
            stocks: List of stock dictionaries
            rules: List of rule dictionaries with rule_name, condition, email, enabled

        Returns:
            List of alert dictionaries
        """
        alerts = []
        enabled_rules = [r for r in rules if r.get('enabled', True)]

        logger.info(f"Evaluating {len(enabled_rules)} custom rules")

        for rule in enabled_rules:
            rule_name = rule.get('rule_name', 'Unknown Rule')
            condition = rule.get('condition', '')
            email = rule.get('email', '')

            if not condition:
                continue

            matching_stocks = []
            for stock in stocks:
                if self.evaluate_custom_rule(stock, condition):
                    matching_stocks.append(stock)

            if matching_stocks:
                alert = {
                    'type': 'custom_rule',
                    'rule_name': rule_name,
                    'condition': condition,
                    'email': email,
                    'matching_stocks': [
                        {
                            'ticker': s.get('ticker'),
                            'company_name': s.get('company_name'),
                            'investor_count': s.get('investor_count', 0),
                            'mention_count': s.get('mention_count', 0),
                            'stockanalysis_link': s.get('stockanalysis_link', '')
                        }
                        for s in matching_stocks
                    ],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                alerts.append(alert)
                logger.info(f"Custom rule '{rule_name}' matched {len(matching_stocks)} stocks")

        return alerts

    def evaluate_all(self, stocks: List[Dict],
                     custom_rules: Optional[List[Dict]] = None,
                     settings: Optional[Dict] = None) -> Dict[str, List[Dict]]:
        """
        Evaluate all alert types.

        Args:
            stocks: List of stock dictionaries
            custom_rules: Optional list of custom rule dictionaries
            settings: Optional settings dictionary

        Returns:
            Dictionary with alert types as keys and alert lists as values
        """
        # Get price threshold from settings
        if settings and 'price_alert_threshold' in settings:
            try:
                self.price_threshold = float(settings['price_alert_threshold'])
            except (ValueError, TypeError):
                pass

        results = {
            'price_alerts': self.evaluate_price_alerts(stocks),
            'cross_source_alerts': self.evaluate_cross_source_alerts(stocks),
            'custom_alerts': []
        }

        if custom_rules:
            results['custom_alerts'] = self.evaluate_custom_rules(stocks, custom_rules)

        total_alerts = sum(len(alerts) for alerts in results.values())
        logger.info(f"Total alerts generated: {total_alerts}")

        return results


def evaluate_alerts(stocks: List[Dict],
                    custom_rules: Optional[List[Dict]] = None,
                    settings: Optional[Dict] = None) -> Dict[str, List[Dict]]:
    """
    Convenience function to evaluate all alerts.

    Args:
        stocks: List of stock dictionaries
        custom_rules: Optional list of custom rule dictionaries
        settings: Optional settings dictionary

    Returns:
        Dictionary with alert types and their alerts
    """
    engine = AlertEngine()
    return engine.evaluate_all(stocks, custom_rules, settings)
