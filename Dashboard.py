
from datetime import date, timedelta
from logging import exception

# Calculate today's and 30-days-ago dates
end_date = date.today()
start_date = end_date - timedelta(days=30)

# API URL constructed to fetch exchange rates from USD to multiple currency over a given date range
url = f"https://api.frankfurter.app/{start_date}..{end_date}?from=USD&to=EUR,INR,JPY,GBP,AUD"

import requests

# Package the request, send the request, and catch the response: response
response = requests.get(url)
# Decode the JSON data into a dictionary: response_json
response_json = response.json()


import pandas as pd

# response_json is converted into a Dataframe called Currencydata_pd.
Currencydata_pd = pd.DataFrame.from_dict(response_json['rates'], orient='index')

# Reset the Dataframe index and then rename the index column as Date.
Currencydata_pd = Currencydata_pd.reset_index().rename(columns={'index': 'Date'})

# Convert Date column to datetime format.
Currencydata_pd['Date'] = pd.to_datetime(Currencydata_pd['Date'])

# Sort dataframe by Date in ascending order
Currencydata_pd = Currencydata_pd.sort_values(by='Date')

# Get recent exchange rate by sorting data by date in descending order and fetching the 1st row
latest_rate = Currencydata_pd.sort_values('Date', ascending=False).iloc[0]

# Set font preference as a CSS style string.
font_family = "'Roboto', 'Helvetica Neue', Helvetica, Arial, sans-serif"

# --- Flag icons ---
flag_urls = {
    'USD': 'https://flagcdn.com/us.svg',
    'AUD': 'https://flagcdn.com/au.svg',
    'EUR': 'https://flagcdn.com/eu.svg',
    'GBP': 'https://flagcdn.com/gb.svg',
    'INR': 'https://flagcdn.com/in.svg',
    'JPY': 'https://flagcdn.com/jp.svg'
}


# Import OLS from statsmodels for regression
from statsmodels.formula.api import ols

import plotly.express as px
import dash
from dash import html, dcc
app = dash.Dash()

def predict_future_rates_ols(currency, days_ahead_list=[7, 15]):
    """
    This function predicts what the exchange rate for a currency might be in the future.
    How it works:
    1. It takes past exchange rate data for the currency from `Currencydata_pd`.
    2. It finds a trend line using a method called Ordinary Least Squares (OLS) regression.
    3. It uses that trend line to predict the exchange rate for certain days in the future.
    :param currency:The name of the column in the data that has the currency's rates.
    :param days_ahead_list:How many days ahead you want predictions for.
    :return:dict: A dictionary where:
            - The keys are the future dates.
            - The values are the predicted rates for those dates.
    """
    predictions = {}
    try:
        df = Currencydata_pd[['Date', currency]].dropna().copy()
        df['Date_ordinal'] = df['Date'].map(pd.Timestamp.toordinal)
        formula = f"{currency} ~ Date_ordinal"
        model = ols(formula=formula, data=df).fit()
        last_date_ordinal = df['Date_ordinal'].max()


        for d in days_ahead_list:
            future_date_ordinal = last_date_ordinal + d
            pred = model.predict({'Date_ordinal': future_date_ordinal})[0]
            pred_date = pd.Timestamp.fromordinal(int(future_date_ordinal))
            predictions[pred_date] = pred

    except Exception as e:
        print(f"Error predicting future rates for {currency}: {e}")


    return predictions


from dash.dependencies import Input, Output, State

app.layout = html.Div(children= [

html.Div([
    html.Div([
        html.Div([

            html.Div([
                html.Div([
                html.Img(
                src='https://img.icons8.com/ios-filled/100/ffffff/currency-exchange.png',
                style={
                    'height': '60px',
                    'marginRight': '15px',
                }
                ),
                html.H1('RateWatch', style={
                    'margin': '0',
                    'color': '#FFFFFF',
                    'fontWeight': '700',
                    'fontSize': '2.8rem',
                    'lineHeight': '1.2',
                }),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),

                html.I('From Dollars to Destinations - We’ve Got You Covered', style={
                    'color': '#BDC3C7',
                    'fontSize': '1.2rem',
                    'fontWeight': '400',
                })
            ])
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'gap': '10px'
        })




    ], style={
        'padding': '30px 20px',
        'backgroundColor': '#2C3E50',
        'borderRadius': '12px',
        'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.3)',
        'marginBottom': '30px',
        'textAlign': 'center',
    })
]),



    html.Div([
    html.Div([
    html.Div([
    html.Div([
        html.Img(src=flag_urls['USD'], style={'width': '25px', 'verticalAlign': 'middle', 'padding-left': '5px'}),
        html.Label('USD', style={'paddingRight': '200px', 'display': 'inline-block', 'padding-left': '5px'}),
        dcc.Input(id='usd_input', type='number', placeholder='$ 0.00',
                  style={'width': '100px', 'padding': '8px'})
    ], style={'marginBottom': '10px'}),

        html.Div([
            dcc.Dropdown(
                id='currency_dd',
                options=[
                    {'label': html.Span([
                        html.Img(src=flag_urls[c], style={'width': '20px', 'marginRight': '5px'}),
                        c
                    ], style={'display': 'flex', 'alignItems': 'center'}), 'value': c}
                    for c in ['AUD', 'EUR', 'GBP', 'INR', 'JPY']
                ],
                placeholder="Select currency",
                value='EUR',
                style={'width': '200px', 'display': 'inline-block', 'marginRight': '70px'}
            ),
            dcc.Input(id='converted_output', type='number', readOnly=True,
                      style={'width': '100px', 'padding': '8px',
                            'display': 'inline-block'})
        ],style={
            'display': 'flex',
            'alignItems': 'center',
            'marginTop': '10px'
            }),
], style= {'marginBottom':'20px'}),

        html.Div([
            html.H3('Prediction & Recommendation',
                    style={'color': '#2C3E50', 'fontWeight': '600', 'fontFamily': font_family, 'textDecoration':'underline'}),
            html.Div(id='recommendation', style={
                'fontWeight': 'bold',
                'color': '#34495e',
                'fontSize': '1.1rem',
                'whiteSpace': 'pre-line',
                'padding': '10px',
            })
        ], style={
            'padding': '20px',
            'border': '1px solid #ccc',
            'borderRadius': '8px',
            'width': '112%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'backgroundColor': 'white',
            'boxShadow': '2px 2px 8px rgba(0,0,0,0.1)',
            'height': 'fit-content',
        })
]),
    # Currency Graph

    html.Div([
        html.H3('Currency Trends (Past 30 Days)', style={'color': '#2C3E50', 'fontWeight': '600'}),
        dcc.Graph(id='currency_graph')
    ],
        style={
            'padding': '20px',
            'border': '1px solid #ccc',
            'borderRadius': '8px',
            'width': '55%',
            'display': 'inline-block',
            'marginLeft': '10%',
            'verticalAlign': 'top'
        })
        ], style={'display': 'flex',
        'alignItems': 'flex-start'})
], style={
    'fontFamily': font_family,
    'backgroundColor': '#F4F6F8',
    'minHeight': '100vh',
    'padding': '40px 20px'
})


@app.callback(
    Output('converted_output', 'value'),
    Output('currency_graph', 'figure'),
    Output('recommendation', 'children'),
    Input('currency_dd', 'value'),
    Input('usd_input', 'value')
)


def update_currency_graph(currency_selected, usd_amount):
    """
       Creates an exchange rate chart, converts USD to the selected currency,
       and gives buy/wait recommendations based on future rate predictions.

       Parameters:
        currency_selected (str): The name of the currency to convert to and plot.
        usd_amount (float): The amount in USD to convert.

        Returns:
        tuple: (converted amount, chart figure, recommendation text)
       """
    #converted_amt variable is created for storing the conversion rate result.

    converted_amt = 0.0
    try:
        if usd_amount is not None and currency_selected:
            rate = latest_rate[currency_selected]
            converted_amt = round(usd_amount * rate, 2)

            fig = px.line(Currencydata_pd, x='Date', y=currency_selected,
                      title=f"{currency_selected} Exchange Rate (USD Base)",
                      markers=True)
            fig.update_layout(yaxis_title="Rate", xaxis_title="Date")

        else:
            fig = px.line(title="Select a currency and enter an amount")

    # Linear regression predictions for 7th and 15th day from last date

        if currency_selected:
            latest = Currencydata_pd[currency_selected].iloc[-1]
            preds = predict_future_rates_ols(currency_selected, days_ahead_list=[7, 15])
            recs = []
            for dt, pred_rate in preds.items():
                if pred_rate > latest:
                    message = html.Span([
                        f"{dt.date()}: Predicted rate {pred_rate:.4f} — ",
                        html.Span("Better to wait.", style={'fontStyle': 'italic', 'color': 'red'})
                    ])
                    recs.append(html.Li(message))
                else:
                    message = html.Span([
                        f"{dt.date()}: Predicted rate {pred_rate:.4f} — ",
                        html.Span("Convert now.", style={'fontStyle': 'italic','color': 'green'})
                    ])
                    recs.append(html.Li(message))

            recommendation_text = html.Ul([html.Li(r) for r in recs])

        else:
            recommendation_text = "Please select a currency to see recommendations."

    except Exception as e:
        print('Unexpected error occured:', e)
        fig = px.line(title ='An error occured')
        recommendation_text = 'Could not generate recommendation due to an error'

    return converted_amt, fig, recommendation_text

# Set the app to run
if __name__ == '__main__':
    app.run(debug=False)