# Necessary packages:
import pandas as pd
import numpy as np
import requests
import json
import cvxpy as cp

# Read JSON data from url into Pandas DataFrame (table format):
def read_JSON(url):
    # Read in JSON data from URL:
    response = requests.get(url)
    json_data = json.loads(response.text)

    # Put JSON data as Pandas DataFrame (table):
    df = pd.DataFrame(json_data)

    return df

# Function to put prices from all symbols into a DataFrame (table):
def get_prices(symbols, url):
    # Read JSON data for symbols retrieved above:
    url_symbs = url[:-10] + 'get_hist_cotacao/' + symbols[0]  # Url for symbol price data
    df = read_JSON(url_symbs)

    # Make a Pandas DataFrame (table) to get price data for each symbol:
    prices_df = pd.DataFrame(index=pd.to_datetime(df.datahora_cotacao).dt.normalize())  # Ensure each date is the same
    prices_df[symbols[0]] = df.cotacao.values  # Set price values to symbol
    prices_df = prices_df[~prices_df.index.duplicated(keep='first')]  # Filter out duplicated dates

    # Populate the rest of the symbols into the above DataFrame (table):
    for symb in symbols[1:]:
        # Read JSON data for each symbol:
        url_symb = url_symbs[:-5] + symb
        df = read_JSON(url_symb)

        # Ensure dates are the same + drop duplicate dates:
        df.index = pd.to_datetime(df.datahora_cotacao).dt.normalize()
        df = df[~df.index.duplicated(keep='first')]

        # Add returns to the original DataFrame (table) to have all together:
        prices_df = prices_df.merge(df.cotacao, how='left', left_index=True, right_index=True)
        prices_df.rename({prices_df.columns[-1]: symb}, axis=1, inplace=True)

        # Filter out symbols with less than 50% of price data:
        prices_df = prices_df.loc[:, (prices_df.count() > prices_df.count().max() / 2)]

    prices_df = prices_df.astype(float)  # Ensure prices are numeric

    return prices_df

# Markowitz Efficient Allocations Function:
def markowitz_model(symbols, cov, data_df, max_vol=None, title="Geral"):
    # Empty DataFrame to store portfolio metrics:
    portfolio = pd.DataFrame(None, index=list(symbols) + ['Retorno', 'Volatilidade', 'Beta'])

    weights = None  # Initial value to ensure max_vol is not too low

    # Loop to fix max vol incrementally if it is too low:
    while type(weights) == type(None):

        # Set allocations for each symbol variable to solve in optimization:
        allocations = cp.Variable(len(symbols))

        # Set Max allocations and Returns variables:
        max_allocs = data_df.Max_Allocations.values
        ret = data_df.Returns.values

        # Set risk variable of variance to be minimized + general constraints:
        var = cp.quad_form(allocations, cov)
        cons = [cp.sum(allocations) == 1, allocations >= 0]

        # Markowitz Optimization: Finding minimum risk (volatility) allocations with returns:
        obj = cp.Minimize(var - ret.T @ allocations)

        # General portfolio only has 2 constraints and does not use returns:
        if max_vol == None:
            obj = cp.Minimize(var)

        else:
            # Add volatility constraint in the form of variance:
            max_var = (max_vol / np.sqrt(252)) ** 2
            cons += [var <= max_var]

            # Add allocation constraints for each symbol:
            for i in range(len(max_allocs)):
                cons += [allocations[i] <= max_allocs[i]]

        # Find allocations with minimization objective and constraints above:
        prob = cp.Problem(obj, cons)
        prob.solve()

        # If allocations are NoneType still, max vol needs to be increased:
        if type(allocations.value) == type(None):
            max_vol += 0.002

        # If not, weights can finally not be None anymore to move forward:
        else:
            weights = allocations.value

    # Round weights and set variable to return it:
    weights = np.array(weights.round(3))

    # Calculate Portfolio Volatility, Return, and Beta:
    vol = np.sqrt(var.value) * np.sqrt(252)
    year_ret = ret @ weights
    beta = data_df.Beta.values @ weights

    port_info = np.append(weights, [year_ret, vol, beta])

    # Add metrics to DataFrame:
    portfolio[title] = port_info

    return portfolio

# Function to get other necessary data: Max Allocations, Max Volatility
# and portfolio metrics (Returns, Beta, covariance):
def get_data():
    # Get symbols of assets from JSON data url:
    url = 'https://dracarinvest.com.br/Software/Portfolio/get_ativos'
    ativos_df = read_JSON(url)
    symbols = ativos_df.codigo_ativo.unique()  # Avoid duplicate symbols

    # Get prices of symbols:
    prices = get_prices(symbols, url)

    # Get max allocations and returns for each symbol:
    data = pd.DataFrame(None, index=prices.columns)  # DataFrame to store info
    max_aloc_lst = []  # List to store max allocations
    ret_lst = []  # List to store returns
    beta_lst = []  # List to store betas

    # Loop to get each symbol's information:
    for symb in data.index:
        # Add up allocations to get max allocation into list:
        alloc_max = ativos_df[ativos_df['codigo_ativo'] == symb]['alocacao'].astype(float).sum()
        max_aloc_lst.append(alloc_max)

        # Get returns for each symbol into list:
        symb_ret = ativos_df[ativos_df['codigo_ativo'] == symb]['retorno'].astype(float).iloc[0]
        ret_lst.append(symb_ret)

        # Get betas for each symbol into list:
        beta = ativos_df[ativos_df['codigo_ativo'] == symb]['beta'].astype(float).iloc[0]
        beta_lst.append(beta)

    # Add lists to DataFrame to store max allocations, returns, beta:
    data['Max_Allocations'] = max_aloc_lst
    data['Returns'] = ret_lst
    data = data / 100
    data['Beta'] = beta_lst

    # Get max volatilities:
    url_vols = url[:-10] + 'get_vol_perfil'
    max_vols = read_JSON(url_vols)
    max_vols = max_vols.astype(float) / 100  # Ensure it is numeric for calculations

    # Calculate log daily returns + covariance of returns:
    log_ret = np.log(prices) - np.log(prices.shift(1))  # Log returns (Daily)
    cov = log_ret.cov()  # Covariance of returns

    return data, max_vols, cov

def efficient_allocations():
    # Get necessary info for allocations:
    data, max_vols, cov = get_data()

    # List of desired portfolios and initial General one to store all:
    ports_lst = ['Conservador', 'Moderado', 'Sofisticado']
    portfolios = markowitz_model(data.index, cov, data)

    # Loop to get each portfolio from the list and concatenate to general one:
    for port in ports_lst:
        # Get portfolio allocations and metrics:
        temp_port = markowitz_model(data.index, cov, data, max_vols[port].values, port)

        # Add portfolio to original DataFrame:
        portfolios = pd.concat([portfolios, temp_port], axis=1)

    # Format/standardize data and place it as json:
    portfolios[:-1] *= 100
    portfolios_json = portfolios.to_json()

    return portfolios_json