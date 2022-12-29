#Necessary packages:
from flask import Flask, request, jsonify
import allocation_model

#Run the web app:
app = Flask(__name__)
app.config['SECRET_KEY'] = 'aaakkksllsjueujf'

@app.route("/")
def index():
    return "go to https://dracar-portfolios.onrender.com/get-efficient-portfolios"

#Route for the get url to retrieve the efficient portfolios:
@app.route('/get-efficient-portfolios', methods=['GET'])
def portfolios():
    if request.method == 'GET':
        portfolios_json = allocation_model.efficient_allocations()

        return portfolios_json
