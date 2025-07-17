# Bloomberg Symbol Reference for Treasury Futures Options

## Overview
This document provides a comprehensive guide to Bloomberg symbol structures for Treasury futures and options.

## Symbol Structure

### Futures
Format: `{Product}{Month}{Year} Comdty`
- Example: `TYU5 Comdty`
  - TY = 10-Year Treasury Note
  - U = September
  - 5 = 2025

### Options
Format: `{Product}{Series}{Month}{Year}{Type}{Week} {Strike} Comdty`
- Example: `VBYN25P3 110.250 Comdty`
  - VBY = Product/Series code
  - N = July
  - 25 = 2025
  - P = Put (C for Call)
  - 3 = 3rd week
  - 110.250 = Strike price

## Product Codes

### Treasury Futures
- TY = 10-Year Treasury Note
- US = 30-Year Treasury Bond
- TU = 2-Year Treasury Note
- FV = 5-Year Treasury Note
- UXY = Ultra 10-Year
- WN = Ultra Bond

### Option Series Prefixes
- 3M = 3-month options
- TYW = TY Weekly options
- VBY = Weekly options (various)
- TJP = Japan trading hours

## Month Codes
- F = January
- G = February  
- H = March
- J = April
- K = May
- M = June
- N = July
- Q = August
- U = September
- V = October
- X = November
- Z = December

## Week Indicators
- 1 = 1st week of month
- 2 = 2nd week of month
- 3 = 3rd week of month
- 4 = 4th week of month
- 5 = 5th week (if applicable)

## Examples

### Futures
- `TYU5 Comdty` = 10-Year Treasury Sept 2025
- `USZ5 Comdty` = 30-Year Bond Dec 2025

### Options
- `3MN5P 110.000 Comdty` = 3-month July 2025 Put, 110 strike
- `TYWN25P4 109.750 Comdty` = TY Weekly July 2025 Put, 4th week, 109.75 strike
- `VBYN25C3 111.000 Comdty` = Weekly July 2025 Call, 3rd week, 111 strike

## Mapping to Actant Format

Actant format: `XCME.{Product}.{Expiry}.{Strike}.{Type}`
- Example: `XCME.ZN2.11JUL25.110.25.P`

### Translation Rules
1. Extract product type from Bloomberg prefix
2. Convert month code to month name
3. Extract week number for weekly options
4. Parse strike price
5. Identify Put/Call from symbol

## Notes
- Strike prices in Bloomberg are in decimal format (e.g., 110.250)
- Weekly options have week indicators (1-5)
- Standard monthly options don't have week indicators
- All treasury derivatives end with "Comdty" commodity identifier 