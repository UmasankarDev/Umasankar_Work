import ee
import geopandas as gpd
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import sys
import os
import configparser

def authenticate_earth_engine(project_id):
    try:
        ee.Initialize(project=project_id)
    except ee.EEException as e:
        print("Error initializing Earth Engine: ", e)
        ee.Authenticate()
        ee.Initialize(project=project_id)

def surface_water_extent_time_series(geojson_file, start_date, end_date,output_file):
    # Load the GeoJSON file
    gdf = gpd.read_file(geojson_file)
    feature = ee.FeatureCollection(gdf.__geo_interface__)

    # Define the date range
    start = ee.Date(start_date)
    end = ee.Date(end_date)

    # Load the JRC Global Surface Water dataset
    dataset = ee.ImageCollection('JRC/GSW1_4/MonthlyHistory') \
        .filterDate(start, end)

    def compute_water_area(image):
        # Mask for water (where water is true)
        water_mask = image.select('water').eq(2)  # Permanent water: 2
        water_area = water_mask.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=feature.geometry(),
            scale=30,
            maxPixels=1e9
        ).get('water')
        return ee.Feature(None, {'date': image.date().format(), 'water_area': water_area})

    # Map over the collection
    water_areas = dataset.map(compute_water_area).getInfo()
    # Extract the results and convert to pandas DataFrame
    results = [{'date': datetime.strptime(feature['properties']['date'], '%Y-%m-%dT%H:%M:%S'),
                'water_area': feature['properties']['water_area']} for feature in water_areas['features']]
    df = pd.DataFrame(results)
    # Plot the time series
    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['water_area'], marker='o', linestyle='-')
    plt.title('Surface Water Extent Time Series')
    plt.xlabel('Date')
    plt.ylabel('Water Area (square meters)')
    plt.grid(True)
    plt.show()
    output_dir, base_name = os.path.split(output_file)
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f"{base_name}_{timestamp}.png")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"{output_file}_{timestamp}.png"
    print(output_file)
    plt.savefig(output_file)

def Process(geojson_file, start_date, end_date, project_id,output_file):
    authenticate_earth_engine(project_id)
    surface_water_extent_time_series(geojson_file, start_date, end_date,output_file)

if __name__ == "__main__":
    config_file = "Config.ini"
    if not os.path.exists(config_file):
        print("Error: Config.ini not found in the current directory.")
        sys.exit(1)
    config = configparser.ConfigParser()
    config.read(config_file)
    geojson_file = config['Input']['geojson_file']
    output_file_base = config['Output']['output_file_base']
    start_date = config['Date_range']['start_date']
    end_date = config['Date_range']['end_date']
    project_id=config['Google_Project_ID']['project_id']
    Process(geojson_file, start_date, end_date, project_id,output_file_base)
