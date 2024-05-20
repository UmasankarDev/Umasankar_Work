import ee
import geopandas as gpd
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd

# Initialize the Earth Engine module.
ee.Initialize()

def surface_water_extent_time_series(geojson_file, start_date, end_date):
    # Load the GeoJSON file
    gdf = gpd.read_file(geojson_file)
    feature = ee.FeatureCollection(gdf.__geo_interface__)

    # Define the date range
    start = ee.Date(start_date)
    end = ee.Date(end_date)

    # Load the JRC Global Surface Water dataset
    dataset = ee.ImageCollection('JRC/GSW1_3/MonthlyHistory') \
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
    plt.savefig('surface_water_extent_time_series.png')
    plt.show()

# Example usage
geojson_file = r'C:\Development\pythonProject\MyDevelopmentHome\Lake_Kfar.geojson'
start_date = '2015-01-01'
end_date = '2020-01-01'

surface_water_extent_time_series(geojson_file, start_date, end_date)
