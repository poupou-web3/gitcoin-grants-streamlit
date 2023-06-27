import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime
import plotly.graph_objs as go

CHAIN_URL = 'https://indexer-grants-stack.gitcoin.co/data'


@st.cache_data(ttl=3000)
def load_chain_data(chain_id):
    json_round_url = '/'.join([CHAIN_URL, chain_id, 'rounds.json'])
    try:
        response = requests.get(json_round_url)
        if response.status_code == 200:
            chain_data = response.json()
            rounds = []
            for round in chain_data:
                if round['metadata'] is not None:
                    try:
                        round_start_time = datetime.datetime.utcfromtimestamp(
                            int(round['roundStartTime'])) if 'roundStartTime' in round else ''
                    except Exception as e:
                        print(f"Error converting roundStartTime {round['roundStartTime']} to datetime: {e}")
                        round_start_time = ''
                    try:
                        round_end_time = datetime.datetime.utcfromtimestamp(
                            int(round['roundEndTime'])) if 'roundEndTime' in round else ''
                    except Exception as e:
                        print(f"Error converting roundEndTime {round['roundEndTime']} to datetime: {e}")
                        round_end_time = ''

                    round_data = {
                        'round_id': round['id'] if 'id' in round else '',
                        'name': round['metadata']['name'] if 'name' in round['metadata'] else '',
                        'amountUSD': round['amountUSD'] if 'amountUSD' in round else '',
                        'votes': round['votes'] if 'votes' in round else '',
                        'description': round['metadata']['description'] if 'description' in round['metadata'] else '',
                        'matchingFundsAvailable': round['metadata']['matchingFunds'][
                            'matchingFundsAvailable'] if 'matchingFunds' in round['metadata'] else '',
                        'matchingCap': round['metadata']['matchingFunds']['matchingCap'] if 'matchingFunds' in round[
                            'metadata'] else '',
                        'roundStartTime': round_start_time,
                        'roundEndTime': round_end_time
                    }
                    rounds.append(round_data)

            df = pd.DataFrame(rounds)
            if chain_id == '1':
                # Filter to beta rounds
                start_time = datetime.datetime(2023, 4, 26, 15, 0, 0)
                end_time = datetime.datetime(2023, 5, 9, 23, 59, 0)
                # filter to only include rounds with votes > 0 and roundStartTime <= start_time and roundEndTime == end_time
                df = df[(df['votes'] > 0) & (df['roundStartTime'] <= start_time) & (df['roundEndTime'] == end_time)]
                df = df[(df['votes'] > 0) & (df['roundStartTime'] <= start_time) & (df['roundEndTime'] == end_time)]
            elif chain_id == '10':
                df = df[df['round_id'] == '0x984e29dCB4286c2D9cbAA2c238AfDd8A191Eefbc']
            return df
    except:
        return pd.DataFrame()


@st.cache_data(ttl=3000)
def load_round_projects_data(chain_id, round_id):
    # prepare the URLs
    projects_url = '/'.join([CHAIN_URL, chain_id, 'rounds', round_id, 'projects.json'])

    try:
        # download the Projects JSON data from the URL
        response = requests.get(projects_url)
        if response.status_code == 200:
            projects_data = response.json()

        # Extract the relevant data from each project
        projects = []
        for project in projects_data:
            project_data = {
                'id': project['id'],
                'title': project['metadata']['application']['project']['title'],
                'description': project['metadata']['application']['project']['description'],
                'status': project['status'],
                'amountUSD': project['amountUSD'],
                'votes': project['votes'],
                'uniqueContributors': project['uniqueContributors']
            }
            projects.append(project_data)
        # Create a DataFrame from the extracted data
        dfp = pd.DataFrame(projects)
        # Reorder the columns to match the desired order and rename column id to project_id
        dfp = dfp[['id', 'title', 'description', 'status', 'amountUSD', 'votes', 'uniqueContributors']]
        dfp = dfp.rename(columns={'id': 'project_id'})
        # Filter to only approved projects
        dfp = dfp[dfp['status'] == 'APPROVED']
        return dfp
    except:
        return pd.DataFrame()


@st.cache_data(ttl=3000)
def load_round_votes_data(chain_id, round_id):
    votes_url = '/'.join([CHAIN_URL, chain_id, 'rounds', round_id, 'votes.json'])
    try:
        # download the Votes JSON data from the URL
        response = requests.get(votes_url)
        if response.status_code == 200:
            votes_data = response.json()
        df = pd.DataFrame(votes_data)
        return df
    except:
        return pd.DataFrame()


def get_USD_by_round_chart(chain_data, color_map):
    grouped_data = chain_data.groupby('name')['amountUSD'].sum().reset_index().sort_values('amountUSD', ascending=True)
    data = [go.Bar(
        x=grouped_data['amountUSD'],
        y=grouped_data['name'],
        marker_color=grouped_data['name'].map(color_map),  # map each round to a specific color
        orientation='h'
    )]
    layout = go.Layout(
        title='Crowdfunded (in $) by Round',
        xaxis=dict(title='Dollars'),
        yaxis=dict(title='Round')
    )
    fig = go.Figure(data=data, layout=layout)
    return fig


def get_contributions_by_round_bar_chart(chain_data, color_map):
    grouped_data = chain_data.groupby('name')['votes'].sum().reset_index().sort_values('votes', ascending=True)
    data = [go.Bar(
        x=grouped_data['votes'],
        y=grouped_data['name'],
        marker_color=grouped_data['name'].map(color_map),  # map each round to a specific color
        orientation='h'
    )]
    layout = go.Layout(
        title='Total Contributions (#) by Round',
        xaxis=dict(title='Number'),
        yaxis=dict(title='Round')
    )
    fig = go.Figure(data=data, layout=layout)
    return fig


def create_color_map(chain_data):
    unique_rounds = chain_data['name'].unique()
    color_list = ['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B2', '#937860', '#DA8BC3', '#8C8C8C', '#CCB974',
                  '#64B5CD', '#4E3D3D', '#AEBD38', '#AD6B5E', '#1F78B4', '#B2DF8A']  # manually specified list of colors
    color_map = dict(zip(unique_rounds, color_list[:len(unique_rounds)]))  # map each round to a specific color
    return color_map


def get_grants_bar_chart(votes_data):
    grouped_data = votes_data.groupby('title')['amountUSD'].sum().reset_index().sort_values('amountUSD', ascending=True)

    data = [go.Bar(
        x=grouped_data['amountUSD'],
        y=grouped_data['title'],
        marker_color='blue',
        orientation='h'
    )]
    layout = go.Layout(
        title='Total Contributions (in $) by Grant',
        xaxis={'title': 'Total Contributions ($)'},
        yaxis={'title': 'Grant'},
        height=800

    )
    fig = go.Figure(data=data, layout=layout)
    return fig


def create_block_times(starting_blockNumber, ending_blockNumber, starting_blockTime, chain_id):
    # Create an array of 107,000 blockNumbers starting from the starting_blockNumber and incrementing by 1 each time
    blocks = np.arange(starting_blockNumber, ending_blockNumber, 1)
    # create a new dataframe with the blocks array
    df = pd.DataFrame(blocks)
    df.columns = ['blockNumber']
    # create a new column called utc_time and use the starting_blockTime as the value for the first starting_blockNumber
    df['utc_time'] = starting_blockTime
    # as the blockNumber increases by 1, add 12.133 seconds to the utc_time
    if chain_id == '1':
        time_between_blocks = 12.133
    elif chain_id == '10':
        time_between_blocks = 2
    df['utc_time'] = pd.to_datetime(df['utc_time']) + pd.to_timedelta(
        time_between_blocks * (df['blockNumber'] - starting_blockNumber), unit='s')
    return df
