"""
SAP PCR Generator — Comprehensive Payroll Test Suite
100+ real-world SAP HCM payroll scenarios
Run: python test_runner.py
"""

import requests
import sys
import time

BASE_URL = "http://localhost:8000"
DELAY_BETWEEN_TESTS = 4  # seconds — avoids Groq 429 rate limit on free tier

TEST_CASES = [

    # ══════════════════════════════════════════════════════
    # SECTION 1: BASIC WAGE TYPE OPERATIONS
    # ══════════════════════════════════════════════════════
    {
        "section": "BASIC OPERATIONS",
        "name": "Simple copy wage type",
        "prompt": "Load wage type 1000 into AMT and store result in wage type 2000",
        "must_contain": ["AMT= 1000", "ADDWT 2000"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Add two wage types",
        "prompt": "Add wage type 1000 and wage type 1010 together and store in 2000",
        "must_contain": ["AMT= 1000", "AMT+ 1010", "ADDWT 2000"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Subtract wage type",
        "prompt": "Deduct wage type 0200 from wage type 1000 and store in 3000",
        "must_contain": ["AMT= 1000", "AMT- 0200", "ADDWT 3000"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Combine three wage types",
        "prompt": "Add wage types 1000, 1010 and 1020 together and store total in 9000",
        "must_contain": ["AMT= 1000", "AMT+ 1010", "AMT+ 1020", "ADDWT 9000"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Zero out a wage type",
        "prompt": "Load wage type 1000 and zero all registers then store in 9000",
        "must_contain": ["AMT= 1000", "ADDWT 9000"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 2: PERCENTAGE CALCULATIONS
    # ══════════════════════════════════════════════════════
    {
        "section": "PERCENTAGE CALCULATIONS",
        "name": "150% overtime premium",
        "prompt": "Calculate overtime at 150% of wage type 1000 and store in 9000",
        "must_contain": ["AMT= 1000", "AMT* 150", "AMT/ 100", "ADDWT 9000"],
        "must_not_contain": ["AMT* 1.5", "THEN", "IF "],
    },
    {
        "name": "200% double time",
        "prompt": "Apply 200% double time rate to wage type 1000 and store result in 8000",
        "must_contain": ["AMT= 1000", "AMT* 200", "AMT/ 100", "ADDWT 8000"],
        "must_not_contain": ["AMT* 2.0", "THEN"],
    },
    {
        "name": "10% income tax deduction",
        "prompt": "Calculate 10% income tax from wage type 2000 and store result in 9100",
        "must_contain": ["AMT= 2000", "AMT* 10", "AMT/ 100", "ADDWT 9100"],
        "must_not_contain": ["AMT* 0.1", "THEN"],
    },
    {
        "name": "12% provident fund deduction",
        "prompt": "Calculate 12% provident fund contribution from basic pay wage type 1000 and store in 9200",
        "must_contain": ["AMT= 1000", "AMT* 12", "AMT/ 100", "ADDWT 9200"],
        "must_not_contain": ["AMT* 0.12", "THEN"],
    },
    {
        "name": "8.33% gratuity calculation",
        "prompt": "Calculate 8.33% gratuity from wage type 1000 and store in 9300",
        "must_contain": ["AMT= 1000", "AMT* 833", "AMT/ 10000", "ADDWT 9300"],
        "must_not_contain": ["AMT* 0.08", "THEN"],
    },
    {
        "name": "125% shift allowance",
        "prompt": "Calculate night shift allowance at 125% of wage type 1000 and store in 3000",
        "must_contain": ["AMT= 1000", "AMT* 125", "AMT/ 100", "ADDWT 3000"],
        "must_not_contain": ["AMT* 1.25", "THEN"],
    },
    {
        "name": "80% partial pay",
        "prompt": "Calculate 80% of basic pay wage type 1000 and store in 5000",
        "must_contain": ["AMT= 1000", "AMT* 80", "AMT/ 100", "ADDWT 5000"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "50% half pay leave",
        "prompt": "Calculate half pay at 50% of wage type 1000 and store in 5100",
        "must_contain": ["AMT= 1000", "AMT* 50", "AMT/ 100", "ADDWT 5100"],
        "must_not_contain": ["AMT* 0.5", "THEN"],
    },
    {
        "name": "175% overtime",
        "prompt": "Calculate overtime premium at 175% of wage type 1000 and store in 9010",
        "must_contain": ["AMT= 1000", "AMT* 175", "AMT/ 100", "ADDWT 9010"],
        "must_not_contain": ["AMT* 1.75", "THEN"],
    },
    {
        "name": "2% professional tax",
        "prompt": "Calculate 2% professional tax from gross pay wage type 2000 and store in 9400",
        "must_contain": ["AMT= 2000", "AMT* 2", "AMT/ 100", "ADDWT 9400"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 3: LEAVE ENCASHMENT
    # ══════════════════════════════════════════════════════
    {
        "section": "LEAVE ENCASHMENT",
        "name": "Leave encashment annual basis (Basic/365)*12*Days",
        "prompt": "Calculate leave encashment where leave days are in wage type 9110 and basic salary is in wage type 1000. Formula: (Basic / 365) * 12 * Leave Days. Store result in 9000",
        "must_contain": ["AMT= 1000", "AMT* 12", "AMT/ 365", "NUM= 9110", "MULTI NUM", "ADDWT 9000"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Leave encashment monthly basis (Basic/26)*Days",
        "prompt": "Calculate leave encashment where leave days are in wage type 9110 and basic salary is in wage type 1000. Formula: (Basic / 26) * Leave Days. Store result in 9000",
        "must_contain": ["AMT= 1000", "AMT/ 26", "NUM= 9110", "MULTI NUM", "ADDWT 9000"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Leave encashment 30-day basis (Basic/30)*Days",
        "prompt": "Calculate leave encashment where leave days are in wage type 9110 and basic salary is in wage type 1000. Formula: (Basic / 30) * Leave Days. Store result in 9000",
        "must_contain": ["AMT= 1000", "AMT/ 30", "NUM= 9110", "MULTI NUM", "ADDWT 9000"],
        "must_not_contain": ["THEN", "IF "],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 4: OVERTIME CALCULATIONS
    # ══════════════════════════════════════════════════════
    {
        "section": "OVERTIME",
        "name": "Overtime hours exceed 8 daily",
        "prompt": "If overtime hours in wage type 3000 exceed 8, calculate 150% of wage type 1000 and store in 9000",
        "must_contain": ["NUM= 3000", "NUM?> 8", "AMT= 1000", "AMT* 150", "AMT/ 100", "ADDWT 9000"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Overtime hours exceed 40 weekly",
        "prompt": "If weekly hours in wage type 3001 exceed 40, calculate 150% of wage type 1000 and store in 9001",
        "must_contain": ["NUM= 3001", "NUM?> 40", "AMT= 1000", "AMT* 150", "AMT/ 100", "ADDWT 9001"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Overtime hours below threshold skip",
        "prompt": "If hours in wage type 2000 are less than 40, apply 80% to wage type 1000 and store in 5000",
        "must_contain": ["NUM= 2000", "NUM?< 40", "AMT= 1000", "AMT* 80", "AMT/ 100", "ADDWT 5000"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Double overtime above 12 hours",
        "prompt": "If overtime hours in wage type 3000 exceed 12, calculate 200% of wage type 1000 and store in 9005",
        "must_contain": ["NUM= 3000", "NUM?> 12", "AMT= 1000", "AMT* 200", "AMT/ 100", "ADDWT 9005"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Overtime rate times hours",
        "prompt": "Multiply overtime rate from wage type 1000 by overtime hours in wage type 3000 and store in 9000",
        "must_contain": ["RTE= 1000", "NUM= 3000", "MULTI NUM", "ADDWT 9000"],
        "must_not_contain": ["THEN", "IF "],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 5: RATE × HOURS (TIME-BASED PAY)
    # ══════════════════════════════════════════════════════
    {
        "section": "RATE × HOURS",
        "name": "Basic rate times planned hours",
        "prompt": "Multiply rate from wage type 1000 by hours in wage type 2000 and store in 3000",
        "must_contain": ["RTE= 1000", "NUM= 2000", "MULTI NUM", "ADDWT 3000"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Shift rate times shift hours",
        "prompt": "Multiply shift rate from wage type 1100 by shift hours in wage type 2100 and store in 3100",
        "must_contain": ["RTE= 1100", "NUM= 2100", "MULTI NUM", "ADDWT 3100"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Holiday rate times holiday hours",
        "prompt": "Multiply holiday pay rate from wage type 1200 by holiday hours in wage type 2200 and store in 3200",
        "must_contain": ["RTE= 1200", "NUM= 2200", "MULTI NUM", "ADDWT 3200"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Piece rate times units produced",
        "prompt": "Multiply piece rate from wage type 1300 by units produced in wage type 2300 and store in 3300",
        "must_contain": ["RTE= 1300", "NUM= 2300", "MULTI NUM", "ADDWT 3300"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 6: ALLOWANCES
    # ══════════════════════════════════════════════════════
    {
        "section": "ALLOWANCES",
        "name": "House rent allowance 40% of basic",
        "prompt": "Calculate house rent allowance at 40% of basic pay wage type 1000 and store in 1100",
        "must_contain": ["AMT= 1000", "AMT* 40", "AMT/ 100", "ADDWT 1100"],
        "must_not_contain": ["AMT* 0.4", "THEN"],
    },
    {
        "name": "Dearness allowance 20% of basic",
        "prompt": "Calculate dearness allowance at 20% of basic pay wage type 1000 and store in 1200",
        "must_contain": ["AMT= 1000", "AMT* 20", "AMT/ 100", "ADDWT 1200"],
        "must_not_contain": ["AMT* 0.2", "THEN"],
    },
    {
        "name": "Medical allowance 15% of basic",
        "prompt": "Calculate medical allowance at 15% of basic pay wage type 1000 and store in 1300",
        "must_contain": ["AMT= 1000", "AMT* 15", "AMT/ 100", "ADDWT 1300"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Transport allowance 10% of basic",
        "prompt": "Calculate transport allowance at 10% of basic pay wage type 1000 and store in 1400",
        "must_contain": ["AMT= 1000", "AMT* 10", "AMT/ 100", "ADDWT 1400"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Children education allowance 5% of basic",
        "prompt": "Calculate children education allowance at 5% of basic pay wage type 1000 and store in 1500",
        "must_contain": ["AMT= 1000", "AMT* 5", "AMT/ 100", "ADDWT 1500"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Night shift allowance 25% of basic",
        "prompt": "Calculate night shift allowance at 25% of wage type 1000 and store in 1600",
        "must_contain": ["AMT= 1000", "AMT* 25", "AMT/ 100", "ADDWT 1600"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Food allowance fixed add",
        "prompt": "Add food allowance from wage type 1700 to basic pay wage type 1000 and store total in 2000",
        "must_contain": ["AMT= 1000", "AMT+ 1700", "ADDWT 2000"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Fuel allowance add to gross",
        "prompt": "Add fuel allowance wage type 1800 to gross pay wage type 2000 and store in 2100",
        "must_contain": ["AMT= 2000", "AMT+ 1800", "ADDWT 2100"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Special allowance 30% of basic",
        "prompt": "Calculate special allowance at 30% of basic pay wage type 1000 and store in 1900",
        "must_contain": ["AMT= 1000", "AMT* 30", "AMT/ 100", "ADDWT 1900"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 7: DEDUCTIONS
    # ══════════════════════════════════════════════════════
    {
        "section": "DEDUCTIONS",
        "name": "PF employee contribution 12%",
        "prompt": "Calculate employee provident fund at 12% of basic pay wage type 1000 and store deduction in 9200",
        "must_contain": ["AMT= 1000", "AMT* 12", "AMT/ 100", "ADDWT 9200"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "ESI deduction 1.75% of gross",
        "prompt": "Calculate ESI employee contribution at 175% of gross pay wage type 2000 divided by 10000 and store in 9210",
        "must_contain": ["AMT= 2000", "ADDWT 9210"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Professional tax deduction",
        "prompt": "Deduct professional tax wage type 9400 from gross pay wage type 2000 and store net in 9500",
        "must_contain": ["AMT= 2000", "AMT- 9400", "ADDWT 9500"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Loan deduction from net pay",
        "prompt": "Deduct loan repayment wage type 9600 from net pay wage type 9500 and store in 9700",
        "must_contain": ["AMT= 9500", "AMT- 9600", "ADDWT 9700"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Advance salary deduction",
        "prompt": "Deduct salary advance wage type 9610 from net pay wage type 9700 and store in 9800",
        "must_contain": ["AMT= 9700", "AMT- 9610", "ADDWT 9800"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Multiple deductions from gross",
        "prompt": "From gross pay wage type 2000, subtract PF wage type 9200, ESI wage type 9210 and tax wage type 9100 and store net in 9500",
        "must_contain": ["AMT= 2000", "AMT- 9200", "AMT- 9210", "AMT- 9100", "ADDWT 9500"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "TDS income tax deduction",
        "prompt": "Deduct TDS income tax wage type 9100 from gross wage type 2000 and store in 9500",
        "must_contain": ["AMT= 2000", "AMT- 9100", "ADDWT 9500"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 8: GRATUITY
    # ══════════════════════════════════════════════════════
    {
        "section": "GRATUITY",
        "name": "Gratuity 15 days per year of service",
        "prompt": "Calculate gratuity where basic salary is in wage type 1000 and years of service are in wage type 9120. Formula: (Basic / 26) * 15 * Years. Store in 9300",
        "must_contain": ["AMT= 1000", "AMT/ 26", "AMT* 15", "NUM= 9120", "MULTI NUM", "ADDWT 9300"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Gratuity monthly basis",
        "prompt": "Calculate gratuity as (basic pay wage type 1000 divided by 30) multiplied by 15 multiplied by years of service in wage type 9120 and store in 9300",
        "must_contain": ["AMT= 1000", "NUM= 9120", "MULTI NUM", "ADDWT 9300"],
        "must_not_contain": ["THEN", "IF "],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 9: BONUS CALCULATIONS
    # ══════════════════════════════════════════════════════
    {
        "section": "BONUS",
        "name": "Annual bonus 8.33% of annual basic",
        "prompt": "Calculate annual bonus at 8.33% of annual basic pay wage type 1000 multiplied by 12 and store in 9350",
        "must_contain": ["AMT= 1000", "AMT* 12", "ADDWT 9350"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Performance bonus 20% of basic",
        "prompt": "Calculate performance bonus at 20% of basic pay wage type 1000 and store in 9360",
        "must_contain": ["AMT= 1000", "AMT* 20", "AMT/ 100", "ADDWT 9360"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Festival bonus one month basic",
        "prompt": "Copy basic pay wage type 1000 as festival bonus and store in wage type 9370",
        "must_contain": ["AMT= 1000", "ADDWT 9370"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Sales incentive 5% of target",
        "prompt": "Calculate sales incentive at 5% of target amount wage type 4000 and store in 9380",
        "must_contain": ["AMT= 4000", "AMT* 5", "AMT/ 100", "ADDWT 9380"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Retention bonus 30% of basic",
        "prompt": "Calculate retention bonus at 30% of basic pay wage type 1000 and store in 9390",
        "must_contain": ["AMT= 1000", "AMT* 30", "AMT/ 100", "ADDWT 9390"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 10: GROSS PAY AGGREGATION
    # ══════════════════════════════════════════════════════
    {
        "section": "GROSS PAY",
        "name": "Gross pay basic plus HRA plus DA",
        "prompt": "Add basic pay wage type 1000, HRA wage type 1100 and dearness allowance wage type 1200 and store gross in 2000",
        "must_contain": ["AMT= 1000", "AMT+ 1100", "AMT+ 1200", "ADDWT 2000"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Gross pay five components",
        "prompt": "Add wage types 1000, 1100, 1200, 1300 and 1400 together and store total gross pay in 2000",
        "must_contain": ["AMT= 1000", "AMT+ 1100", "AMT+ 1200", "AMT+ 1300", "AMT+ 1400", "ADDWT 2000"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Gross pay including overtime",
        "prompt": "Add basic pay wage type 1000 and overtime pay wage type 9000 and store total in 2000",
        "must_contain": ["AMT= 1000", "AMT+ 9000", "ADDWT 2000"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 11: NET PAY CALCULATION
    # ══════════════════════════════════════════════════════
    {
        "section": "NET PAY",
        "name": "Net pay after PF and tax",
        "prompt": "From gross pay wage type 2000 subtract provident fund wage type 9200 and income tax wage type 9100 and store net pay in 9500",
        "must_contain": ["AMT= 2000", "AMT- 9200", "AMT- 9100", "ADDWT 9500"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Net pay after all deductions",
        "prompt": "From gross pay wage type 2000 subtract PF wage type 9200, ESI wage type 9210, tax wage type 9100 and loan wage type 9600 and store net pay in 9500",
        "must_contain": ["AMT= 2000", "AMT- 9200", "AMT- 9210", "AMT- 9100", "AMT- 9600", "ADDWT 9500"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 12: PRORATION / PARTIAL MONTH
    # ══════════════════════════════════════════════════════
    {
        "section": "PRORATION",
        "name": "Prorate basic pay by working days",
        "prompt": "Prorate basic pay wage type 1000 by multiplying by actual working days in wage type 2500 then dividing by 26 working days and store in 1001",
        "must_contain": ["AMT= 1000", "NUM= 2500", "MULTI NUM", "AMT/ 26", "ADDWT 1001"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Prorate pay by calendar days",
        "prompt": "Prorate wage type 1000 by actual days worked in wage type 2500 divided by 30 calendar days and store in 1002",
        "must_contain": ["AMT= 1000", "NUM= 2500", "MULTI NUM", "AMT/ 30", "ADDWT 1002"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Loss of pay deduction",
        "prompt": "Calculate loss of pay by loading basic wage type 1000, dividing by 26 working days, multiplying by absent days in wage type 2600 and store deduction in 9650",
        "must_contain": ["AMT= 1000", "AMT/ 26", "NUM= 2600", "MULTI NUM", "ADDWT 9650"],
        "must_not_contain": ["THEN", "IF "],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 13: CONDITIONAL PAYMENTS
    # ══════════════════════════════════════════════════════
    {
        "section": "CONDITIONAL PAYMENTS",
        "name": "Pay only if AMT positive",
        "prompt": "Load wage type 1000, if AMT is greater than 0 continue else exit, then store in 9000",
        "must_contain": ["AMT= 1000", "AMT?> 0", "ADDWT 9000"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Conditional overtime above threshold",
        "prompt": "If overtime hours in wage type 3000 exceed 8, calculate 150% of wage type 1000 and store in 9000",
        "must_contain": ["NUM= 3000", "NUM?> 8", "AMT= 1000", "AMT* 150", "AMT/ 100", "ADDWT 9000"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Conditional shift allowance",
        "prompt": "If shift hours in wage type 3100 exceed 0, calculate 25% of basic pay wage type 1000 and store in 1600",
        "must_contain": ["NUM= 3100", "NUM?> 0", "AMT= 1000", "AMT* 25", "AMT/ 100", "ADDWT 1600"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Conditional deduction if gross exceeds threshold",
        "prompt": "If gross pay in wage type 2000 exceeds 15000, deduct professional tax wage type 9400 from gross and store net in 9500",
        "must_contain": ["AMT= 2000", "AMT?> 15000", "AMT- 9400", "ADDWT 9500"],
        "must_not_contain": ["THEN", "IF "],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 14: EMPLOYER CONTRIBUTIONS
    # ══════════════════════════════════════════════════════
    {
        "section": "EMPLOYER CONTRIBUTIONS",
        "name": "Employer PF contribution 12%",
        "prompt": "Calculate employer provident fund contribution at 12% of basic pay wage type 1000 and store in 9220",
        "must_contain": ["AMT= 1000", "AMT* 12", "AMT/ 100", "ADDWT 9220"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Employer ESI contribution 4.75%",
        "prompt": "Calculate employer ESI contribution at 475% of gross pay wage type 2000 divided by 10000 and store in 9230",
        "must_contain": ["AMT= 2000", "ADDWT 9230"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Employer gratuity provision",
        "prompt": "Calculate employer gratuity provision at 4.81% of basic pay wage type 1000 and store in 9310",
        "must_contain": ["AMT= 1000", "ADDWT 9310"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 15: DAILY / HOURLY RATE CALCULATIONS
    # ══════════════════════════════════════════════════════
    {
        "section": "DAILY AND HOURLY RATES",
        "name": "Daily rate from monthly basic divide by 26",
        "prompt": "Calculate daily rate by dividing basic pay wage type 1000 by 26 working days and store in 1050",
        "must_contain": ["AMT= 1000", "AMT/ 26", "ADDWT 1050"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Daily rate from monthly basic divide by 30",
        "prompt": "Calculate daily rate by dividing basic pay wage type 1000 by 30 calendar days and store in 1051",
        "must_contain": ["AMT= 1000", "AMT/ 30", "ADDWT 1051"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Hourly rate from monthly basic",
        "prompt": "Calculate hourly rate by dividing basic pay wage type 1000 by 208 hours per month and store in 1052",
        "must_contain": ["AMT= 1000", "AMT/ 208", "ADDWT 1052"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Annual salary from monthly",
        "prompt": "Calculate annual salary by multiplying monthly basic pay wage type 1000 by 12 and store in 1060",
        "must_contain": ["AMT= 1000", "AMT* 12", "ADDWT 1060"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 16: ARREARS
    # ══════════════════════════════════════════════════════
    {
        "section": "ARREARS",
        "name": "Salary arrears copy to arrear wage type",
        "prompt": "Copy arrear basic pay from wage type 1000 to arrear wage type 9900",
        "must_contain": ["AMT= 1000", "ADDWT 9900"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Arrear HRA calculation",
        "prompt": "Calculate arrear HRA at 40% of arrear basic pay wage type 9900 and store in 9910",
        "must_contain": ["AMT= 9900", "AMT* 40", "AMT/ 100", "ADDWT 9910"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Total arrear aggregation",
        "prompt": "Add arrear basic wage type 9900 and arrear HRA wage type 9910 and store total arrear in 9950",
        "must_contain": ["AMT= 9900", "AMT+ 9910", "ADDWT 9950"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 17: LOAN AND ADVANCE
    # ══════════════════════════════════════════════════════
    {
        "section": "LOAN AND ADVANCE",
        "name": "Loan EMI deduction",
        "prompt": "Deduct loan EMI wage type 9600 from net pay wage type 9500 and store in 9700",
        "must_contain": ["AMT= 9500", "AMT- 9600", "ADDWT 9700"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Salary advance deduction",
        "prompt": "Deduct salary advance wage type 9610 from net pay wage type 9700 and store final pay in 9800",
        "must_contain": ["AMT= 9700", "AMT- 9610", "ADDWT 9800"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Vehicle loan deduction",
        "prompt": "Deduct vehicle loan installment wage type 9620 from gross pay wage type 2000 and store in 9710",
        "must_contain": ["AMT= 2000", "AMT- 9620", "ADDWT 9710"],
        "must_not_contain": ["THEN"],
    },

    # ══════════════════════════════════════════════════════
    # SECTION 18: SPECIAL SCENARIOS
    # ══════════════════════════════════════════════════════
    {
        "section": "SPECIAL SCENARIOS",
        "name": "No THEN keyword ever",
        "prompt": "Check if hours in 3000 are greater than 8 then pay 150% from 1000 into 9000",
        "must_contain": ["NUM= 3000", "ADDWT 9000"],
        "must_not_contain": ["THEN", "IF THEN"],
    },
    {
        "name": "No indexed access",
        "prompt": "Load the amount from wage type 2000 and apply 120% and store in 5000",
        "must_contain": ["AMT= 2000", "AMT* 120", "AMT/ 100", "ADDWT 5000"],
        "must_not_contain": ["AMT(", "NUM(", "RTE("],
    },
    {
        "name": "No decimal percentage",
        "prompt": "Calculate 15% of basic pay wage type 1000 and store in 1300",
        "must_contain": ["AMT= 1000", "AMT* 15", "AMT/ 100", "ADDWT 1300"],
        "must_not_contain": ["AMT* 0.15", "AMT* .15"],
    },
    {
        "name": "Suppress zero wage type output",
        "prompt": "Load wage type 1000, if AMT equals 0 suppress the output otherwise store in 9000",
        "must_contain": ["AMT= 1000", "ADDWT 9000"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Copy NUM hours to output",
        "prompt": "Load overtime hours from wage type 3000 into NUM and store in output wage type 3001",
        "must_contain": ["NUM= 3000", "ADDWT 3001"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Weekend overtime double rate",
        "prompt": "If weekend hours in wage type 3200 exceed 0, calculate 200% of basic rate wage type 1000 and store in 9020",
        "must_contain": ["NUM= 3200", "NUM?> 0", "AMT= 1000", "AMT* 200", "AMT/ 100", "ADDWT 9020"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Public holiday triple pay",
        "prompt": "If public holiday hours in wage type 3300 exceed 0, calculate 300% of wage type 1000 and store in 9030",
        "must_contain": ["NUM= 3300", "NUM?> 0", "AMT= 1000", "AMT* 300", "AMT/ 100", "ADDWT 9030"],
        "must_not_contain": ["THEN", "IF "],
    },
    {
        "name": "Salary revision difference",
        "prompt": "Subtract old basic pay wage type 1001 from new basic pay wage type 1000 and store salary revision difference in 9950",
        "must_contain": ["AMT= 1000", "AMT- 1001", "ADDWT 9950"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "CTC total cost to company",
        "prompt": "Add gross pay wage type 2000, employer PF wage type 9220 and employer ESI wage type 9230 and store CTC in 9990",
        "must_contain": ["AMT= 2000", "AMT+ 9220", "AMT+ 9230", "ADDWT 9990"],
        "must_not_contain": ["THEN"],
    },
    {
        "name": "Payout after all deductions",
        "prompt": "From gross pay 2000 subtract tax 9100, PF 9200, ESI 9210, loan 9600 and advance 9610 and store final payout in 9800",
        "must_contain": ["AMT= 2000", "AMT- 9100", "AMT- 9200", "AMT- 9210", "AMT- 9600", "AMT- 9610", "ADDWT 9800"],
        "must_not_contain": ["THEN"],
    },
]


def run_tests():
    passed = 0
    failed = 0
    errors = 0
    current_section = ""

    total = len(TEST_CASES)
    print(f"\n{'═'*64}")
    print(f"  SAP PCR Generator — Comprehensive Payroll Test Suite")
    print(f"  {total} scenarios | Target: {BASE_URL}")
    print(f"  Delay: {DELAY_BETWEEN_TESTS}s between tests (Groq free tier)")
    print(f"{'═'*64}\n")

    for i, test in enumerate(TEST_CASES, 1):

        # Print section header
        if test.get("section") and test["section"] != current_section:
            current_section = test["section"]
            print(f"\n  ── {current_section} {'─'*(50-len(current_section))}")

        name = test["name"]
        prompt = test["prompt"]

        if i > 1:
            time.sleep(DELAY_BETWEEN_TESTS)

        try:
            res = requests.post(
                f"{BASE_URL}/generate",
                json={"prompt": prompt},
                timeout=40
            )
            data = res.json()
        except Exception as e:
            print(f"  [{i:03d}] ❌ {name}")
            print(f"         ERROR: {e}")
            errors += 1
            continue

        if not data.get("ok"):
            print(f"  [{i:03d}] ❌ {name}")
            print(f"         API ERROR: {data.get('error', '')[:120]}")
            errors += 1
            continue

        pcr = data.get("pcr", "")
        fail_reasons = []

        for expected in test.get("must_contain", []):
            if expected not in pcr:
                fail_reasons.append(f"Missing: '{expected}'")

        for forbidden in test.get("must_not_contain", []):
            if forbidden in pcr:
                fail_reasons.append(f"Forbidden: '{forbidden}'")

        warnings = data.get("warnings", [])

        if not fail_reasons and not warnings:
            print(f"  [{i:03d}] ✅ {name}")
            passed += 1
        elif not fail_reasons and warnings:
            print(f"  [{i:03d}] ⚠️  {name}")
            for w in warnings:
                print(f"         ⚠  {w}")
            passed += 1
        else:
            print(f"  [{i:03d}] ❌ {name}")
            for r in fail_reasons:
                print(f"         ✗  {r}")
            print(f"         PCR: {pcr[:200]}")
            failed += 1

    print(f"\n{'═'*64}")
    print(f"  RESULTS: {passed}/{total} passed  |  {failed} failed  |  {errors} errors")
    score = int((passed / total) * 100)
    print(f"  SCORE:   {score}%")
    print(f"{'═'*64}\n")

    if failed > 0 or errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()