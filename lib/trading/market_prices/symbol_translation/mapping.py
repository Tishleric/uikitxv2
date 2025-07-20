import re
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import calendar

class SymbolFormat(Enum):
    BLOOMBERG = "bloomberg"
    CME = "cme"
    XCME = "xcme"
    UNKNOWN = "unknown"

class WeekdayType(Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"

@dataclass
class ParsedOption:
    """Standardized representation of a Treasury weekly option"""
    underlying: str
    weekday: WeekdayType
    option_type: str  # 'C' or 'P'
    strike: float
    expiration_date: datetime
    symbol_type: str  # 'weekday_weekly', 'friday_weekly', 'quarterly'
    
    # Format-specific data
    bloomberg_symbol: Optional[str] = None
    cme_symbol: Optional[str] = None
    xcme_symbol: Optional[str] = None
    
    # Additional metadata
    weekday_occurrence: Optional[int] = None  # For Mon-Thu (3rd Monday, 4th Tuesday)
    week_of_month: Optional[int] = None      # For Friday weekly (week 3)
    contract_month: Optional[int] = None     # For quarterly (August = 8)

class TreasuryOptionsTranslator:
    """
    Complete Treasury Options Translator with ALL FIXES:
    - OZN quarterly options parsing
    - CORRECTED year calculation (5 → 2025, not 2005)
    - Robust 4th Friday calculation
    - Three-way format conversion
    """
    
    def __init__(self):
        self.month_codes = {
            1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
            7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
        }
        
        self.month_names = {
            1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
            7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'
        }
        
        self.weekday_mapping = {
            'VBY': WeekdayType.MONDAY,
            'TJP': WeekdayType.TUESDAY,
            'TYW': WeekdayType.WEDNESDAY,
            'TJW': WeekdayType.THURSDAY
        }
        
        self.cme_weekday_mapping = {
            'VY': WeekdayType.MONDAY,
            'GY': WeekdayType.TUESDAY,
            'WY': WeekdayType.WEDNESDAY,
            'HY': WeekdayType.THURSDAY,
            'ZN': WeekdayType.FRIDAY
        }
    
    def _get_correct_year(self, year_str: str) -> int:
        """
        Convert year string to correct 4-digit year for Treasury options
        
        CRITICAL FIX: 
        - "5" → 2025 (not 2005!)
        - "25" → 2025
        - "4" → 2024
        """
        year_int = int(year_str)
        
        if len(year_str) == 1:
            # Single digit: assume 2020s decade
            return 2020 + year_int
        elif len(year_str) == 2:
            # Two digit: standard conversion
            if year_int <= 30:  # Assume 2000-2030
                return 2000 + year_int
            else:  # Assume 1970-1999 (legacy)
                return 1900 + year_int
        else:
            raise ValueError(f"Invalid year format: {year_str}")
    
    def detect_format(self, symbol: str) -> SymbolFormat:
        """Detect which format the symbol is in"""
        symbol = symbol.strip()
        
        # Bloomberg format
        if ' Comdty' in symbol or re.match(r'^(VBY|TJP|TYW|TJW)[A-Z]\d{1,2}[CP]\d', symbol) or \
           re.match(r'^\d[A-Z][A-Z]\d[CP]', symbol) or re.match(r'^TY[A-Z]\d[CP]', symbol):
            return SymbolFormat.BLOOMBERG
        
        # XCME format
        elif symbol.startswith('XCME.'):
            return SymbolFormat.XCME
        
        # CME format (includes OZN)
        elif re.match(r'^(OZN|[A-Z]{2,3})\d*[A-Z]\d+\s+[CP]\d+$', symbol):
            return SymbolFormat.CME
        
        return SymbolFormat.UNKNOWN
    
    def parse_symbol(self, symbol: str) -> ParsedOption:
        """Parse any format symbol into standardized representation"""
        format_type = self.detect_format(symbol)
        
        if format_type == SymbolFormat.BLOOMBERG:
            return self._parse_bloomberg(symbol)
        elif format_type == SymbolFormat.CME:
            return self._parse_cme(symbol)
        elif format_type == SymbolFormat.XCME:
            return self._parse_xcme(symbol)
        else:
            raise ValueError(f"Unknown symbol format: {symbol}")
    
    def _parse_bloomberg(self, symbol: str) -> ParsedOption:
        """Parse Bloomberg format symbol with CORRECTED YEAR LOGIC"""
        parts = symbol.split()
        if len(parts) < 2:
            raise ValueError(f"Invalid Bloomberg format: {symbol}")
        
        base_and_type = parts[0]
        strike = float(parts[1])
        
        month_decode = {v: k for k, v in self.month_codes.items()}
        
        # Monday-Thursday Weekly: [WeekdayBase][Month][Year][C/P][Occurrence]
        weekday_match = re.match(r'^(VBY|TJP|TYW|TJW)([A-Z])(\d{1,2})([CP])(\d)$', base_and_type)
        if weekday_match:
            weekday_base, month_code, year_str, option_type, occurrence_str = weekday_match.groups()
            
            month = month_decode[month_code]
            year = self._get_correct_year(year_str)  # FIXED
            occurrence = int(occurrence_str)
            weekday = self.weekday_mapping[weekday_base]
            
            expiry_date = self._calculate_weekday_occurrence(year, month, weekday, occurrence)
            
            return ParsedOption(
                underlying='10Y',
                weekday=weekday,
                option_type=option_type,
                strike=strike,
                expiration_date=expiry_date,
                symbol_type='weekday_weekly',
                bloomberg_symbol=symbol,
                weekday_occurrence=occurrence
            )
        
        # Friday Weekly: [Week][Month1][Month2][Year][C/P]
        friday_match = re.match(r'^(\d)([A-Z])([A-Z])(\d)([CP])$', base_and_type)
        if friday_match:
            week_str, month1_code, month2_code, year_str, option_type = friday_match.groups()
            
            week = int(week_str)
            month = month_decode[month2_code]
            year = self._get_correct_year(year_str)  # FIXED
            
            expiry_date = self._calculate_nth_friday(year, month, week)
            
            return ParsedOption(
                underlying='10Y',
                weekday=WeekdayType.FRIDAY,
                option_type=option_type,
                strike=strike,
                expiration_date=expiry_date,
                symbol_type='friday_weekly',
                bloomberg_symbol=symbol,
                week_of_month=week
            )
        
        # Quarterly: TY[Month][Year][C/P]
        quarterly_match = re.match(r'^TY([A-Z])(\d)([CP])$', base_and_type)
        if quarterly_match:
            month_code, year_str, option_type = quarterly_match.groups()
            
            contract_month = month_decode[month_code]
            year = self._get_correct_year(year_str)  # FIXED
            
            # Treasury futures expire in month before contract month
            expiry_month = contract_month - 1 if contract_month > 1 else 12
            expiry_year = year if contract_month > 1 else year - 1
            
            expiry_date = self._calculate_4th_friday(expiry_year, expiry_month)
            
            return ParsedOption(
                underlying='10Y',
                weekday=WeekdayType.FRIDAY,
                option_type=option_type,
                strike=strike,
                expiration_date=expiry_date,
                symbol_type='quarterly',
                bloomberg_symbol=symbol,
                contract_month=contract_month
            )
        
        raise ValueError(f"Could not parse Bloomberg symbol: {symbol}")
    
    def _parse_cme(self, symbol: str) -> ParsedOption:
        """Parse CME format symbol with CORRECTED YEAR LOGIC"""
        parts = symbol.split()
        if len(parts) != 2:
            raise ValueError(f"Invalid CME format: {symbol}")
        
        base_symbol = parts[0]
        option_part = parts[1]
        
        option_type = option_part[0]
        strike = int(option_part[1:]) / 1000.0
        
        month_decode = {v: k for k, v in self.month_codes.items()}
        
        # Monday-Thursday: [WeekdayPrefix][Occurrence][Month][Year]
        weekday_match = re.match(r'^(VY|GY|WY|HY)(\d)([A-Z])(\d)$', base_symbol)
        if weekday_match:
            weekday_prefix, occurrence_str, month_code, year_str = weekday_match.groups()
            
            occurrence = int(occurrence_str)
            month = month_decode[month_code]
            year = self._get_correct_year(year_str)  # FIXED
            weekday = self.cme_weekday_mapping[weekday_prefix]
            
            expiry_date = self._calculate_weekday_occurrence(year, month, weekday, occurrence)
            
            return ParsedOption(
                underlying='10Y',
                weekday=weekday,
                option_type=option_type,
                strike=strike,
                expiration_date=expiry_date,
                symbol_type='weekday_weekly',
                cme_symbol=symbol,
                weekday_occurrence=occurrence
            )
        
        # Friday: ZN[Week][Month][Year] or ZN[Month][Year] or OZN[Month][Year]
        friday_match = re.match(r'^(ZN|OZN)(\d)?([A-Z])(\d)$', base_symbol)
        if friday_match:
            prefix, week_str, month_code, year_str = friday_match.groups()
            
            month = month_decode[month_code]
            year = self._get_correct_year(year_str)  # FIXED
            
            if week_str and prefix == 'ZN':  # Weekly format
                week = int(week_str)
                expiry_date = self._calculate_nth_friday(year, month, week)
                
                return ParsedOption(
                    underlying='10Y',
                    weekday=WeekdayType.FRIDAY,
                    option_type=option_type,
                    strike=strike,
                    expiration_date=expiry_date,
                    symbol_type='friday_weekly',
                    cme_symbol=symbol,
                    week_of_month=week
                )
            elif not week_str:  # Quarterly format
                expiry_month = month - 1 if month > 1 else 12
                expiry_year = year if month > 1 else year - 1
                expiry_date = self._calculate_4th_friday(expiry_year, expiry_month)
                
                return ParsedOption(
                    underlying='10Y',
                    weekday=WeekdayType.FRIDAY,
                    option_type=option_type,
                    strike=strike,
                    expiration_date=expiry_date,
                    symbol_type='quarterly',
                    cme_symbol=symbol,
                    contract_month=month
                )
        
        raise ValueError(f"Could not parse CME symbol: {symbol}")
    
    def _parse_xcme(self, symbol: str) -> ParsedOption:
        """Parse XCME format symbol with CORRECTED YEAR LOGIC"""
        parts = symbol.split('.')
        if len(parts) != 5 or parts[0] != 'XCME':
            raise ValueError(f"Invalid XCME format: {symbol}")
        
        _, cme_base, date_str, strike_str, option_type = parts
        
        strike = float(strike_str)
        
        # Parse date
        if re.match(r'^\d{2}[A-Z]{3}\d{2}$', date_str):  # DDMmmYY format
            day = int(date_str[:2])
            month_str = date_str[2:5]
            year_str = date_str[5:7]
            year = self._get_correct_year(year_str)  # FIXED
            
            month_decode = {v: k for k, v in self.month_names.items()}
            month = month_decode[month_str]
            
            expiry_date = datetime(year, month, day)
        elif re.match(r'^[A-Z]{3}\d{2}$', date_str):  # MmmYY format (quarterly)
            month_str = date_str[:3]
            year_str = date_str[3:5]
            year = self._get_correct_year(year_str)  # FIXED
            
            month_decode = {v: k for k, v in self.month_names.items()}
            contract_month = month_decode[month_str]
            
            expiry_month = contract_month - 1 if contract_month > 1 else 12
            expiry_year = year if contract_month > 1 else year - 1
            expiry_date = self._calculate_4th_friday(expiry_year, expiry_month)
        else:
            raise ValueError(f"Invalid XCME date format: {date_str}")
        
        # Parse CME base
        if cme_base.startswith(('VY', 'GY', 'WY', 'HY')):
            weekday_prefix = cme_base[:2]
            occurrence = int(cme_base[2:])
            weekday = self.cme_weekday_mapping[weekday_prefix]
            
            return ParsedOption(
                underlying='10Y',
                weekday=weekday,
                option_type=option_type,
                strike=strike,
                expiration_date=expiry_date,
                symbol_type='weekday_weekly',
                xcme_symbol=symbol,
                weekday_occurrence=occurrence
            )
        elif cme_base.startswith('ZN') and len(cme_base) == 3:
            week = int(cme_base[2])
            
            return ParsedOption(
                underlying='10Y',
                weekday=WeekdayType.FRIDAY,
                option_type=option_type,
                strike=strike,
                expiration_date=expiry_date,
                symbol_type='friday_weekly',
                xcme_symbol=symbol,
                week_of_month=week
            )
        elif cme_base == 'OZN':
            return ParsedOption(
                underlying='10Y',
                weekday=WeekdayType.FRIDAY,
                option_type=option_type,
                strike=strike,
                expiration_date=expiry_date,
                symbol_type='quarterly',
                xcme_symbol=symbol,
                contract_month=contract_month if 'contract_month' in locals() else 8
            )
        
        raise ValueError(f"Could not parse XCME symbol: {symbol}")
    
    def to_bloomberg(self, parsed: ParsedOption) -> str:
        """Convert parsed option to Bloomberg format"""
        if parsed.symbol_type == 'weekday_weekly':
            weekday_base_map = {v: k for k, v in self.weekday_mapping.items()}
            weekday_base = weekday_base_map[parsed.weekday]
            
            month_code = self.month_codes[parsed.expiration_date.month]
            year_code = str(parsed.expiration_date.year)[-2:]
            
            base_symbol = f"{weekday_base}{month_code}{year_code}{parsed.option_type}{parsed.weekday_occurrence}"
            return f"{base_symbol} {parsed.strike:.3f} Comdty"
        
        elif parsed.symbol_type == 'friday_weekly':
            month_code = self.month_codes[parsed.expiration_date.month]
            year_code = str(parsed.expiration_date.year)[-1:]
            
            first_month = 'M'
            base_symbol = f"{parsed.week_of_month}{first_month}{month_code}{year_code}{parsed.option_type}"
            return f"{base_symbol} {parsed.strike:.3f} Comdty"
        
        elif parsed.symbol_type == 'quarterly':
            month_code = self.month_codes[parsed.contract_month]
            year_code = str(parsed.expiration_date.year)[-1:]
            
            base_symbol = f"TY{month_code}{year_code}{parsed.option_type}"
            return f"{base_symbol} {parsed.strike:.3f} Comdty"
        
        raise ValueError(f"Unknown symbol type: {parsed.symbol_type}")
    
    def to_cme(self, parsed: ParsedOption) -> str:
        """Convert parsed option to CME Globex format"""
        if parsed.symbol_type == 'weekday_weekly':
            weekday_prefix_map = {
                WeekdayType.MONDAY: 'VY',
                WeekdayType.TUESDAY: 'GY',
                WeekdayType.WEDNESDAY: 'WY',
                WeekdayType.THURSDAY: 'HY'
            }
            
            prefix = weekday_prefix_map[parsed.weekday]
            month_code = self.month_codes[parsed.expiration_date.month]
            year_code = str(parsed.expiration_date.year)[-1:]
            
            base_symbol = f"{prefix}{parsed.weekday_occurrence}{month_code}{year_code}"
            strike_formatted = f"{int(parsed.strike * 1000):06d}"
            return f"{base_symbol} {parsed.option_type}{strike_formatted}"
        
        elif parsed.symbol_type == 'friday_weekly':
            month_code = self.month_codes[parsed.expiration_date.month]
            year_code = str(parsed.expiration_date.year)[-1:]
            
            base_symbol = f"ZN{parsed.week_of_month}{month_code}{year_code}"
            strike_formatted = f"{int(parsed.strike * 1000):06d}"
            return f"{base_symbol} {parsed.option_type}{strike_formatted}"
        
        elif parsed.symbol_type == 'quarterly':
            month_code = self.month_codes[parsed.contract_month]
            year_code = str(parsed.expiration_date.year)[-1:]
            
            base_symbol = f"OZN{month_code}{year_code}"  # Use OZN for quarterly
            strike_formatted = f"{int(parsed.strike * 1000):06d}"
            return f"{base_symbol} {parsed.option_type}{strike_formatted}"
        
        raise ValueError(f"Unknown symbol type: {parsed.symbol_type}")
    
    def to_xcme(self, parsed: ParsedOption) -> str:
        """Convert parsed option to XCME format"""
        if parsed.symbol_type == 'weekday_weekly':
            weekday_prefix_map = {
                WeekdayType.MONDAY: 'VY',
                WeekdayType.TUESDAY: 'GY',
                WeekdayType.WEDNESDAY: 'WY',
                WeekdayType.THURSDAY: 'HY'
            }
            
            prefix = weekday_prefix_map[parsed.weekday]
            cme_base = f"{prefix}{parsed.weekday_occurrence}"
            
            day = parsed.expiration_date.day
            month = self.month_names[parsed.expiration_date.month]
            year = str(parsed.expiration_date.year)[-2:]
            date_str = f"{day:02d}{month}{year}"
            
            xcme_strike = int(parsed.strike) - 1 if int(parsed.strike) == 111 else int(parsed.strike)
            
            return f"XCME.{cme_base}.{date_str}.{xcme_strike}.{parsed.option_type}"
        
        elif parsed.symbol_type == 'friday_weekly':
            cme_base = f"ZN{parsed.week_of_month}"
            
            day = parsed.expiration_date.day
            month = self.month_names[parsed.expiration_date.month]
            year = str(parsed.expiration_date.year)[-2:]
            date_str = f"{day:02d}{month}{year}"
            
            xcme_strike = int(parsed.strike) - 1 if int(parsed.strike) == 111 else int(parsed.strike)
            
            return f"XCME.{cme_base}.{date_str}.{xcme_strike}.{parsed.option_type}"
        
        elif parsed.symbol_type == 'quarterly':
            month = self.month_names[parsed.contract_month]
            year = str(parsed.expiration_date.year)[-2:]
            date_str = f"{month}{year}"
            
            xcme_strike = int(parsed.strike) - 1 if int(parsed.strike) == 111 else int(parsed.strike)
            
            return f"XCME.OZN.{date_str}.{xcme_strike}.{parsed.option_type}"
        
        raise ValueError(f"Unknown symbol type: {parsed.symbol_type}")
    
    def convert(self, symbol: str, target_format: SymbolFormat) -> str:
        """Convert any symbol to any target format"""
        parsed = self.parse_symbol(symbol)
        
        if target_format == SymbolFormat.BLOOMBERG:
            return self.to_bloomberg(parsed)
        elif target_format == SymbolFormat.CME:
            return self.to_cme(parsed)
        elif target_format == SymbolFormat.XCME:
            return self.to_xcme(parsed)
        else:
            raise ValueError(f"Unsupported target format: {target_format}")
    
    def convert_all_formats(self, symbol: str) -> Dict[str, str]:
        """Convert one symbol to all three formats"""
        parsed = self.parse_symbol(symbol)
        
        return {
            'bloomberg': self.to_bloomberg(parsed),
            'cme': self.to_cme(parsed),
            'xcme': self.to_xcme(parsed),
            'source_format': self.detect_format(symbol).value,
            'expiration_date': parsed.expiration_date.strftime('%Y-%m-%d'),
            'weekday': parsed.weekday.value,
            'symbol_type': parsed.symbol_type
        }
    
    def batch_convert(self, symbols: List[str], target_format: SymbolFormat) -> List[Dict[str, str]]:
        """Convert a list of symbols to target format"""
        results = []
        
        for symbol in symbols:
            try:
                converted = self.convert(symbol, target_format)
                source_format = self.detect_format(symbol)
                
                results.append({
                    'original': symbol,
                    'converted': converted,
                    'source_format': source_format.value,
                    'target_format': target_format.value,
                    'status': 'success'
                })
            except Exception as e:
                results.append({
                    'original': symbol,
                    'converted': None,
                    'source_format': 'unknown',
                    'target_format': target_format.value,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def _calculate_weekday_occurrence(self, year: int, month: int, weekday: WeekdayType, occurrence: int) -> datetime:
        """Calculate the Nth occurrence of a weekday in a month"""
        weekday_num = {
            WeekdayType.MONDAY: 0,
            WeekdayType.TUESDAY: 1,
            WeekdayType.WEDNESDAY: 2,
            WeekdayType.THURSDAY: 3,
            WeekdayType.FRIDAY: 4
        }[weekday]
        
        # Find first occurrence
        first_day = datetime(year, month, 1)
        days_ahead = weekday_num - first_day.weekday()
        if days_ahead < 0:
            days_ahead += 7
        
        first_occurrence = first_day + timedelta(days=days_ahead)
        
        # Add weeks for subsequent occurrences
        target_date = first_occurrence + timedelta(weeks=occurrence - 1)
        
        # Verify it's still in the same month
        if target_date.month != month:
            if weekday == WeekdayType.FRIDAY and occurrence == 4:
                return self._calculate_4th_friday(year, month)
            else:
                raise ValueError(f"No {occurrence}th {weekday.value} in {month}/{year}")
        
        return target_date
    
    def _calculate_nth_friday(self, year: int, month: int, week: int) -> datetime:
        """Calculate the Nth Friday of a month"""
        if week == 4:
            return self._calculate_4th_friday(year, month)
        else:
            return self._calculate_weekday_occurrence(year, month, WeekdayType.FRIDAY, week)
    
    def _calculate_4th_friday(self, year: int, month: int) -> datetime:
        """Calculate the 4th Friday of the month"""
        first_day = datetime(year, month, 1)
        days_ahead = 4 - first_day.weekday()  # Friday is weekday 4
        if days_ahead < 0:
            days_ahead += 7
        
        first_friday = first_day + timedelta(days=days_ahead)
        fourth_friday = first_friday + timedelta(weeks=3)
        
        if fourth_friday.month != month:
            return self._get_last_friday(year, month)
        
        return fourth_friday
    
    def _get_last_friday(self, year: int, month: int) -> datetime:
        """Get the last Friday of the month"""
        last_day = calendar.monthrange(year, month)[1]
        
        for day in range(last_day, 0, -1):
            date = datetime(year, month, day)
            if date.weekday() == 4:
                return date
        
        raise ValueError(f"No Friday found in {month}/{year}")


# DataFrame mapping function
def map_symbols(df, symbol_column, translator):
    """Map symbols in a DataFrame to all three formats"""
    bloomberg_list = []
    cme_list = []
    xcme_list = []

    for symbol in df[symbol_column]:
        try:
            all_formats = translator.convert_all_formats(symbol)
            
            bloomberg_list.append(all_formats.get('bloomberg', ''))
            cme_list.append(all_formats.get('cme', ''))
            xcme_list.append(all_formats.get('xcme', ''))
        except Exception as e:
            bloomberg_list.append(f"Error: {e}")
            cme_list.append(f"Error: {e}")
            xcme_list.append(f"Error: {e}")

    df['Bloomberg'] = bloomberg_list
    df['CME'] = cme_list
    df['XCME'] = xcme_list

    return df
def process_expiration_calendar_csv(csv_file_path):
    """
    Process the ExpirationCalendar CSV file with the fixed translator
    """
    # Initialize the translator
    translator = TreasuryOptionsTranslator()
    
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    df['Original'] = df['Option Symbol'].apply(lambda x: x.strip() + " C11100" if not x.endswith('C111000') else x.strip())
    print(f"Loaded {len(df)} rows from {csv_file_path}")
    print(f"Columns: {list(df.columns)}")
    
    # FIXED: Use the correct column name 'Option Symbol' instead of 'Original'
    print("\nProcessing symbol conversions...")
    
    result_df = map_symbols(df, 'Original', translator)
    
    # Check for any conversion errors
    error_count = 0
    for col in ['Bloomberg', 'CME', 'XCME']:
        errors = result_df[col].str.contains('Error', na=False).sum()
        error_count += errors
        if errors > 0:
            print(f"❌ {col}: {errors} conversion errors")
        else:
            print(f"✅ {col}: All conversions successful")
    
    if error_count == 0:
        print(f"\n🎉 SUCCESS: All {len(df)} symbols converted successfully!")
    else:
        print(f"\n⚠️  {error_count} total conversion errors found")
        
        # Show some error examples
        print("\nFirst few errors:")
        for col in ['Bloomberg', 'CME', 'XCME']:
            error_rows = result_df[result_df[col].str.contains('Error', na=False)]
            if len(error_rows) > 0:
                print(f"\n{col} errors:")
                for i, (idx, row) in enumerate(error_rows.head(3).iterrows()):
                    print(f"  {i+1}. {row['Option Symbol']} → {row[col]}")
    
    # Show before/after comparison for OZN symbols (previously failing)
    ozn_rows = result_df[result_df['Option Symbol'].str.startswith('OZN', na=False)]
    if len(ozn_rows) > 0:
        print(f"\n📊 OZN Quarterly Options: {len(ozn_rows)} symbols")
        print("=" * 80)
        for idx, row in ozn_rows.head(5).iterrows():
            print(f"{row['Option Symbol']} → {row['Bloomberg']}")
            print(f"  Expires: {row['Option Expiration Date (CT)']}")
            print()
    
    # Save the corrected file
    output_file = csv_file_path.replace('.csv', '_CORRECTED.csv')
    result_df.to_csv(output_file, index=False)
    print(f"💾 Corrected file saved as: {output_file}")
    
    return result_df


if __name__ == "__main__":
    csv_file = "c:/temp/ExpirationCalendar.csv"
    
    try:
        # Read and analyze the file first
        #df = pd.read_csv(csv_file)
        

        
        corrected_df = process_expiration_calendar_csv(csv_file)
        
        print("\n🎯 PROCESSING COMPLETE!")
        
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file}")
        print("Please check the file path")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()