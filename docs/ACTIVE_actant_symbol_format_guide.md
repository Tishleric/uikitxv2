# ACTIVE Actant Symbol Format Guide

This is the **ACTIVE** guide for understanding and converting Actant symbol formats.

## Overview

Actant uses a proprietary format for encoding futures and options symbols. This guide documents the format and conversion rules to Bloomberg and CME/TYU5 formats.

## Actant Symbol Format

### Futures Format
```
XCMEFFDPSX{YYYYMMDD}{MonthCode}{Digit}{ProductCode}
```

Example: `XCMEFFDPSX20250919U0ZN`
- `XCME`: Exchange (CME)
- `FFDPS`: Futures identifier
- `X`: Separator
- `20250919`: Expiry date (YYYYMMDD)
- `U`: Month code (September)
- `0`: Additional identifier
- `ZN`: Product code (10-Year Treasury Note)

### Options Format
```
XCME{Type}PS{YYYYMMDD}N0{SeriesCode}{WeekDigit}/{Strike}
```

Example: `XCMEOCADPS20250714N0VY2/108.75`
- `XCME`: Exchange (CME)
- `OCAD`: Call option (OPAD for Put)
- `PS`: Options identifier
- `20250714`: Trade/expiry date (YYYYMMDD)
- `N0`: Additional identifier
- `VY`: Series code (Monday weekly)
- `2`: Week number
- `108.75`: Strike price

## Symbol Mappings

### Futures Product Codes
| Actant | Bloomberg | Product |
|--------|-----------|---------|
| ZN | TY | 10-Year Treasury Note |
| TU | TU | 2-Year Treasury Note |
| FV | FV | 5-Year Treasury Note |
| US | US | Ultra Treasury Bond |
| RX | RX | Euro-Bund |

### Options Series Codes
| Actant | Bloomberg | CME | Weekday |
|--------|-----------|-----|---------|
| VY | VBY | VY | Monday |
| TJ | TJP | GY | Tuesday |
| WY | TYW | WY | Wednesday |
| TH | TJW | HY | Thursday |
| ZN | 3M | ZN | Friday |

## Conversion Examples

### Futures
- Actant: `XCMEFFDPSX20250919U0ZN`
- Bloomberg: `TYU5 Comdty`
- CME/TYU5: `TYU5`

### Options
- Actant: `XCMEOCADPS20250714N0VY2/108.75`
- Bloomberg: `VBYN25C2 108.750 Comdty`
- CME/TYU5: `VY2N5 C 108.750`

## Month Codes
| Month | Code |
|-------|------|
| January | F |
| February | G |
| March | H |
| April | J |
| May | K |
| June | M |
| July | N |
| August | Q |
| September | U |
| October | V |
| November | X |
| December | Z |

## Processing Rules

1. **SOD Trades**: Skip trades with timestamp `00:00:00.000` (Start of Day positions)
2. **Exercised Options**: Skip trades with price = 0 (exercised options)
3. **Trade IDs**: Generate globally unique IDs as `{filename}_{tradeId}_{row_number}`
4. **Action Mapping**: 
   - Positive quantity → 'BUY'
   - Negative quantity → 'SELL'
5. **Fixed Values**:
   - Fees: 0.0
   - Counterparty: 'FRGM'

## Implementation References

- Symbol Translation: `lib/trading/symbol_translator.py`
- Trade Processing: `lib/trading/pnl_calculator/trade_preprocessor.py`
- File Watching: `lib/trading/pnl_calculator/trade_file_watcher.py` 