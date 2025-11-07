import folium
import streamlit as st
import pandas as pd
import leafmap.foliumap as leafmap
from folium.plugins import HeatMap

@st.cache_data
def load_addresses(path):
    return pd.read_csv(path)

@st.cache_data
def load_commutes(path):
    return pd.read_csv(path)

addresses = load_addresses('data/georgia_addresses.csv').dropna(subset=['asset_name', 'asset_lat', 'asset_lon', 'applicant_lat', 'applicant_lon', 'employer_lat', 'employer_lon']).drop_duplicates(subset=['applicant_lat', 'applicant_lon', 'employer_lat', 'employer_lon'])
commutes = load_commutes('data/commutes.csv')

valid_assets = addresses['asset_name'].value_counts()
valid_assets = valid_assets[valid_assets >= 10].index.tolist()

asset = st.sidebar.selectbox('Select Asset', sorted(valid_assets))
display = st.sidebar.radio('What to display?', options=['Employers', 'Previous Addresses'])

asset_loc = addresses[addresses['asset_name'] == asset][['asset_lat', 'asset_lon']].iloc[0]
asset_lat, asset_lon = asset_loc['asset_lat'], asset_loc['asset_lon']

employer_locs = addresses[addresses['asset_name'] == asset][['asset_name', 'employer_lat', 'employer_lon', 'employer_name', 'employer_address', 'employer_city', 'employer_zip_code']]
employer_locs['employer_full_address'] = (
    employer_locs['employer_address'].fillna('') + ', ' +
    employer_locs['employer_city'].fillna('') + ', ' +
    employer_locs['employer_zip_code'].fillna('')
)

employer_locs = pd.merge(employer_locs, commutes[['asset_name', 'employer_name', 'new_commute']], on=['asset_name', 'employer_name']).rename(columns={'new_commute': 'commute_time'})

employer_locs['_'] = (
    '<br>' + 
    employer_locs['employer_name'].fillna('') + '<br><br>' +
    employer_locs['employer_full_address'].fillna('') + '<br><br>' +
    'Commute time: ' + round(employer_locs['commute_time']).astype(str).fillna('') + ' min.'
)


prev_address_locs = addresses[addresses['asset_name'] == asset][['applicant_lat', 'applicant_lon', 'applicant_address', 'applicant_city', 'applicant_zip_code']]
prev_address_locs['applicant_full_address'] = (
    prev_address_locs['applicant_address'].fillna('') + ', ' +
    prev_address_locs['applicant_city'].fillna('') + ', ' +
    prev_address_locs['applicant_zip_code'].fillna('')
)

m = leafmap.Map(center=[asset_lat, asset_lon], zoom=9)
m.add_basemap("CartoDB.Positron")

emoji_icon = folium.DivIcon(html=f"""<div style="font-size: 24px;">🏠</div>""")
folium.Marker(
    location=[asset_lat, asset_lon],
    popup=asset,
    icon=emoji_icon
).add_to(m)

if display == 'Employers':
    m.add_points_from_xy(
        data=employer_locs,
        x='employer_lon',
        y='employer_lat',
        popup=['_'],
        layer_name='Employers',
        show=False
    )

    HeatMap(
        employer_locs[['employer_lat', 'employer_lon']].dropna().values.tolist(),
        radius=15,
        blur=25,
        min_opacity=0.4,
        name='Employer Heatmap'
    ).add_to(m)

elif display == 'Previous Addresses':
    m.add_points_from_xy(
        data=prev_address_locs,
        x='applicant_lon',
        y='applicant_lat',
        popup=['applicant_full_address'],
        layer_name='Previous Addresseses',
        show=False
    )
    HeatMap(
        prev_address_locs[['applicant_lat', 'applicant_lon']].dropna().values.tolist(),
        radius=15,
        blur=25,
        min_opacity=0.4,
        name='Employer Heatmap'
    ).add_to(m)

m.to_streamlit(height=700)