#Necessary packages:
from flask import Flask, request, jsonify
import allocation_model

#Run the web app:
app = Flask(__name__)
app.config['SECRET_KEY'] = 'aaakkksllsjueujf'

#Route for the get url to retrieve the efficient portfolios:
@app.route('/get-efficient-portfolios', methods=['GET'])
def index():
    if request.method == 'GET':
        portfolios_json = allocation_model.efficient_allocations()

        return portfolios_json

if __name__ == "__main__":
    app.run()
