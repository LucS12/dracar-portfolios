#Necessary packages/modules:
from fastapi import FastAPI
import markowitz

#Create api instance:
api = FastAPI()

#Create endpoint for retrieving API data (efficient portfolios):
@api.get('/portfolios')
async def get_portfolios():
    #Get portfolios from markowitz function:
    portfolios = markowitz.efficient_allocations()

    return portfolios
