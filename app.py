from flask import (
    Flask,
    render_template,
    request,
    send_file,
    session,
)
import folium
import json
import pandas as pd
import os
import requests
import shutil


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OVERPASS_QUERY = """[out:json];
(
  node
    ["{}"="{}"]
    ({},{},{},{});
);
(._;>;);
out;"""

CSV_OUTPUT_FILENAME = "output.csv"
CACHE_DIR = 'cache/'

OSM_ATTRIBUTE_FILE = 'osm_values_to_keys.json'
COLS_TO_MOVE = ['name', 'lat', 'lon']


app = Flask(__name__)
app.secret_key = 'wa'


@app.route("/")
def main():
    session.clear()
    osm_values_to_keys = load_json(os.path.join(os.getcwd(), OSM_ATTRIBUTE_FILE))
    osm_values = sorted(osm_values_to_keys.keys())
    return render_template('index.html', values=osm_values)


@app.route('/process', methods=['GET', 'POST'])
def process():
    ne_lat = request.args.get('ne_lat')
    ne_lng = request.args.get('ne_lng')
    sw_lat = request.args.get('sw_lat')
    sw_lng = request.args.get('sw_lng')
    value = request.args.get('value')

    bbox = [sw_lat, sw_lng, ne_lat, ne_lng]

    osm_values_to_keys = load_json(os.path.join(os.getcwd(), OSM_ATTRIBUTE_FILE))

    map_features = extract_osm_data(bbox, osm_values_to_keys.get(value), value)
    df, output_file = convert_map_features_to_csv(map_features, value)

    session['output_file'] = output_file

    map_ = generate_map(location=[bbox[0], bbox[1]], zoom_start=13, markers_df=df, bbox=bbox)
    return render_template(
        'output.html',
        map=map_._repr_html_(),
        tables=[df.to_html(classes='data')],
        title=value
    )


@app.route('/download')
def download():
    output_file = session.get('output_file')
    return send_file(output_file, as_attachment=True)


if __name__ == '__main__':
    app.run()


def extract_osm_data(bbox, key, value, url=OVERPASS_URL, query = OVERPASS_QUERY):
    map_features = []
    response = requests.post(url, data={'data': query.format(key, value, *bbox)})
    if response.status_code != 200:
        raise KeyError("Bad request, check OSM keys and values in the query")
    data = response.json()
    for elt in data.get('elements'):
        elt_dict = {
            "id": elt.get('id'),
            "lat": elt.get('lat'),
            "lon": elt.get('lon'),
        }
        elt_dict.update(elt.get('tags'))
        map_features.append(elt_dict)
    return map_features
    

def convert_map_features_to_csv(map_features, value):
    df = pd.DataFrame.from_dict(map_features)
    df.dropna(axis=1, how='all', inplace=True)
    if not map_features:
        return pd.DataFrame([]), None
    remaining_cols = [col for col in df.columns if col not in COLS_TO_MOVE]
    df = df[COLS_TO_MOVE + remaining_cols]
    output_file = os.path.join(os.getcwd(), value + '_' + CSV_OUTPUT_FILENAME)
    df.to_csv(output_file)
    return df, output_file


def generate_map(location=[0, 0], zoom_start=3, width="100%", height="100%", bbox=None, markers_df=None):
    map_ = folium.Map(location=location, zoom_start=zoom_start, width=width, height=height)
    if markers_df is None:
        return map_
    for indice, row in markers_df.iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=row['name'],
            icon=folium.map.Icon(color='blue')
        ).add_to(map_)
    if bbox:
        map_.fit_bounds([(bbox[0], bbox[1]), (bbox[2], bbox[3])])
    return map_


def load_json(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)
