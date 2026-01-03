// Activity structure from Dataroma
export interface Activity {
  action: 'Buy' | 'Add' | 'Sell' | 'Reduce' | 'Hold' | 'New';
  percentage: number | null;
}

// Individual investor entry
export interface Investor {
  name: string;
  fund_id: string;
  portfolio_pct: number | null;
  shares: number | null;
  activity: Activity;
  activity_raw: string;
  source_url: string;
}

// Substack mention entry
export interface SubstackMention {
  publication: string;
  article_title: string;
  article_url: string;
  thesis: string;
  published_date: string | null;
}

// Dataroma data for a stock
export interface DataromaData {
  investors: Investor[];
}

// Substack data for a stock
export interface SubstackData {
  mentions: SubstackMention[];
}

// Fundamentals from yfinance
export interface Fundamentals {
  pe_ratio: number | string;
  forward_pe: number | string;
  pb_ratio: number | string;
  peg_ratio: number | string;
  week_52_high: number | string;
  week_52_low: number | string;
  pct_above_52w_low: number | string;
  pct_below_52w_high: number | string;
  current_price: number | string;
  previous_close: number | string;
  total_cash: number | string;
  total_debt: number | string;
  long_term_debt: number | string;
  net_debt: number | string;
  market_cap: number | string;
  insider_pct: number | string;
  institutional_pct: number | string;
  sector: string;
  industry: string;
  country: string;
  currency: string;
  exchange: string;
  is_international: boolean;
}

// Main stock entry
export interface Stock {
  ticker: string;
  company_name: string;
  sources: ('Dataroma' | 'Substack')[];
  dataroma_data: DataromaData;
  substack_data: SubstackData;
  fundamentals: Fundamentals;
  stockanalysis_link: string;
  is_etf: boolean;
  thesis: string | null;
  aggregate_activity: string;
  investor_count: number;
  mention_count: number;
}

// Stats from the data file
export interface Stats {
  dataroma_stocks: number;
  substack_stocks: number;
  both_sources: number;
  dataroma_only: number;
  substack_only: number;
}

// Root data structure
export interface StockData {
  last_updated: string;
  total_stocks: number;
  stats: Stats;
  stocks: Stock[];
}

// Column definition for the table
export interface ColumnConfig {
  id: string;
  label: string;
  visible: boolean;
  group: 'basic' | 'valuation' | 'quality' | 'income' | 'other';
}

// Default columns configuration
export const DEFAULT_COLUMNS: ColumnConfig[] = [
  { id: 'ticker', label: 'Ticker', visible: true, group: 'basic' },
  { id: 'company_name', label: 'Company', visible: true, group: 'basic' },
  { id: 'pe_ratio', label: 'PE Ratio', visible: true, group: 'valuation' },
  { id: 'pb_ratio', label: 'PB Ratio', visible: true, group: 'valuation' },
  { id: 'week_52_low', label: '52W Low', visible: true, group: 'valuation' },
  { id: 'week_52_high', label: '52W High', visible: true, group: 'valuation' },
  { id: 'pct_above_52w_low', label: '% Above Low', visible: true, group: 'valuation' },
  { id: 'pct_below_52w_high', label: '% Below High', visible: true, group: 'valuation' },
  { id: 'sources', label: 'Sources', visible: true, group: 'basic' },
  { id: 'investors', label: 'Investors', visible: true, group: 'basic' },
  { id: 'activity', label: 'Activity', visible: true, group: 'basic' },
  // Additional columns (hidden by default)
  { id: 'market_cap', label: 'Market Cap', visible: false, group: 'valuation' },
  { id: 'peg_ratio', label: 'PEG', visible: false, group: 'valuation' },
  { id: 'forward_pe', label: 'Fwd PE', visible: false, group: 'valuation' },
  { id: 'total_cash', label: 'Cash', visible: false, group: 'valuation' },
  { id: 'total_debt', label: 'Total Debt', visible: false, group: 'valuation' },
  { id: 'net_debt', label: 'Net Debt', visible: false, group: 'valuation' },
  { id: 'insider_pct', label: 'Insider %', visible: false, group: 'other' },
  { id: 'institutional_pct', label: 'Inst %', visible: false, group: 'other' },
  { id: 'sector', label: 'Sector', visible: false, group: 'basic' },
  { id: 'industry', label: 'Industry', visible: false, group: 'basic' },
  { id: 'current_price', label: 'Price', visible: false, group: 'valuation' },
  { id: 'is_etf', label: 'ETF', visible: false, group: 'basic' },
  { id: 'thesis', label: 'Thesis', visible: false, group: 'basic' },
  { id: 'link', label: 'Link', visible: true, group: 'basic' },
];
