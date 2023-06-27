import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import locale
from functions import *

st.set_page_config(
    page_title="Gitcoin Rounds",
    page_icon="📊",
    layout="wide",
)

round_name = st.radio("Select Round ", ('Beta', 'Community'))

if round_name == 'Beta':
    chain_id = '1'

    st.title('Gitcoin Beta Rounds')
    st.write('The Gitcoin Grants Program is a quarterly initiative that empowers everyday believers to drive funding '
             'toward what they believe matters, with the impact of individual donations being magnified by the use of '
             'the [Quadratic Funding (QF)](https://wtfisqf.com) distribution mechanism.')
    st.write('You can donate to projects in the Beta Round from April 25th 2023 12:00 UTC to May 9th 2023 23:59 UTC.')
    st.write('👉 Visit [grants.gitcoin.co](https://grants.gitcoin.co) to donate.')

elif round_name == 'Community':
    chain_id = '10'

    st.title('Gitcoin Community Rounds')


data_load_state = st.text('Loading data...')
chain_data = load_chain_data(chain_id)
data_load_state.text("")

st.subheader(round_name + ' Rounds Summary')
# create two-column metrics. One with the sum of votes and the other with the amountUSD
col1, col2, col3 = st.columns(3)
col1.metric("Total Votes", '{:,.0f}'.format(chain_data['votes'].sum()))
col2.metric('Total Contributed', '${:,.2f}'.format(chain_data['amountUSD'].sum()))
col3.metric('Total Rounds', '{:,.0f}'.format(chain_data['round_id'].count()))

if chain_data['round_id'].count() > 1:
    # create color map
    color_map = create_color_map(chain_data)
    # create two-column charts. One with the sum of votes and the other with the amountUSD
    col1, col2 = st.columns(2)
    fig = get_USD_by_round_chart(chain_data, color_map)
    col1.plotly_chart(fig, use_container_width=True)
    fig = get_contributions_by_round_bar_chart(chain_data, color_map)
    col2.plotly_chart(fig, use_container_width=True)
    chain_data_display = chain_data[['name', 'votes', 'amountUSD']]

    st.subheader("Round Details")
    # selectbox to select the round
    option = st.selectbox(
        'Select Round',
        chain_data['name'])
else:
    option = chain_data['name'].values[0]
    st.subheader("Round Details:")
    st.subheader(option)

data_load_state = st.text('Loading data...')
# load round data for the option selected by looking up the round id with that name in the chain_data df
round_id = chain_data[chain_data['name'] == option]['round_id'].values[0]
dfp = load_round_projects_data(chain_id, round_id)
dfv = load_round_votes_data(chain_id, round_id)
data_load_state.text("")

dfv = pd.merge(dfv, dfp[['project_id', 'title', 'status']], how='left', left_on='projectId', right_on='project_id')

col1, col2 = st.columns(2)
total_usd = dfv['amountUSD'].sum()
col1.metric('Total USD', '${:,.2f}'.format(total_usd))
total_donations = (dfv['amountUSD'] > 0).sum()
col1.metric('Total Donations',  '{:,.0f}'.format(total_donations))
total_by_donor = dfv.groupby('voter')['amountUSD'].sum()
nonZero_donors = (total_by_donor > 0).sum()
col1.metric('Total Donors',  '{:,.0f}'.format(nonZero_donors))

col1.metric('Total Projects',  '{:,.0f}'.format(len(dfp)))

col2.write('## Projects')
# write projects title, votes, amount USD, unique contributors
col2.write(dfp[['title', 'votes', 'amountUSD', 'uniqueContributors']])


# display the chart
# fig_grants = get_grants_bar_chart(dfv)
# st.plotly_chart(fig_grants, use_container_width=False)

starting_blockNumber = 17123133
ending_blockNumber = dfv['blockNumber'].max()
starting_blockTime = datetime.datetime(2023, 4, 25, 12, 13, 35)

dfb = create_block_times(starting_blockNumber, ending_blockNumber, starting_blockTime)
# merge the block times with the votes data
dfv = pd.merge(dfv, dfb, how='left', on='blockNumber')
# graph of the amountUSD grouped by utc_time hour
#st.subheader('Amount USD by Hour and day of utc_time')
dfv_count = dfv.groupby([dfv['utc_time'].dt.strftime('%m-%d-%Y %H')])['id'].nunique()
# set the index to be the utc_time column
dfv_count.index = pd.to_datetime(dfv_count.index)
# fill in missing hours with 0
dfv_count = dfv_count.reindex(pd.date_range(start=dfv_count.index.min(), end=dfv_count.index.max(), freq='H'), fill_value=0)
fig = px.bar(dfv_count, x=dfv_count.index, y='id', labels={'id': 'Number of Votes'}, title='Number of Contributions over Time')
st.plotly_chart(fig, use_container_width=True)
