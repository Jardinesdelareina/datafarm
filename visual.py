import pandas as pd
import datetime
import plotly.graph_objects as go
import plotly.graph_objs as gos
from test import SYMBOL

time_now = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
data_file = f'{SYMBOL}.csv'

df = pd.read_csv(data_file) 

chart = go.Scatter(
    x=df.Time,
    y=df.Price,
    mode='lines',
    line=dict(width=1),
    marker=dict(color='blue')
)

layout = go.Layout(
    title='Тиковый график',
    yaxis=dict(
        title='Цена',
        side='right',
        showgrid=False,
        zeroline=False
    ),
    xaxis=dict(
        title='Время',
        showgrid=False,
        zeroline=False
    ),
    margin=gos.layout.Margin(
        l=40,
        r=0,
        t=40,
        b=30
    )
)

data = [chart]
fig = go.Figure(data=data, layout=layout)
fig.write_image(f"telegram/images/{SYMBOL}-{time_now}.png")
