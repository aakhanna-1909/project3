# Import the libraries
import pandas as pd
import streamlit as st
import yfinance as yf
import time
import datetime
import numpy as np

# Get all tickers of stocks in the S&P 500 stock market index
sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
sp500_tickers = sp500[0]["Symbol"]
sp500_tickers_sample = sp500_tickers.sample(n=5).reset_index(drop=True)


# Display five random stock tickers on the UI on the streamlit UI
st.write("The stocks available to you are: ")
st.write(sp500_tickers_sample)


# Allow user to enter the a symbol from the displayed list
sp500_tickers_input_value = st.text_input("Enter a stock ticker").upper()


# Define function to retrieve the ticker index number [COMPLETE]
def get_key_number_from_ticker(ticker_value):
    ticker_symbol = sp500[0]["Symbol"]
    ticker_symbol_dict = ticker_symbol.to_dict()
    for key, value in ticker_symbol_dict.items():
        if value == ticker_value:
            return key
    return 999


# Define function to retrieve stock information [COMPLETE]
def get_stock_info_from_key_number(ticker_key):
    stock_info_df = sp500[0][["Security", "GICS Sector", "GICS Sub-Industry", "Headquarters Location"]]
    new_cols = ["Security", "Sector", "Sub-Industry", "Headquarters"]
    stock_info_df.columns = new_cols
    
    if ticker_key < len(stock_info_df):
        stock_info_df = stock_info_df.loc[ticker_key, :]
        return stock_info_df
    else:
        empty_series = pd.Series({"Security": "Enter a valid ticker!", 
                    "Sector":"Enter a valid ticker!",
                    "Sub-Industry":"Enter a valid ticker!",
                    "Headquarters":"Enter a valid ticker!"})
        return empty_series
 



# Capital Asset Pricing Model


# Define function to get risk-free rate from Yahoo Finance (risk-free rate = 10-year US Treasury Bond Yield)

def get_risk_free_rate():
    url = "https://finance.yahoo.com/bonds"
    us_bonds = pd.read_html(url)    
    us_bonds_df = us_bonds[0]
    index = ["13_week_tbill", "treasury_yield_5years", "treasury_yield_10years", "treasury_yield_30years"]
    us_bonds_df = us_bonds_df.set_index("Name")
    us_10_year_bond_yield = (us_bonds_df.loc["Treasury Yield 10 Years", "Last Price"])/100
    return us_10_year_bond_yield

# Define a function to get stock beta using Yahoo Finance library

def stock_beta(ticker_value):
    ticker_data = yf.Ticker(ticker_value)
    ticker_beta = ticker_data.info["beta"]
    return ticker_beta

# Define function to calculate the Cost of Equity (we use Capital Asset Pricing Model)

def cost_of_equity(beta):
    risk_free_rate = get_risk_free_rate() # Higher T-Bill yield will result in higher stock return...  The current 10-Y US T-Bill rate is 3.87%, which is quite high because the fed keeps increasing returns to combat inflation. But to be more realistic I took a rate of 2.5%
    expected_market_return = 0.08 # Higher expected market rate is giving higher expected stock return... I am taking a conservative value of 8%
    expected_stock_return = risk_free_rate + beta*(expected_market_return - risk_free_rate)
    return expected_stock_return

# Define function to get Total Debt value from Balance Sheet

def get_total_debt(ticker_value):
    # Set the stock ticker
    stock_ticker = yf.Ticker(ticker_value)
    
    # Get the Balance Sheet data of the stock ticker in a Pandas DataFrame
    stock_balance_sheet = stock_ticker.balance_sheet
    
    # Get the value of the latest 10K filling date
    cols = stock_balance_sheet.columns
    latest_filling_date = cols[0]
    latest_filling_date = latest_filling_date.strftime("%Y-%m-%d")
    
    # Get value for Total Debt
    total_debt = stock_balance_sheet.loc["Total Debt", latest_filling_date]
    return round(total_debt)

def get_market_cap(ticker_value):
    
    # Set the stock ticker
    stock_ticker = yf.Ticker(ticker_value)
    
    # Get the Balance Sheet data of the stock ticker in a Pandas DataFrame
    market_cap = stock_ticker.info["marketCap"]
        
    return market_cap

    
# Define function to calculate weight of equity
def weight_of_equity(ticker_value):
    equity_weight = get_market_cap(ticker_value) / ( get_total_debt(ticker_value) +  get_market_cap(ticker_value))
    return equity_weight


# Define function to calculate weight of debt
def weight_of_debt(ticker_value):
    debt_weight = get_total_debt(ticker_value) / ( get_total_debt(ticker_value) +  get_market_cap(ticker_value))
    return debt_weight



# Define function to calculate Cost of debt

def cost_of_debt(ticker_value):
    # Set the stock ticker
    stock_ticker = yf.Ticker(ticker_value)
    
    # Get the Income Statement data of the stock ticker in a Pandas DataFrame
    stock_income_statement = stock_ticker.income_stmt
    
    # Get the value of the latest 10K filling date
    cols = stock_income_statement.columns
    latest_filling_date = cols[0]
    latest_filling_date = latest_filling_date.strftime("%Y-%m-%d")
    
    # Get value for Interest expense from Income Statement
    interest_expense = stock_income_statement.loc["Interest Expense Non Operating",latest_filling_date]
    #print(interest_expense)

    # Get value of total debt from get_total_debt() function
    total_debt = get_total_debt(ticker_value)

    # Calculate Cost of Debt = (Interest Expense) / (Total Debt)
    debt_cost = interest_expense / total_debt

    return debt_cost




# Define function to calculate Effective Tax Rate

# Effective Tax Rate = (Income Tax Expense) / (Pre-tax Income)
 

def effective_tax_rate(ticker_value):
    # Set the stock ticker
    stock_ticker = yf.Ticker(ticker_value)
    
    # Get the Income Statement data of the stock ticker in a Pandas DataFrame
    stock_income_statement = stock_ticker.income_stmt
    
    # Get the value of the latest 10K filling date
    cols = stock_income_statement.columns
    latest_filling_date = cols[0]
    latest_filling_date = latest_filling_date.strftime("%Y-%m-%d")
    
    # Get value for Income Tax Expense from Income Statement
    income_tax_expense = stock_income_statement.loc["Tax Provision", latest_filling_date]
    #print("The income tax expense is: " + str(income_tax_expense))
    #print(type(income_tax_expense))
    #print("_________________________________________")

    # Get value for Pretax Income from Income Statement
    pretax_income = stock_income_statement.loc["Pretax Income", latest_filling_date]
    #print("The pretax income is: " + str(pretax_income))
    #print(type(pretax_income))

    # Calculate Effective Tax Rate = (Income Tax Expense) / (Pretax Income)
    effective_tax_rate = income_tax_expense / pretax_income


    return effective_tax_rate







# Define function to calculate WACC

# WACC = {Weight of equity * Cost of equity} + {Weight of debt * Cost of debt * (1 - Effective Tax Rate}

def wacc(ticker_value):
    weight_equity = weight_of_equity(ticker_value)
    cost_equity = cost_of_equity(stock_beta(ticker_value))
    weight_debt = weight_of_debt(ticker_value)
    cost_debt = cost_of_debt(ticker_value)
    eff_tax_rate_minus_1 = (1 - effective_tax_rate(ticker_value))
    discount_rate = (weight_equity * cost_equity) + (weight_debt * cost_debt * eff_tax_rate_minus_1)
    return discount_rate








# Define function to calculate Average Free Cash Flow Growth Rate

def fcf_growth_rate(ticker_value):
    
    # Get the ticker value from the user
    ticker = yf.Ticker(ticker_value)
    
    # Get the Statement of Cash Flows from Yahoo Finance
    ticker_cash_flow_statement = ticker.cashflow
    
    # Get the historical Free Cash Flow values from the Cash Flow Statement
    ticker_historical_fcf = ticker_cash_flow_statement.loc["Free Cash Flow", :]
    
    # Get the Free Cash Flow values into a Pandas DataFrame
    ticker_historical_fcf_df = pd.DataFrame(ticker_historical_fcf)
    
    # Sort the indices of the Free Cash Flow values DataFrame to see the oldest FCF value first
    ticker_historical_fcf_df = ticker_historical_fcf_df.sort_index()
    #display(ticker_historical_fcf_df)
    
    # Create a new column that contains the FCF Growth Rate (using pct_change() function)
    ticker_historical_fcf_df["FCF Growth Rate"] = ticker_historical_fcf_df.pct_change(periods=1)
    #display(ticker_historical_fcf_df)
    
    # Get the minimum value for the FCF Growth Rate, which will be used to project the future Free Cash Flows. We use the minimum value for the FCF Growth Rate to get the most conservative estimate.
    fcf_growth_rate = ticker_historical_fcf_df["FCF Growth Rate"].min()
    #print(fcf_growth_rate)
    
    # Return the Free Cash Flow Growth Rate
    return fcf_growth_rate









def projected_fcf(ticker_value):
    
    # Get the growth rate for the specified company ticker using fcf_growth_rate() function
    growth_rate = fcf_growth_rate(ticker_value)
    
    # Hard-code the perpetual growth rate for the company (equivalent to US Economy growth rate)
    perpetual_growth_rate = 0.02
    
    # Get the discount rate (WACC) for the specified company ticker using wacc() function
    discount_rate_wacc = wacc(ticker_value)
    
    # Get the ticker value as function's parameter
    ticker = yf.Ticker(ticker_value)

    # Get the Statement of Cash Flows from Yahoo Finance
    ticker_cash_flow_statement = ticker.cashflow
    #print(msft_cash_flow_stmt.loc["Free Cash Flow", :])

    
    # Get the historical Free Cash Flow values from the Cash Flow Statement
    ticker_historical_fcf_df = pd.DataFrame(ticker_cash_flow_statement.loc["Free Cash Flow", :])
    #display(ticker_historical_fcf_df)
    
    # Sort the indices of the historical FCF DataFrame to see the oldest FCF value first
    ticker_historical_fcf_df = ticker_historical_fcf_df.sort_index()
    #display(ticker_historical_fcf_df)
    
    # Reset the indices of historical FCF DataFrame
    ticker_historical_fcf_df = ticker_historical_fcf_df.reset_index()
    
    # Create a new DataFrame column called "Year"
    ticker_historical_fcf_df['Year'] = pd.DatetimeIndex(ticker_historical_fcf_df['index']).year
    
    # Drop the index column from historical FCF DataFrame
    ticker_historical_fcf_df = ticker_historical_fcf_df.drop(columns="index")
    #display(ticker_historical_fcf_df)
    
    # Get latest FCF value from the historical FCF DataFrame. This is our starting point for projecting FCF.
    latest_fcf_df = pd.DataFrame(ticker_historical_fcf_df.iloc[(len(ticker_historical_fcf_df) - 1), :]).T.reset_index(drop=True)
    #display(latest_fcf_df)
        
    most_recent_year = latest_fcf_df["Year"][0]
    #display(most_recent_year)
        
    # Project first FCF, one year into the future
    projected_fcf_1 = latest_fcf_df.loc[(len(latest_fcf_df.index)-1), "Free Cash Flow"] * (1+growth_rate)
    projected_year_1 = latest_fcf_df.loc[(len(latest_fcf_df.index)-1), "Year"] + 1
    latest_fcf_df.loc[len(latest_fcf_df.index)] = [projected_fcf_1, projected_year_1]
    #display(latest_fcf_df)

    # Project second FCF, two years into the future
    projected_fcf_2 = latest_fcf_df.loc[(len(latest_fcf_df.index)-1), "Free Cash Flow"] * (1+growth_rate)
    projected_year_2 = latest_fcf_df.loc[(len(latest_fcf_df.index)-1), "Year"] + 1
    latest_fcf_df.loc[len(latest_fcf_df.index)] = [projected_fcf_2, projected_year_2]
    #display(latest_fcf_df)
    
    # Project third FCF, three years into the future
    projected_fcf_3 = latest_fcf_df.loc[(len(latest_fcf_df.index)-1), "Free Cash Flow"] * (1+growth_rate)
    projected_year_3 = latest_fcf_df.loc[(len(latest_fcf_df.index)-1), "Year"] + 1
    latest_fcf_df.loc[len(latest_fcf_df.index)] = [projected_fcf_3, projected_year_3]
    #display(latest_fcf_df)
    
    # Project fourth FCF, four years into the future
    projected_fcf_4 = latest_fcf_df.loc[(len(latest_fcf_df.index)-1), "Free Cash Flow"] * (1+growth_rate)
    projected_year_4 = latest_fcf_df.loc[(len(latest_fcf_df.index)-1), "Year"] + 1
    latest_fcf_df.loc[len(latest_fcf_df.index)] = [projected_fcf_4, projected_year_4]

                        
                        
    #display(latest_fcf_df)
    
    # Project fifth FCF, five years into the future
    projected_fcf_5 = latest_fcf_df.loc[(len(latest_fcf_df.index)-1), "Free Cash Flow"] * (1+growth_rate)
    projected_year_5 = latest_fcf_df.loc[(len(latest_fcf_df.index)-1), "Year"] + 1
    latest_fcf_df.loc[len(latest_fcf_df.index)] = [projected_fcf_5, projected_year_5]
    #print(latest_fcf_df)
    
    
    # Calculate the terminal value
    
    # Get the last projected FCF, five years into the future
    last_projected_fcf = latest_fcf_df.loc[(len(latest_fcf_df)-1), "Free Cash Flow"]
    #print(last_projected_fcf)
    
    # Get the last projected Year, five years into the future
    last_projected_year = latest_fcf_df.loc[(len(latest_fcf_df)-1), "Year"]
    
    # Calculate the terminal value. Formula: {(Last projected FCF * (1 + Perpetual growth rate)} / {(WACC discount rate) - (Perpetual growth rate)}
    projected_terminal_value = (last_projected_fcf * (1 + perpetual_growth_rate)) / (discount_rate_wacc - perpetual_growth_rate)
    #print(projected_terminal_value)
    
    # Add the terminal value to the latest_fcf_df DataFrame
    latest_fcf_df.loc[len(latest_fcf_df.index)] = [projected_terminal_value, last_projected_year]
    #print(latest_fcf_df)
    
    # Grab the calculated terminal value from the last row of the latest_fcf_df DataFrame
    terminal_value = latest_fcf_df.loc[(len(latest_fcf_df.index) - 1), "Free Cash Flow"]
    
    # Drop the last row of the latest_fcf_df DataFrame
    latest_fcf_df = latest_fcf_df.drop(latest_fcf_df.tail(1).index) # drop last 1 row
    #print(latest_fcf_df)
    
    # Add the calculated terminal value to the final projected FCF, five years into the future
    latest_fcf_df.loc[len(latest_fcf_df) - 1] = [(projected_fcf_5 + terminal_value), projected_year_5]
    
    # Drop the first row from the latest_fcf_df DataFrame
    latest_fcf_df = latest_fcf_df.drop(latest_fcf_df.head(1).index) # drop first 1 row

    # Drop the "Year" column from the latest_fcf_df DataFrame
    latest_fcf_df = latest_fcf_df.drop(columns="Year").reset_index(drop=False)
    
    return latest_fcf_df















# Define a function to calculate the sum of Present Values of all projected FCF
def present_values(ticker_value):
    
    # Get the discount rate, wacc() function
    discount_rate = wacc(ticker_value)
    
    # Get the Data Frame that contains the projected future cash flows, projected_fcf() function
    projected_fcf_df = projected_fcf(ticker_value)
    
    # Create an empty column called "Present Value" in the projected FCF DataFrame
    projected_fcf_df["Present Value"] = np.nan

    # Create a FOR loop that will loop through each row of projected FCF Data Frame, calculating the present value of each projected cash flow
    for each_index, each_row in projected_fcf_df.iterrows():
        projected_fcf_df.loc[each_index, "Present Value"] = (projected_fcf_df.loc[each_index, "Free Cash Flow"]) / ( (1 + discount_rate)**(projected_fcf_df.loc[each_index, "index"]) )
    
    
    # print(projected_fcf_df)
    # Add up the Present Values of all projected cash flows. This is the Enterprise Value
    enterprise_value = projected_fcf_df["Present Value"].sum()
    
    # Return the Enterprise Value
    return enterprise_value





# Define function to calculate the intrinsic value of a stock

def intrinsic_value(ticker_value):
    
    # Get the Enterprise Value, pv() function
    enterprise_value = present_values(ticker_value)
    #print(enterprise_value)
    
    # Set the stock ticker
    stock_ticker = yf.Ticker(ticker_value)
    
    # Get the Balance Sheet data of the stock ticker in a Pandas DataFrame
    stock_balance_sheet = stock_ticker.balance_sheet
    
    # Get the value of the latest 10K filling date
    cols = stock_balance_sheet.columns
    latest_filling_date = cols[0]
    latest_filling_date = latest_filling_date.strftime("%Y-%m-%d")
    
    # Get value for "Cash, Cash Equivalents, And Short Term Investments"
    cash = stock_balance_sheet.loc["Cash Cash Equivalents And Short Term Investments", latest_filling_date]
    #print(cash)
    
    # Get value for total debt, get_total_debt() function
    total_debt = get_total_debt(ticker_value)
    #print(total_debt)
    
    # Calculate Equity Value (= Enterprise Value + Cash - Total Debt)
    equity_value = enterprise_value + cash - total_debt
    #print(equity_value)
    
    # Get no. of shares outstanding
    shares_outstanding = stock_ticker.info["sharesOutstanding"]
    #print(shares_outstanding)
    
    # Calculate intrinsic value per share (= equity_value / shares_outstanding)
    intrinsic_value_per_share = equity_value / shares_outstanding
    #print(intrinsic_value_per_share)
    
    return intrinsic_value_per_share









# Allow user to enter the a symbol from the displayed list
if st.button("Go"):

    st.write("Corporation Name: "+ get_stock_info_from_key_number(get_key_number_from_ticker(sp500_tickers_input_value))["Security"])
    st.write("Sector: "+ get_stock_info_from_key_number(get_key_number_from_ticker(sp500_tickers_input_value))["Sector"])
    st.write("Sub-Industry: "+ get_stock_info_from_key_number(get_key_number_from_ticker(sp500_tickers_input_value))["Sub-Industry"])
    st.write("Headquarters: "+ get_stock_info_from_key_number(get_key_number_from_ticker(sp500_tickers_input_value))["Headquarters"])
    st.write("The intrinsic value of the stock is: " + str(intrinsic_value(sp500_tickers_input_value)))
    
