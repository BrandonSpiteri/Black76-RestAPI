# Rest API application for Option pricing using the Black-76 Formula

A RestAPI web application which:
1. Stores options market data in a local database using PUT requests
2. Calculate the present value on options using Black-76 formula
3. Handle GET requests to retrieve uploaded market data as well as the calculated present value
4. Hadnle DELETE requests to delete options from local database


# Black (1976) Model 

The Black (1976) model is used to evaluate the present value of options and can be used for European options on commodities, future contract as well as bonds. 

The model aims to give an approximation to the current present value of an option given that it relies on a number of assumptions, including:
1. Transaction and profit taxes are ignored
2. The risk free interest rate and volatility are known throughout the life of the option
3. Future prices are log-normally distributed

The Black (1976) models states that the price for an option can be derived as follows:

$$ \text{Call Option Price} = e^{-r.t} \[ \text{fN(d} _{1} )- \text{xN(d} _{2}) \]$$

$$ \text{Put Option Price} = e^{-r.t} \[ \text{xN(-d} _{2} )- \text{fN(-d} _{1}) \]$$

Where:

$$ \text{d} _{1} =  \frac{  \text{ln(f/x) + (v}^2 \text{/2) . t}    } {v\sqrt{t}}   $$

$$ \text{d} _{2} =  \text{d} _{1} - v\sqrt{t}   $$


f = Future option price

$$ \text{x = Strike price at which option will be executed in the future} $$

$$ \text{t = Maturity period (in years), that is, years left until option expires} $$

$$ \text{r = Continuously compounded risk free interest rate} $$

$$ \text{v = Implied volatility for the underlying forward price} $$


# Model Training
A moving window mechanicsm is used, which 200 instances are used as training set, and the next day (d) is predicted. The window moves by one day, and predicts the following day (d+1). 

# Models Trained
1. Linear Regression
2. ElasticNet
3. SGDRegressor

# Results
| Model  | R2_Score(%) | RMSE | Note |
| ------------- | ------------- | ------------- | ------------- |
| Linear Regression	  | 36.01  | 28874.251778	| Basic Dataframe | 
| Linear Regression	| 75.56	| 17845.382889	| Enhanced Dataframe |
| Elastic Net	| 74.15	| 18353.240225	| Enhanced Dataframe |
| SGD Regressor	| 74.29	| 18301.823954 |	Enhanced Dataframe |

# Libraries
matplotlib==3.2.1 

