from flask import Flask, request, jsonify, render_template
import requests
import folium
from geopy.distance import geodesic
import pandas as pd
from sklearn.cluster import KMeans
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Foursquare API credentials
CLIENT_ID = '5O2OQN1HOFBER5CQ4VJSEBU3PZ54Z3T31EGTNFJ0V04KSKZI'
CLIENT_SECRET = 'H2KIZ3QZRGZD2GVCOSSTL04SQ3N0Y5QWEWQKPQ1VTPQNF24R'
VERSION = '20180604'

@app.route('/')
def index():
    return render_template('index.html')

def fetch_foursquare_data(lat, lng, query, radius, limit=50):
    """Fetch data from Foursquare API for a specific query."""
    url = (
        f'https://api.foursquare.com/v2/venues/search'
        f'?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}'
        f'&ll={lat},{lng}&v={VERSION}&query={query}&radius={radius}&limit={limit}'
    )
    response = requests.get(url)
    if response.status_code == 200:
        return len(response.json()['response']['venues'])
    return 0

@app.route('/search', methods=['GET','POST'])
def search():
    
    latitude = float(request.form['latitude'])
    longitude = float(request.form['longitude'])
    preference1 = request.form['preference1']
    preference2 = request.form['preference2']
    display_metro = request.form['display_metro'] 
    
    # Collect preferences
    preferences = [preference1, preference2]
    available_preferences = {
    'Restaurants': 'Restaurant',
    'Groceries': 'Fruit',
    'Gyms': 'Gym',
    'Cafes': 'Cafes',
    'Parks': 'Park',
    'Hospitals': 'Hospital',
    'Schools': 'School',
    'Shopping Malls': 'Mall',
    'Banks/ATMs': 'Bank',
    'Libraries': 'Library',
    'Pet Stores': 'Pet Store',
    'Pharmacies': 'Pharmacy',
    'Fitness Studios': 'Fitness'
}
    valid_preferences = [pref for pref in preferences if pref in available_preferences]

    if not valid_preferences:
        return jsonify({'status': 'error', 'message': 'Invalid preferences selected'})

    # Search for apartments
    search_query = 'Apartment'
    radius = 18000
    LIMIT = 50
    url = (f'https://api.foursquare.com/v2/venues/search?client_id={CLIENT_ID}'
           f'&client_secret={CLIENT_SECRET}&ll={latitude},{longitude}&v={VERSION}'
           f'&query={search_query}&radius={radius}&limit={LIMIT}')
    results = requests.get(url).json()
    venues = results['response']['venues']
    dataframe = pd.json_normalize(venues)

    # Extract necessary columns
    dataframe['lat'] = dataframe['location.lat']
    dataframe['lng'] = dataframe['location.lng']
    dataframe = dataframe[['name', 'lat', 'lng']]

    # Use ThreadPoolExecutor for concurrent API requests based on preferences
    preference_data = {pref: [] for pref in valid_preferences}
    with ThreadPoolExecutor(max_workers=10) as executor:
        tasks = {
            pref: [
                executor.submit(fetch_foursquare_data, lat, lng, available_preferences[pref], 5000)
                for lat, lng in zip(dataframe['lat'], dataframe['lng'])
            ]
            for pref in valid_preferences
        }
        for pref, task_list in tasks.items():
            preference_data[pref] = [task.result() for task in task_list]

    # Add preference data to the DataFrame
    for pref in valid_preferences:
        dataframe[pref] = preference_data[pref]

    # Clustering based on selected preferences
    clustering_columns = ['lat', 'lng'] + valid_preferences
    kmeans = KMeans(n_clusters=3, random_state=0).fit(dataframe[clustering_columns])
    dataframe['Cluster'] = kmeans.labels_.astype(str)

    
    
    

    # Map generation
    map_bang = folium.Map(location=[latitude, longitude], zoom_start=12)
    folium.Marker([latitude, longitude], popup="Your Location", icon=folium.Icon(color="red")).add_to(map_bang)

    def color_producer(cluster):
        return ['green', 'orange', 'red'][int(cluster)]

    # Add apartment markers
    for _, row in dataframe.iterrows():
        apartment_location = (row['lat'], row['lng'])
        distance = geodesic((latitude, longitude), apartment_location).kilometers
        popup_content = f"<b>{row['name']}</b><br>Distance: {distance:.2f} km"
        popup = folium.Popup(popup_content, max_width=200, min_width=150)

        folium.CircleMarker(
            [row['lat'], row['lng']],
            fill=True,
            fill_opacity=1,
            popup=popup,
            radius=5,
            color=color_producer(row['Cluster'])
        ).add_to(map_bang)

    if(display_metro=="yes"):
            # Fetch Metro Stations
        metro_url = (
            f'https://api.foursquare.com/v2/venues/search?client_id={CLIENT_ID}'
            f'&client_secret={CLIENT_SECRET}&ll={latitude},{longitude}&v={VERSION}'
            f'&query=Metro Station&radius={radius}&limit={LIMIT}'
        )
        metro_response = requests.get(metro_url)
        metro_stations = []
        if metro_response.status_code == 200:
            metro_data = metro_response.json()['response']['venues']
            metro_stations = pd.json_normalize(metro_data)[['name', 'location.lat', 'location.lng']]

        # Add metro station markers
        for _, metro in metro_stations.iterrows():
            metro_location = (metro['location.lat'], metro['location.lng'])
            distance = geodesic((latitude, longitude), metro_location).kilometers
            popup_content = f"{metro['name']}</b><br>Distance: {distance:.2f} km"
            popup = folium.Popup(popup_content, max_width=200, min_width=150)

            folium.Marker(
                [metro['location.lat'], metro['location.lng']],
                popup=popup,
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(map_bang)

    # Save map to an HTML file
    map_bang.save('templates/map.html')

    response_data = {
        "status": "success",
        "data": dataframe.to_dict(orient='records')  # Converts the dataframe to a list of dictionaries
    }
    
    return jsonify(response_data)

@app.route('/map')
def display_map():
    return render_template('map.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
