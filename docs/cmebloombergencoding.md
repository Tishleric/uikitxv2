Based on CME Group’s official documentation, Treasury Weekly Options are available for every weekday (Monday through Friday) with different symbols, rules, and settlement procedures for each day.

Key Features of Treasury Weekly Options:

Weekday-Specific Symbols for 10-Year Treasury:

• Monday: VY (e.g., VY2N5 = 2nd Monday of July 2025)

• Tuesday: GY (e.g., GY2N5 = 2nd Tuesday of July 2025)

• Wednesday: WY (e.g., WY2N5 = 2nd Wednesday of July 2025)

• Thursday: HY (e.g., HY2N5 = 2nd Thursday of July 2025)

• Friday: ZN (e.g., ZN2N5 = 2nd Friday of July 2025)

Critical Differences by Weekday:

Monday-Thursday Options:

• Trading stops at 2:00 PM CT on expiration

• No contrary instructions allowed

• Two expirations listed at a time (~14 days each)

• ATM calls auto-exercised, ATM puts auto-abandoned

Friday Options (Standard):

• Trading continues until 4:00 PM CT

• Contrary instructions allowed

• Three expirations listed at a time (~28 days each)

• All ATM options auto-abandoned

Technical Specifications:

Strike Increments:

• 10-Year and Ultra 10-Year Note options: ¼ of one point

• 2-Year Note options: 1/8 of one point

• U.S. Treasury Bond and Ultra Bond options: ½ of one point

Exercise and Settlement:

• All WTOs exercise physically into their underlying Treasury futures contracts

• A Weekly option will exercise into the same futures contract as its nearest subsequent quarterly option

Real-World Examples:

Wednesday 10Y Weekly Options (WY2N5):

• Call 109.50: WY2N5 C109500

• Put 109.00: WY2N5 P109000

• Bloomberg: TYYA C10950 Comdty / TYYA P10900 Comdty

Monday 10Y Weekly Options (VY2N5):

• Call 109.50: VY2N5 C109500

• Put 109.00: VY2N5 P109000

• Bloomberg: VBYA C10950 Comdty / VBYA P10900 Comdty

The two artifacts I created provide:

1. Python backend system with complete weekly options calendar generation, symbol mapping, and option chain creation

2. Interactive reference tables showing live expiration schedules, symbol examples by weekday, and sample option chains