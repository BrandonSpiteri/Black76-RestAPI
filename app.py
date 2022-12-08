#imports libraries
from flask import Flask, request, jsonify, make_response, abort
from flask_restful import Resource, Api
import json
import numpy as np
from scipy.stats import norm
from datetime import date, datetime

#define Flask server
app = Flask(__name__)
#define API
api = Api(app)

'''
Define 'Data' as the list which stores local database, that is, 
    dictionary elements with the option name as key, and market data as values
    
'''
Data =[]

'''
Define a list 'expected_json_keys' containing the market data keys
    expected in the POST request when adding new options to the local database

'''
expected_json_keys = ['type', 'f', 'x', 'expiry', 'r', 'v']


'''
Route home directory requests to 'index' function  

Returns 
-------
    All elements in the local database
    
Can be accessed through: http://127.0.0.1:5000/
'''
@app.route("/")
def index():
    return jsonify({'Local Database': Data})


'''
Process Flask server 404 errors using the 'error_handler' function

Returns 
-------
    Error message
'''
@app.errorhandler(404)
def error_handler(e):
    return jsonify(error=e), 404


class preprocess_post_body():
    
    """
    Class to preprocess POST body sent to REST API

    ...

    Attributes
    ----------
    body : dictionary
        POST body message containing the:
            'type' - option type 
            'f' : the initial underlying future option price
            'x' : strike price at which option will be executed in the future
            'expiry' = contract expiry date
            'r' = continuously compounded risk free interest rate
            'v' = implied volatility for the underlying forward price
        
        
    name : str
        Option name in the format AA-MMMYY-{C/P}-1111
        where:
        AA - represents the product name e.g. BB for Brent Cruid Oil Futures
        MMMYY - represents the Contract Month e.g. JAN24
        {C/P} - can take a value of 'C' or 'P' depending on whether the option is a call of put
        1111 - can be any integer value representing the strike price e.g. 100
        An example of a name can be: BB-JAN24-C-100 (Brent Cruid Oil Futures, with a contract month
            of January 2024, being a call, with a strike price of $100
    
    option_type: str
        option_type : str {'c', 'p'}
        Specifies if a call 'c' or 'put' option is being valued
    
    t = float
        Maturity period (in years), that is, years left until option expires
        
    integral: float
        Any value that is continuous 
    
    expiry_date: str
        Contract expiry date in the format 'YYYY-MM-DD'
    
    
    Methods
    -------
    
    _check_json_missing_keys(body)
        Checks if the POST has the required keys
        
    _check_if_option_already_exists(name)
        Checks if the option already exists in the local database
        
    _is_valid_option_type(option_type)
        Checks if the POST option type is either 'c' or 'p' (call or put)
    
    _is_valid_expiry_date(expiry_date)
        Checks if the POST expiry date is in the YYYY-MM-DD date format
        
    _is_valid_float(integral)
        Checks if the passed variable is continuous and greater than 0
    
    _calculate_t(expiry_date)
        Calculate the maturity period (in years)
        
    """
    
    def _check_json_missing_keys(self, body):
        '''
        Function which checks if the POST has the keys required to calculate the option present value
        
        Parameters
        ----------
        body : dictionary
            POST body message containing the:
                'type' - option type 
                'f' : the initial underlying future option price
                'x' : strike price at which option will be executed in the future
                'expiry' = contract expiry date
                'r' = continuously compounded risk free interest rate
                'v' = implied volatility for the underlying forward price
        
        Raises
        ------
        abort 
            Returns a 404 error if the POST body is empty
        
            Returns a 404 error if any of the following body keys are not found in the POST message
                {'type', 'f', 'x', 'expiry', 'r', 'v'}, together with the missing keys
        
        '''
        if not body:
            error_msg = "Empty POST body"
            abort(404, description=error_msg)
            
        body_keys=list(body.keys())

        missing_keys = list(set(expected_json_keys) - set(body_keys))

        if len(missing_keys)>0:
            error_msg = "Found missing body keys: "+ str(missing_keys)
            abort(404, description=error_msg)
    
    def _check_if_option_already_exists(self,name):
        '''
        Function which checks if the option already exists in the local database
        
        Parameters
        ----------
        name : str
            Option name in the format AA-MMMYY-{C/P}-1111
            where:
            AA - represents the product name e.g. BB for Brent Cruid Oil Futures
            MMMYY - represents the Contract Month e.g. JAN24
            {C/P} - can take a value of 'C' or 'P' depending on whether the option is a call of put
            1111 - can be any integer value representing the strike price e.g. 100
            An example of a name can be: BB-JAN24-C-100 (Brent Cruid Oil Futures, with a contract month
                of January 2024, being a call, with a strike price of $100
        
        Raises
        ------
        abort 
            Returns a 404 error if the option already exists in the local database
        
        '''
        for index in range(len(Data)):
            for key in Data[index]:
                if key == name:
                    error_msg = "Option already exists: "+ str(name)
                    abort(404, description=error_msg)
        
    def _is_valid_option_type(self, option_type):
        '''
        Function which checks if the option type is valid, that is, either 'c' or 'p' (call or put)
        
        Parameters
        ----------
        option_type : str {'c', 'p'}
            Specifies if a call 'c' or 'put' option is being valued
    
        Raises
        ------
        abort 
            Returns a 404 error together with the POST option type if the option type is not 'c' or 'p'
        
        '''
        if ((option_type != 'c') and (option_type != 'p')):
            error_msg = "Option type can only be set to \'c' or 'p'. Entered: "+ str(option_type)
            abort(404, description=error_msg)
        return option_type
    
    def _is_valid_expiry_date(self, expiry_date):
        '''
        Function which checks if the option expiry date is in the valid YYYY-MM-DD date format
        
        Parameters
        ----------
        expiry_date: str
            Contract expiry date in the format 'YYYY-MM-DD'
    
        Raises
        ------
        abort 
            Returns a 404 error together with the POST date if the expiry date is not in the format 'YYYY-MM-DD'
        
        '''
        
        try:
            datetime.strptime(expiry_date, '%Y-%m-%d').date()
            return expiry_date
        except:  
            error_msg = "Expiry date in expected \'%Y-%m-%d\' format. Entered: "+ str(expiry_date)
            abort(404, description=error_msg)
    
    def _is_valid_float(self, integral):
        '''
        Function which checks if the 'f', 'x','r' and'v' key values in the POST are continuous variables
            and greater than 0
        
        Parameters
        ----------
        integral: float
            Any variable in the POST amongst 'f', 'x','r' and'v'
    
        Raises
        ------
        abort 
            Returns a 404 error together with the POST value if the passed variable is not continuous
                and/or not greater than 0
        
        '''
        
        try:
            float_casted_integral=float(integral)
            if float_casted_integral<0:
                error_msg = "Input must be greater than zero. Entered: "+ str(integral)
                abort(404, description=error_msg)
            return float_casted_integral 
        except:
            error_msg = "Input must be continuous variables. Entered: "+ str(integral)
            abort(404, description=error_msg)
            
    
    def _calculate_t(self, expiry_date):
        '''
        Function which calculates the Maturity period (in years), that is, years left until option expires
            from current date
        
        Parameters
        ----------
        expiry_date: str
            Contract expiry date in the format 'YYYY-MM-DD'
    
        Raises
        ------
        abort 
            Returns a 404 error together with the expiry date if the maturity period cannot be calculated
        
        '''
        try:
            today = date.today()
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()

            time_to_maturity = ((expiry_date - today).days) + 1
            return round(max(time_to_maturity,0)/365, 5)
        except:
            error_msg = "Cannot calculate maturity period. Entered: "+ str(expiry_date)
            abort(404, description=error_msg)

class rest_api_handler(preprocess_post_body, Resource):
    
    """
    Class which handles REST API requests using Flask framework

    Class 'rest_api_handler' inherts the properties and methods from its parent classes 'Resource' and 'preprocess_post_body'

    ...

    Attributes
    ----------
  
    name : str
        Option name in the format AA-MMMYY-{C/P}-1111
        where:
        AA - represents the product name e.g. BB for Brent Cruid Oil Futures
        MMMYY - represents the Contract Month e.g. JAN24
        {C/P} - can take a value of 'C' or 'P' depending on whether the option is a call of put
        1111 - can be any integer value representing the strike price e.g. 100
        An example of a name can be: BB-JAN24-C-100 (Brent Cruid Oil Futures, with a contract month
            of January 2024, being a call, with a strike price of $100
    
    Parameters
    ----------
    option_type : str {'c', 'p'}
        Specifies if a call 'c' or 'put' option is being valued
        
    f : float
        The initial underlying future option price
    
    x : float
        Strike price at which option will be executed in the future
    
    expiry_date: str
        Contract expiry date in the format 'YYYY-MM-DD'
        
    t = float
        Maturity period (in years), that is, years left until option expires
        
    r = float
        Continuously compounded risk free interest rate
        
    v = float
        Implied volatility for the underlying forward price
        
    
    Methods
    -------
    
    get(name)
        Handles GET requests to read options from local database
    
    post(name)
        Handles POST requests to create options in local database
    
    delete(name)
        Handles DELETE requests to delete options from local database
        
    """
    
    #print if a name exists in list 
    def get(self, name):
        '''
        Function handles GET requests. 
        
            
        Function can be called by sending a GET request to http://127.0.0.1:5000/{name}
            where name is the option name
        
        Parameters
        ----------
        name : str
            Option name in the format AA-MMMYY-{C/P}-1111
            where:
            AA - represents the product name e.g. BB for Brent Cruid Oil Futures
            MMMYY - represents the Contract Month e.g. JAN24
            {C/P} - can take a value of 'C' or 'P' depending on whether the option is a call of put
            1111 - can be any integer value representing the strike price e.g. 100
            An example of a name can be: BB-JAN24-C-100 (Brent Cruid Oil Futures, with a contract month
                of January 2024, being a call, with a strike price of $100
        
        Returns
        ----------
        
        Returns the requested option together with the present value (pv) as well as 
            the stored market data
            
        Raises
        ------
        
        Returns "option not found" message together with the requested option name if option not found
            in local database
        
        '''
        
        #Loop through Data list and if the key of any dictionary matches the GET name, return the dictionary 
        #content
        for index in range(len(Data)):
            for key in Data[index]:
                if key == name:
                    values = Data[index][key]                    
                    return {name:values}

                    
        return {name:"option not found"}
        
    
    #populate the list
    def post(self,name): 
        '''
        Function handles POST requests. The function appends new options together with 
            market data to the local database ('Data' list)
        
            
        Function can be called by sending a POST request to http://127.0.0.1:5000/{name}
            where name is the option name
            
        A JSON formatted body needs to attached to the POST request to populate market data
            to the option in the local database as shown in the example:
                {
                  "type":"c",
                  "f":2006,
                  "x":2100,
                  "expiry":"2023-01-05",
                  "r": 0.051342,
                  "v":0.35
                }
        
        Parameters
        ----------
        name : str
            Option name in the format AA-MMMYY-{C/P}-1111
            where:
            AA - represents the product name e.g. BB for Brent Cruid Oil Futures
            MMMYY - represents the Contract Month e.g. JAN24
            {C/P} - can take a value of 'C' or 'P' depending on whether the option is a call of put
            1111 - can be any integer value representing the strike price e.g. 100
            An example of a name can be: BB-JAN24-C-100 (Brent Cruid Oil Futures, with a contract month
                of January 2024, being a call, with a strike price of $100
        
        Returns
        ----------
        
        Returns a JSON message if option was added successfully
            
        
        '''
        
        body = request.json
        self._check_json_missing_keys(body)
        self._check_if_option_already_exists(name)

        #populate self
        self.option_type = self._is_valid_option_type(body['type'])
        self.f = self._is_valid_float(body['f'])
        self.x = self._is_valid_float(body['x'])
        self.expiry = self._is_valid_expiry_date(body['expiry'])
        self.r = self._is_valid_float(body['r'])
        self.v = self._is_valid_float(body['v'])
        self.t = self._calculate_t(self.expiry)
        self.pv = self.price()
              
        #append self to local database    
        temp = {name:self.__dict__}
        Data.append(temp)
        
        return make_response(jsonify({"message": "Added "+name+" successfully"}), 200)
    
    def delete(self,name):
        '''
        Function handles Delete requests. The function deletes existing options together with 
            market data from the local database ('Data' list)
        
            
        Function can be called by sending a DELETE request to http://127.0.0.1:5000/{name}
            where name is the option name
            
        
        Parameters
        ----------
        name : str
            Option name in the format AA-MMMYY-{C/P}-1111
            where:
            AA - represents the product name e.g. BB for Brent Cruid Oil Futures
            MMMYY - represents the Contract Month e.g. JAN24
            {C/P} - can take a value of 'C' or 'P' depending on whether the option is a call of put
            1111 - can be any integer value representing the strike price e.g. 100
            An example of a name can be: BB-JAN24-C-100 (Brent Cruid Oil Futures, with a contract month
                of January 2024, being a call, with a strike price of $100
        
        Returns
        ----------
        
        Returns a JSON message if option was added successfully
           
        Raises
        ------
        
        Returns "option not found" message together with the requested option name if option to be deleted
            is not found in local database
        
        
        '''
        #Loop through Data list and if the key of any dictionary matches the GET name, 
        # delete the option from the local database
        delete =0
        for ind,x in enumerate(Data):
            for key in Data[ind]:
                if key == name:
                    Data.pop(ind)
                    return {'Deleted Option':name}
                    delete =1
        if delete ==0:
            return {name:"option not found"}

            
class black_76(rest_api_handler):
    '''
    Class to calculate Present Value of options using Black-76 formula
    
    
    Class 'black_76' inherts the properties and methods from its parent class 'rest_api_handler'
    
    Methods
    -------
    _d1()
        Returns probability factor d1
    
    _d2()
        Returns probability factor d2
     
    _call_value()
        Return the present value of the call option
        
    _put_value()
        Return the present value of the put option
    
    price()
        Return the present value of the option based on the option type ('c' or 'p')
      
    
    '''
    def __init__(self):
        pass
    
    def _d1(self):
        '''
        Function which returns the probability factor d1
        
        '''
        return (np.log( self.f/self.x ) + ( self.t* self.v**2 )/2)/ (self.v * np.sqrt(self.t) )

    def _d2(self):
        '''
        Function which returns the probability factor d2
        
        '''
        return self._d1() - (self.v*np.sqrt(self.t))

    def _call_value(self):
        '''
        Function which returns the present value of the call option
        
        '''
        return round( np.exp(-self.r*self.t) * (self.f*norm.cdf(self._d1())-self.x*norm.cdf(self._d2())) ,2)
    
    def _put_value(self):
        '''
        Function which returns the present value of the put option
        
        '''
        return round( np.exp(-self.r*self.t) * (self.x*norm.cdf(-self._d2())-self.f*norm.cdf(-self._d1())) ,2)
    
    def price(self):
        '''
        Function which returns the present value of the option
        
        Raises 
        -------
        abort 
            Returns a 404 error together with a description if the option type instance is not 'c' or 'p' (call or put)
        
        '''
        if self.option_type =='c':
            return self._call_value()
        elif self.option_type =='p':
            return self._put_value()
        else:
            error_msg = "Unknown Option Type. Entered: "+ str(self.option_type)
            abort(404, description=error_msg)
        
            
#Route Option names to class 'black_75'
#Add resource to Flask API
api.add_resource(black_76,'/<string:name>')

#Run app on a Flask server
if __name__ == "__main__":
    app.run(debug=True)