import pandas as pd

from datetime import datetime, timedelta

from typing import Dict, List, Optional, Tuple

import numpy as np

from dataclasses import dataclass

from enum import Enum

import calendar



class TreasuryWeeklyDay(Enum):

MONDAY = “Monday”

TUESDAY = “Tuesday”

WEDNESDAY = “Wednesday”

THURSDAY = “Thursday”

FRIDAY = “Friday”



@dataclass

class TreasuryWeeklyOption:

symbol: str

underlying_futures: str

expiration_date: datetime

expiry_weekday: TreasuryWeeklyDay

strike: float

option_type: str  # ‘C’ or ‘P’

week_of_month: int

cme_globex_symbol: str

bloomberg_ticker: str

refinitiv_ticker: str

days_to_expiry: Optional[int] = None

underlying_price: Optional[float] = None



class TreasuryWeeklyOptionsTable:

def **init**(self):

self.treasury_products = self._initialize_treasury_products()

self.month_codes = self._get_month_codes()

self.weekday_symbols = self._get_weekday_symbols()



```

def _initialize_treasury_products(self) -> Dict:

    """Initialize Treasury futures products that support weekly options"""

    return {

        '2Y': {

            'name': '2-Year Treasury Note',

            'cme_futures_symbol': 'ZT',

            'bloomberg_futures': 'TU',

            'strike_increment': 0.125,  # 1/8 point

            'contract_size': 200000,

            'tick_value': 7.8125,

            'globex_base': {

                'monday': 'VT',

                'tuesday': 'GT', 

                'wednesday': 'WT',

                'thursday': 'HT',

                'friday': 'ZT'

            }

        },

        '5Y': {

            'name': '5-Year Treasury Note',

            'cme_futures_symbol': 'ZF',

            'bloomberg_futures': 'FV',

            'strike_increment': 0.25,  # 1/4 point

            'contract_size': 100000,

            'tick_value': 7.8125,

            'globex_base': {

                'monday': 'VF',

                'tuesday': 'GF',

                'wednesday': 'WF', 

                'thursday': 'HF',

                'friday': 'ZF'

            }

        },

        '10Y': {

            'name': '10-Year Treasury Note',

            'cme_futures_symbol': 'ZN',

            'bloomberg_futures': 'TY',

            'strike_increment': 0.25,  # 1/4 point

            'contract_size': 100000,

            'tick_value': 15.625,

            'globex_base': {

                'monday': 'VY',

                'tuesday': 'GY',

                'wednesday': 'WY',

                'thursday': 'HY', 

                'friday': 'ZN'

            }

        },

        'UXY': {

            'name': 'Ultra 10-Year Treasury Note',

            'cme_futures_symbol': 'TN',

            'bloomberg_futures': 'UXY',

            'strike_increment': 0.25,  # 1/4 point

            'contract_size': 100000,

            'tick_value': 15.625,

            'globex_base': {

                'monday': 'VX',

                'tuesday': 'GX',

                'wednesday': 'WX',

                'thursday': 'HX',

                'friday': 'TN'

            }

        },

        '30Y': {

            'name': 'U.S. Treasury Bond',

            'cme_futures_symbol': 'ZB',

            'bloomberg_futures': 'US',

            'strike_increment': 0.5,  # 1/2 point

            'contract_size': 100000,

            'tick_value': 31.25,

            'globex_base': {

                'monday': 'VB',

                'tuesday': 'GB',

                'wednesday': 'WB',

                'thursday': 'HB',

                'friday': 'ZB'

            }

        },

        'UB': {

            'name': 'Ultra Treasury Bond',

            'cme_futures_symbol': 'UB',

            'bloomberg_futures': 'WN',

            'strike_increment': 0.5,  # 1/2 point

            'contract_size': 100000,

            'tick_value': 31.25,

            'globex_base': {

                'monday': 'VU',

                'tuesday': 'GU',

                'wednesday': 'WU',

                'thursday': 'HU',

                'friday': 'UB'

            }

        }

    }



def _get_month_codes(self) -> Dict[int, str]:

    """CME month codes"""

    return {

        1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',

        7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'

    }



def _get_weekday_symbols(self) -> Dict[str, str]:

    """Get weekday symbol mapping"""

    return {

        'monday': 'V',

        'tuesday': 'G', 

        'wednesday': 'W',

        'thursday': 'H',

        'friday': 'Z'  # Note: Friday uses regular quarterly symbols

    }



def generate_weekly_expiration_calendar(self, underlying: str = '10Y', 

                                      start_date: datetime = None,

                                      weeks_ahead: int = 12) -> pd.DataFrame:

    """Generate weekly expiration calendar for Treasury options"""

    if start_date is None:

        start_date = datetime.now()

        

    expirations = []

    current_date = start_date

    

    for week in range(weeks_ahead):

        # Find Monday of current week

        monday = current_date - timedelta(days=current_date.weekday())

        

        for day_offset, weekday in enumerate(['monday', 'tuesday', 'wednesday', 'thursday', 'friday']):

            expiry_date = monday + timedelta(days=day_offset)

            

            # Skip if expiry date is in the past

            if expiry_date < start_date:

                continue

            

            # Check for holidays (simplified - would need proper holiday calendar)

            if self._is_market_holiday(expiry_date):

                continue

            

            week_of_month = self._get_week_of_month(expiry_date)

            

            # Determine which futures contract this option exercises into

            futures_contract = self._get_futures_contract_for_option(expiry_date, underlying)

            

            # Generate CME Globex symbol

            globex_symbol = self._generate_globex_symbol(

                underlying, weekday, week_of_month, expiry_date

            )

            

            # Generate Bloomberg ticker

            bloomberg_ticker = self._generate_bloomberg_wto_ticker(

                underlying, weekday, expiry_date

            )

            

            expirations.append({

                'underlying': underlying,

                'expiration_date': expiry_date,

                'weekday': weekday.capitalize(),

                'week_of_month': week_of_month,

                'week_of_year': week + 1,

                'days_to_expiry': (expiry_date - start_date).days,

                'futures_contract': futures_contract,

                'globex_symbol_base': globex_symbol,

                'bloomberg_ticker_base': bloomberg_ticker,

                'is_monthly_expiry': self._is_monthly_expiry(expiry_date, weekday),

                'settlement_time': '2:00 PM CT',

                'trading_ends': '2:00 PM CT' if weekday != 'friday' else '4:00 PM CT'

            })

        

        current_date += timedelta(days=7)

    

    return pd.DataFrame(expirations)



def generate_option_chain(self, underlying: str, expiry_weekday: str, 

                        expiration_date: datetime, current_futures_price: float,

                        strike_range: Tuple[float, float] = None) -> pd.DataFrame:

    """Generate complete option chain for specific weekday expiration"""

    

    if underlying not in self.treasury_products:

        raise ValueError(f"Underlying {underlying} not supported")

    

    product_info = self.treasury_products[underlying]

    strike_increment = product_info['strike_increment']

    

    # Default strike range: ±5 points from current price

    if strike_range is None:

        strike_range = (

            current_futures_price - 5.0,

            current_futures_price + 5.0

        )

    

    # Generate strikes

    start_strike = strike_range[0] - (strike_range[0] % strike_increment)

    strikes = np.arange(start_strike, strike_range[1] + strike_increment, strike_increment)

    

    options = []

    week_of_month = self._get_week_of_month(expiration_date)

    

    for strike in strikes:

        for option_type in ['C', 'P']:

            # Generate symbols

            globex_symbol = self._generate_globex_symbol(

                underlying, expiry_weekday.lower(), week_of_month, expiration_date

            )

            

            bloomberg_ticker = self._generate_bloomberg_wto_ticker(

                underlying, expiry_weekday.lower(), expiration_date

            )

            

            # Add strike and option type to symbols

            full_globex = f"{globex_symbol} {option_type}{self._format_strike_for_globex(strike)}"

            full_bloomberg = f"{bloomberg_ticker} {option_type}{self._format_strike_for_bloomberg(strike)} Comdty"

            

            # Create option object

            option = TreasuryWeeklyOption(

                symbol=f"{underlying}_{expiry_weekday[0]}{week_of_month}_{expiration_date.strftime('%m%d')}_{option_type}{int(strike*4):03d}",

                underlying_futures=self._get_futures_contract_for_option(expiration_date, underlying),

                expiration_date=expiration_date,

                expiry_weekday=TreasuryWeeklyDay(expiry_weekday.capitalize()),

                strike=strike,

                option_type=option_type,

                week_of_month=week_of_month,

                cme_globex_symbol=full_globex,

                bloomberg_ticker=full_bloomberg,

                refinitiv_ticker=self._generate_refinitiv_ticker(underlying, expiry_weekday, week_of_month),

                days_to_expiry=(expiration_date - datetime.now()).days,

                underlying_price=current_futures_price

            )

            

            options.append(option)

    

    # Convert to DataFrame

    df = pd.DataFrame([

        {

            'symbol': opt.symbol,

            'underlying_futures': opt.underlying_futures,

            'expiration_date': opt.expiration_date,

            'expiry_weekday': opt.expiry_weekday.value,

            'strike': opt.strike,

            'option_type': opt.option_type,

            'week_of_month': opt.week_of_month,

            'cme_globex_symbol': opt.cme_globex_symbol,

            'bloomberg_ticker': opt.bloomberg_ticker,

            'refinitiv_ticker': opt.refinitiv_ticker,

            'days_to_expiry': opt.days_to_expiry,

            'moneyness': 'ITM' if (opt.option_type == 'C' and opt.strike < current_futures_price) or 

                       (opt.option_type == 'P' and opt.strike > current_futures_price) else 'OTM',

            'intrinsic_value': max(0, current_futures_price - opt.strike if opt.option_type == 'C' 

                                 else opt.strike - current_futures_price)

        }

        for opt in options

    ])

    

    return df.sort_values(['option_type', 'strike'])



def _generate_globex_symbol(self, underlying: str, weekday: str, 

                          week_of_month: int, expiry_date: datetime) -> str:

    """Generate CME Globex symbol for weekly Treasury options"""

    product_info = self.treasury_products[underlying]

    base_symbol = product_info['globex_base'][weekday]

    month_code = self.month_codes[expiry_date.month]

    year_code = str(expiry_date.year)[-1]  # Last digit of year

    

    return f"{base_symbol}{week_of_month}{month_code}{year_code}"



def _generate_bloomberg_wto_ticker(self, underlying: str, weekday: str, 

                                 expiry_date: datetime) -> str:

    """Generate Bloomberg ticker for weekly Treasury options"""

    # Bloomberg WTO naming varies by day and product

    weekday_map = {

        'monday': 'VBY',

        'tuesday': 'TJP', 

        'wednesday': 'TYY',

        'thursday': 'TJW',

        'friday': f"{self._get_bloomberg_weekly_base(underlying)}"

    }

    

    if underlying == '10Y':

        if weekday == 'friday':

            # Friday uses standard format with week number

            week = self._get_week_of_month(expiry_date)

            return f"{week}MA"

        else:

            return f"{weekday_map.get(weekday, 'TYY')}A"

    

    return f"{underlying}_WTO_{weekday.upper()}"



def _generate_refinitiv_ticker(self, underlying: str, weekday: str, week: int) -> str:

    """Generate Refinitiv ticker format"""

    if underlying == '10Y':

        base_map = {

            'monday': 'VYW',

            'tuesday': f'GY{week}W',

            'wednesday': '0#WYW+',

            'thursday': f'HY{week}W', 

            'friday': '0#TYW+'

        }

        return base_map.get(weekday, f'{underlying}_{weekday}W')

    

    return f'{underlying}_{weekday}W'



def _get_bloomberg_weekly_base(self, underlying: str) -> str:

    """Get Bloomberg base for weekly options"""

    mapping = {

        '2Y': '1WA',

        '5Y': '1IA', 

        '10Y': '1MA',

        'UXY': 'UXWA',

        '30Y': '1CA',

        'UB': '1JA'

    }

    return mapping.get(underlying, f'{underlying}W')



def _format_strike_for_globex(self, strike: float) -> str:

    """Format strike for CME Globex"""

    return f"{strike:.3f}".replace('.', '')



def _format_strike_for_bloomberg(self, strike: float) -> str:

    """Format strike for Bloomberg"""

    return f"{strike:.2f}".replace('.', '')



def _get_week_of_month(self, date: datetime) -> int:

    """Get week of month (1-5)"""

    first_day = date.replace(day=1)

    first_weekday = first_day.weekday()

    days_since_first = (date.day - 1)

    return (days_since_first + first_weekday) // 7 + 1



def _is_market_holiday(self, date: datetime) -> bool:

    """Check if date is a market holiday (simplified)"""

    # This would need a proper holiday calendar

    major_holidays = [

        datetime(2025, 1, 1),   # New Year's Day

        datetime(2025, 1, 20),  # MLK Day

        datetime(2025, 2, 17),  # Presidents Day

        datetime(2025, 5, 26),  # Memorial Day

        datetime(2025, 6, 19),  # Juneteenth

        datetime(2025, 7, 4),   # Independence Day

        datetime(2025, 9, 1),   # Labor Day

        datetime(2025, 11, 27), # Thanksgiving

        datetime(2025, 12, 25)  # Christmas

    ]

    return date.date() in [h.date() for h in major_holidays]



def _is_monthly_expiry(self, expiry_date: datetime, weekday: str) -> bool:

    """Check if this is a monthly expiry (third Friday)"""

    if weekday.lower() != 'friday':

        return False

    

    # Find third Friday of the month

    first_day = expiry_date.replace(day=1)

    first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)

    third_friday = first_friday + timedelta(days=14)

    

    return expiry_date.date() == third_friday.date()



def _get_futures_contract_for_option(self, expiry_date: datetime, underlying: str) -> str:

    """Determine which futures contract the option exercises into"""

    # Weekly options exercise into the same futures as the nearest quarterly option

    # This is a simplified version - real implementation would need full quarterly calendar

    

    year = expiry_date.year

    month = expiry_date.month

    

    # Quarterly months: Mar(3), Jun(6), Sep(9), Dec(12)

    quarterly_months = [3, 6, 9, 12]

    

    # Find next quarterly month

    next_quarterly = None

    for q_month in quarterly_months:

        if month <= q_month:

            next_quarterly = q_month

            break

    

    if next_quarterly is None:

        next_quarterly = 3

        year += 1

    

    month_code = self.month_codes[next_quarterly]

    year_code = str(year)[-2:]

    futures_symbol = self.treasury_products[underlying]['cme_futures_symbol']

    

    return f"{futures_symbol}{month_code}{year_code}"

```



# Example usage and demonstration



if **name** == “**main**”:

# Initialize the Treasury weekly options system

treasury_weekly = TreasuryWeeklyOptionsTable()



```

# Generate weekly expiration calendar for 10Y Treasury

print("=== 10-Year Treasury Weekly Options Expiration Calendar ===")

calendar_df = treasury_weekly.generate_weekly_expiration_calendar('10Y', weeks_ahead=8)

print(calendar_df[['expiration_date', 'weekday', 'week_of_month', 'days_to_expiry', 

                  'globex_symbol_base', 'futures_contract']].head(15))

print()



# Generate option chain for Monday expiry

print("=== Monday Weekly Options Chain (Example) ===")

next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)

monday_chain = treasury_weekly.generate_option_chain(

    underlying='10Y',

    expiry_weekday='Monday', 

    expiration_date=next_monday,

    current_futures_price=110.50,  # Example futures price

    strike_range=(109.0, 112.0)

)

print(monday_chain[['strike', 'option_type', 'cme_globex_symbol', 'bloomberg_ticker', 

                   'moneyness', 'intrinsic_value']].head(10))

print()



# Generate option chain for Wednesday expiry  

print("=== Wednesday Weekly Options Chain (Example) ===")

next_wednesday = next_monday + timedelta(days=2)

wednesday_chain = treasury_weekly.generate_option_chain(

    underlying='10Y',

    expiry_weekday='Wednesday',

    expiration_date=next_wednesday, 

    current_futures_price=110.50,

    strike_range=(109.0, 112.0)

)

print(wednesday_chain[['strike', 'option_type', 'cme_globex_symbol', 'bloomberg_ticker',

                      'moneyness', 'intrinsic_value']].head(10))

print()



# Show different weekday symbol examples

print("=== Weekly Treasury Options Symbol Examples ===")

examples = [

    ('Monday', 'VY2N5', 'VBYA Comdty', 'Second Monday in July 2025'),

    ('Tuesday', 'GY2N5', 'TJPA Comdty', 'Second Tuesday in July 2025'), 

    ('Wednesday', 'WY2N5', 'TYYA Comdty', 'Second Wednesday in July 2025'),

    ('Thursday', 'HY2N5', 'TJWA Comdty', 'Second Thursday in July 2025'),

    ('Friday', 'ZN2N5', '2MA Comdty', 'Second Friday in July 2025')

]



for weekday, globex, bloomberg, description in examples:

    print(f"{weekday:9} | CME: {globex} | Bloomberg: {bloomberg:12} | {description}")

```