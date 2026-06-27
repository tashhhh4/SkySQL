import numpy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.img_tiles import OSM
import contextily
import folium
import geodatasets
import geopandas
import pandas
import rasterio
from PIL import Image
from matplotlib import (
    pyplot, colors,
    cm as colormap
)

BLUE = "#2476b3"
COLOR_GRADIENT = colormap.YlGnBu
RED_GRADIENT = colormap.Reds
RED_GREEN_GRADIENT =
COLORMAP_3 = colormap.viridis_r
GLOBAL_EXTENT = [-180, 180, -90, 90]
USA_EXTENT = [-127, -68.5, 24, 45] # min_lon, max_lon, min_lat, max_lat
# MAP_PATH = "maps/NE1_LR_LC.tif"


def validate_chart_data(data, sets):
    """
    Ensures that data is a dictionary containing exactly the keys in `sets`,
    and that each value is a list of equal length.
    """
    first_item_len = len(data[sets[0]])
    for dataset in sets:
        if len(data[dataset]) == 0:
            raise TypeError(f"chart data: Dictionary value can't be an empty list!")
        if dataset not in data:
            raise TypeError(f"chart data: Missing key '{dataset}' in data!")
        if len(data[dataset]) != first_item_len:
            raise TypeError(f"chart data: Mismatched lengths of lists in data dictionary!")


def draw_pct_delay_by_airline(data):
    """
    Creates a bar graph.
    `data` must be a dict in the following format:
      {
        "airlines": [...],
        "percentages": [...],
      }
    """

    validate_chart_data(data, ["airlines", "percentages"])
    airlines = data["airlines"]
    values = data["percentages"]

    fig, ax = pyplot.subplots(figsize=(12, 6), dpi=100) # 12x6 in. => 1200x600 pixels
    ax.bar(airlines, values, color=BLUE)
    ax.set_title("Percentage of Delayed Flights by Airline")
    ax.set_ylabel("Percentage of Delayed Flights")
    ax.set_xlabel("Airline")
    pyplot.xticks(rotation=20, ha="right")
    pyplot.tight_layout()

    return fig


def draw_pct_delay_by_hour(data):
    """
    Creates a color-mapped bar graph.
    `data` must be a dict in the following format:
      {
        "hours": [...],
        "percentages": [...],
      }
    """
    validate_chart_data(data, ["hours", "percentages"])
    hours = [str(int(h)) for h in data["hours"]]
    percentages = data["percentages"]

    fig, ax = pyplot.subplots(
        figsize=(12, 6),
        dpi=100,
    )
    ax.bar(hours, percentages, color="gray")
    ax.set_title("Percentage of Delayed Flights by Hour of Day")
    ax.set_ylabel("Percentage of Delayed Flights")
    ax.set_xlabel("Hour of Day")

    ymin, ymax = ax.get_ylim()

    normalization = colors.Normalize(vmin=ymin, vmax=ymax)
    cmap = COLOR_GRADIENT
    chart_colors = cmap(normalization(percentages))

    scalar_mappable = colormap.ScalarMappable(norm=normalization, cmap=cmap)
    scalar_mappable.set_array([])
    fig.colorbar(scalar_mappable, ax=ax)

    ax.bar(hours, percentages, color=chart_colors)

    fig.tight_layout()
    fig.subplots_adjust(right=1.08)

    return fig


def draw_pct_delay_by_route_heat(data):
    """
    `data` must be a dict in the following format:
      {
        "origins": [...],
        "destinations": [...],
        "percentages": [...],
      }
    """

    validate_chart_data(data, ["origins", "destinations", "percentages"])

    origins = data["origins"]
    destinations = data["destinations"]
    percentages = data["percentages"]
    unique_origins = sorted(set(origins))
    unique_destinations = sorted(set(destinations))
    values_matrix = numpy.zeros((len(unique_origins), len(unique_destinations)))
    for origin, destination, value in zip(
        origins, destinations, percentages
    ):
        i = unique_origins.index(origin)
        j = unique_destinations.index(destination)
        values_matrix[i, j] = value

    fig, ax = pyplot.subplots(figsize=(10.5, 10.5), dpi=100)
    heatmap = ax.imshow(values_matrix, cmap=RED_GRADIENT, aspect="auto")

    ax.set_title("Percentage of Delayed Flights on a Heatmap of Routes", fontsize=18, pad=20)

    ax.set_xticks(numpy.arange(len(unique_destinations)))
    ax.set_xticklabels(unique_destinations, rotation=90)
    ax.set_xlabel("DESTINATION AIRPORT", fontsize=12)
    ax.set_yticks(numpy.arange(len(unique_origins)))
    ax.set_yticklabels(unique_origins)
    ax.set_ylabel("ORIGIN AIRPORT", fontsize=12)

    cbar = pyplot.colorbar(heatmap, ax=ax)
    cbar.ax.tick_params(labelsize=14)

    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar.outline.set_visible(False)

    pyplot.tight_layout()
    fig.subplots_adjust(right=1.04)

    return fig


def draw_pct_delay_by_route_map(data):
    """ Plots lines over a map of the continental USA,
        with red lines representing the highest delays.
        `data` must contain:
          {
            "routes": [list of ((lat, lon) (lat, lon))],
            "pcts": [percentage delay for each route],
          }
    """
    validate_chart_data(data, ["routes", "pcts"])

    tiler = OSM()

    fig = pyplot.figure(figsize=(12, 6), dpi=100)
    ax = pyplot.axes(projection=tiler.crs)
    ax.set_extent(USA_EXTENT, crs=ccrs.PlateCarree())
    ax.add_image(tiler, 5) # Zoom level - the higher,
                           # the more tiles to download

    for route, pct in zip(data["routes"], data["pcts"]):
        ((origin_lat, origin_lon),
         (destination_lat, destination_lon)) = route
        origin_lat = float(origin_lat)
        origin_lon = float(origin_lon)
        destination_lat = float(destination_lat)
        destination_lon = float(destination_lon)

        ax.plot(
            [origin_lon, destination_lon],
            [origin_lat, destination_lat],
            transform=ccrs.PlateCarree(),
            color="red",
            linewidth=1,
            alpha=0.1,
        )

    fig.canvas.draw()

    return fig
