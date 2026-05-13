from flask import Flask, jsonify, request
from flask_cors import CORS
import random

import netCDF4
import pandas as pd

import numpy as np
from scipy.stats import scoreatpercentile, percentileofscore

import xarray as xr

import threading
file_lock = threading.Lock()

app = Flask(__name__)
CORS(app)  # Allow requests from Vue dev server

DATADIR = '../../data/'
MAPDIR = DATADIR + 'mapping/'
MONTH_NAMES = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

# --- Example in-memory data store ---
items = [
    {"id": 1, "name": "Item One", "description": "First example item"},
    {"id": 2, "name": "Item Two", "description": "Second example item"},
]
next_id = 3


# --- API Routes ---

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Flask API is running"})


@app.route("/api/items", methods=["GET"])
def get_items():
    """Return all items."""
    return jsonify({"items": items})


@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """Return a single item by ID."""
    item = next((i for i in items if i["id"] == item_id), None)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item)


@app.route("/api/items", methods=["POST"])
def create_item():
    """Create a new item."""
    global next_id
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Name is required"}), 400

    new_item = {
        "id": next_id,
        "name": data["name"],
        "description": data.get("description", ""),
    }
    items.append(new_item)
    next_id += 1
    return jsonify(new_item), 201


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete an item by ID."""
    global items
    item = next((i for i in items if i["id"] == item_id), None)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    items = [i for i in items if i["id"] != item_id]
    return jsonify({"message": f"Item {item_id} deleted"})


# --- Chart Data Routes ---
# All chart endpoints return { labels: [...], values: [...] }
# so the BarChart component can consume them without any extra mapping.

YEARS = list(range(1981,2026))

CHART_DATA = {
    "pr":   [142, 198, 175, 220, 265, 310, 289, 340, 295, 378, 410, 450],
    "tas":   [980, 1120, 1050, 1340, 1480, 1600, 1520, 1750, 1690, 1820, 1940, 2100],
    "labels": YEARS
}


@app.route("/api/data/<collection>/<dataset>/<varname>/<feature_id>", methods=["GET"])
def timeseries(collection, dataset, varname, feature_id):

    agg = request.args.get('agg', 'mean') 
    timeagg = request.args.get('timeagg', 'monthly')
    anomaly = request.args.get('anomaly', 'none')
    startmonth = request.args.get('startmonth', '1')
    endmonth = request.args.get('endmonth', '12')

    response = {}

    try:
        startmonth = int(startmonth)
        endmonth = int(endmonth)
    except:
        return jsonify({'error': f'Cannot convert startmonth and enddmonth to integers {startmonth} {endmonth}'})

    if startmonth > endmonth:
        months = list(range(startmonth, 13)) + list(range(1,endmonth+1))
    else:
        months = list(range(startmonth, endmonth+1))

    months = list(set(months))

    # Validate feature_id
    try:
        feature_id = float(feature_id)
    except (ValueError, TypeError):
        return jsonify({'error': f'Invalid feature_id {feature_id}'})

    path = f'{DATADIR}{collection}/{dataset}.nc'

    with file_lock:
        try:
            ds = xr.open_dataset(path, engine='netcdf4')
        except:
            return jsonify({'error': f'Failed to open datasets {dataset} at path {path}'})

        variable = ds[varname]

        if timeagg == 'monthly':
            times = list(variable.time.data)

        elif timeagg == 'seasonal':
            variable = variable.groupby(variable.time.dt.month).mean()
            times = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        elif timeagg == 'annual':
            date_filter = ds.time.dt.month.isin(months).data
            variable = variable.isel(time=date_filter)
           
            if agg == 'mean':
                variable = variable.groupby(variable.time.dt.year).mean()
            else:
                variable = variable.groupby(variable.time.dt.year).sum()
            
            times = list(variable.year.data)

        try:
            ids = list(ds['id'].data)
        except:
            response['error'] = f'No id variable in dataset {dataset}'
            return (response, headers)

        loc = ids.index(feature_id)

        if loc < 0:
            response['error'] = f'Failed to find feature id {feature_id} in {dataset}'

        slices = [slice(None)] * len(variable.shape)
        slices[-1] = loc
        subset = variable[tuple(slices)]

        vals = subset.data

        vals_min = vals.min()
        vals_max = vals.max()

        if anomaly == 'absolute':
            vals = vals - vals.mean()
        elif anomaly == 'relative':
            vals = 100.0 * ((vals - vals.mean())/vals.mean())

        vals = [float(v) for v in list(vals)]
        times = [str(t) for t in times]

        response['values'] = vals
        response['minval'] = float(vals_min)
        response['maxval'] = float(vals_max)
        response['labels'] = times

        ds.close()

    return jsonify(response)



@app.route("/api/forecast/<model>/<year>/<month>/<varname>/<feature_id>")
def forecast(model, year, month, varname, feature_id):
    """
    Seasonal forecast endpoint that:
    1. Loads observed and forecast data for a specific location
    2. Calculates forecast probabilities relative to observed climatology
    3. Evaluates forecast skill using hit/miss statistics
    4. Returns probabilities and skill metrics for the target year
    """
    
    response = {'model': model}
    headers = {'Access-Control-Allow-Origin': '*'}

    VARMAP = {'pr': {'name': 'pr', 'scale': 86400 * 1000 * 30.1}}
#    VARMAP['pr']['scale'] = 86400 * 1000 * 30.1  # mm/month
    
    obs_filename = f'{DATADIR}observed/PRCPTOT_mon_CHC_CHIRPS-2.0-0p25_198101-202312_epsg102113.nc'
    fcst_filename = f'{DATADIR}ecmwf/system51/hexgrid_p25_epsg102113/_pr.nc'

    print("obs filename", obs_filename)
    print("fcst filename", fcst_filename)

    # Convert URL parameters to proper types
    month = int(month)
    year = int(year)

    # Parse lead time range (default: 0-5 months ahead)
    # lead=(0,3) means forecast months 0, 1, 2, 3 after initialization
    lead_arg = request.args.get('lead')
    lead = tuple(int(v) for v in lead_arg.split(','))

    # Parse obs_threshold argument 
    obs_threshold_arg = request.args.get('obs_threshold')
    try:
        obs_threshold = float(obs_threshold_arg)
    except (ValueError, TypeError):
        response['error'] = f'Invalid obs_threshold value: {obs_threshold_arg}'
        return (response, headers)

    # Parse feature ID
    try:
        feature_id = float(feature_id)
    except (ValueError, TypeError):
        response['error'] = f'Invalid feature_id {feature_id}'
        return (response, headers)

    print("year/month", year, month)
    print("obs_threshold", obs_threshold)
    print("feature_id", feature_id)


    with file_lock:

        bigbag = {'observed': [], 'ensemble': []}

        # === Load observed data ===
        obs_ds = xr.open_dataset(obs_filename, engine='netcdf4')
        obsvar = obs_ds['PRCPTOT']
        obs_ids = list(obs_ds['id'].data)

        # Find feature location in observed dataset
        try:
            obs_loc = obs_ids.index(feature_id)
        except ValueError:
            response['error'] = f'Feature ID {feature_id} not found in observed dataset.'
            return (response, headers)

        obsvar = obsvar[:, obs_loc]

        # Load forecast data
        fcst_ds = netCDF4.Dataset(fcst_filename)

        try:
            fcst_var = fcst_ds[VARMAP[varname]['name']]
        except KeyError:
            response['error'] = f'Variable {varname} not found in forecast dataset.'
            return (response, headers)

        try:
            ids = list(fcst_ds['id'][:])
            fcst_loc = ids.index(feature_id)
        except:
            response['error'] = f'Feature ID {feature_id} not found in forecast dataset.'
            return (response, headers)

        print('fcst var', fcst_var)

        # Get time information
        fcst_times = netCDF4.num2date(fcst_ds['time'], fcst_ds['time'].units)
        #times = times.filled()
        
        # Determine year range from data
        years_in_data = [t.year for t in fcst_times if hasattr(t, 'year') and not pd.isna(t.year)]
        if not years_in_data:
            response['error'] = 'No valid years found in forecast dataset.'
            return (response, headers)
        
        min_year = min(years_in_data)
        max_year = max(years_in_data)
        forecast_year = year  # Use the requested year from URL as forecast target
        print('first, last, forecast', min_year, max_year, forecast_year)
        
        # Check if requested year is available in the dataset
        if forecast_year not in years_in_data:
            response['error'] = f'Requested forecast year {forecast_year} not found in dataset. Available years: {min_year}-{max_year}'
            return (response, headers)
        
        vals = {}
        for y in range(min_year, max_year+1):
            print(y, month)

            # Find time indices for this year/month using flattened times
            time_matches = [(t.year == y and t.month == month) for t in fcst_times]
            time_indices = [i for i, match in enumerate(time_matches) if match]
  
            # store year by year data in a dict
            vals[y] = {}
            # Extract data based on time array structure
            lead_slice = slice(lead[0], lead[1] + 1)
            time_indices = np.array(time_indices)
            print('time indices', time_indices)
            print('lead slice', lead_slice)

            extract = fcst_var[time_indices, lead_slice, :, fcst_loc]  # use all 51 not 20 (not sure what happened here)
            extract = extract.squeeze() * VARMAP[varname]['scale']  # drop now 1 dim time step and scale to mm/day
            print(extract.shape, extract)
#            extract = extract.mean(axis=0)  # get the mean of the first dimension (lead_slice)(we get our month then work with this + forecast leads)
            extract = extract.sum(axis=0)  # get the mean of the first dimension (lead_slice)(we get our month then work with this + forecast leads)
            print(extract.shape) #= (20,) or (51,) for full ensemble
            ensemble_vals = extract.flatten().tolist()
            vals[y]['ensemble'] = ensemble_vals
            #print(vals[y])
            if y < forecast_year-2: # ie is a hindcast not the forecast
                bigbag['ensemble'].append(ensemble_vals) # a list of lists n_years long, each list containing 20 ensemble members
                yearA = y
                yearB = y
                monthA = month + lead[0]
                monthB = month + lead[1]
                if monthB > 12:
                    monthB -= 12
                    yearB += 1
                startdate = f'{yearA}-{monthA:02d}-01'
                enddate = f'{yearB}-{monthB:02d}-28'
                print(f'startdate {startdate} enddate {enddate}')
                obsval = obsvar.loc[startdate: enddate].sum(axis=0).data.tolist()
                print(obsval)
                bigbag['observed'].append(obsval)
        obs_ds.close()
        fcst_ds.close()

    bigbag['observed_sorted'] = np.sort(np.array(bigbag['observed']))
    bigbag['ensemble_sorted'] = np.sort(np.array(bigbag['ensemble']).flatten())
    
    print(f'ensemble_sorted {bigbag["ensemble_sorted"]}')

    # Find what percentile the threshold value represents in observed climatology
    obs_percentile = percentileofscore(bigbag['observed_sorted'], obs_threshold, kind='strict')
    
    # cap percentile to 99.9 and 0.1 to avoid division by zero problems
    if obs_percentile >= 99.9:
        obs_percentile = 99.9
    elif obs_percentile <= 0.1:
        obs_percentile = 0.1

    print(f'obs_percentile {obs_percentile}')

    # Find equivalent threshold in forecast climatology
    ens_threshold = np.percentile(bigbag['ensemble_sorted'], obs_percentile) # silence numpy warnings, should be faster
    print(f'ensemble threshold {ens_threshold}')

    # calibration
    prob_below = []
    prob_above = []
    for i in range(len(bigbag['ensemble'])):
        ens_vals = bigbag['ensemble'][i]
        prob_below.append(100.0 * (ens_vals < ens_threshold).sum() / len(ens_vals))
        prob_above.append(100.0 * (ens_vals >= ens_threshold).sum() / len(ens_vals))
        del ens_vals

    prob_below = np.array(prob_below)
    prob_above = np.array(prob_above)
    
    # These thresholds define when to issue a forecast
    threshold_below = np.percentile(prob_below, 100 - obs_percentile)  
    threshold_above = np.percentile(prob_above, 100 - obs_percentile)

    # Calculate forecast probabilities for the target year
    forecast_ensemble = vals[forecast_year]['ensemble']
    prob_below = 100.0 * (np.array(forecast_ensemble) < ens_threshold).sum() / len(forecast_ensemble)
    prob_above = 100.0 * (np.array(forecast_ensemble) >= ens_threshold).sum() / len(forecast_ensemble)
    
    # Determine if forecast indicates high probability event
    fcst_below = prob_below > threshold_below
    fcst_above = prob_above > threshold_above

    if fcst_below and fcst_above:
        if prob_below > prob_above:
            fcst_above = False
        elif prob_above > prob_below:
            fcst_below = False
        else:
            # If both probabilities are equal, set both to False
            fcst_below = False
            fcst_above = False

    ensemble_mems_above = len([x for x in forecast_ensemble if x > ens_threshold])
    ensemble_mems_below = len([x for x in forecast_ensemble if x <= ens_threshold])

    # Hindcast Verification
    hits_below = hits_above = misses_below = misses_above = falses_below = falses_above = neutral = total_forecasts = 0
    for i in range(len(bigbag['ensemble'])): # bigbag only filled with hindcast so can go by index not year
        obs_val_at_t = bigbag['observed'][i]
        ens_vals_at_t = bigbag['ensemble'][i]
        ens_vals_at_t = np.sort(ens_vals_at_t) # sort only this year != bigbag['ensemble_sorted']
        
        # Calculate probabilities for this year 
        prob_below_at_t = 100.0 * (ens_vals_at_t < ens_threshold).sum() / len(ens_vals_at_t)
        prob_above_at_t = 100.0 * (ens_vals_at_t >= ens_threshold).sum() / len(ens_vals_at_t)

        # Determine if forecast indicates high probability event
        fcst_below_at_t = prob_below_at_t > threshold_below
        fcst_above_at_t = prob_above_at_t > threshold_above

        if fcst_below_at_t and fcst_above_at_t:
            if prob_below_at_t > prob_above_at_t:
                fcst_above_at_t = False
            elif prob_above_at_t > prob_below_at_t:
                fcst_below_at_t = False
            else:
                # If both probabilities are equal, set both to False
                fcst_below_at_t = False
                fcst_above_at_t = False

        obs_below_at_t = obs_val_at_t < obs_threshold
        obs_above_at_t = obs_val_at_t >= obs_threshold

        # correct forecasts
        if fcst_below_at_t and obs_below_at_t:
            hits_below = hits_below + 1        # Correctly predicted below-threshold event
        if fcst_above_at_t and obs_above_at_t:
            hits_above = hits_above + 1        # Correctly predicted above-threshold event
        
        # false forecasts (forecast predicted event but it didn't happen)
        if fcst_below_at_t and not obs_below_at_t:
            falses_below = falses_below + 1      # Predicted below-threshold but observed above
        if fcst_above_at_t and not obs_above_at_t:
            falses_above = falses_above + 1      # Predicted above-threshold but observed below
        
        # misses (event happened but forecast didn't predict it)
        if not fcst_below_at_t and obs_below_at_t:
            misses_below = misses_below + 1      # Missed a below-threshold event
        if not fcst_above_at_t and obs_above_at_t:
            misses_above = misses_above + 1      # Missed an above-threshold event
        
        # neutral forecast (neither above nor below threshold exceeded)
        if not fcst_below_at_t and not fcst_above_at_t:
            neutral = neutral + 1  # No forecast issued (regardless of what was observed)

        if fcst_below_at_t or fcst_above_at_t:
            total_forecasts = total_forecasts + 1
    
    response['obs_threshold'] = obs_threshold
    response['obs_percentile'] = int(round(obs_percentile))
    response['ens_threshold'] = ens_threshold
    response['prob_below'] = int(prob_below)
    response['prob_above'] = int(prob_above)
    response['fcst_below'] = str(fcst_below)
    response['fcst_above'] = str(fcst_above)
    response['ensemble_mems_above'] = ensemble_mems_above
    response['ensemble_mems_below'] = ensemble_mems_below
    response['hits_below'] = hits_below
    response['hits_above'] = hits_above
    response['misses_below'] = misses_below
    response['misses_above'] = misses_above
    response['falses_below'] = falses_below
    response['falses_above'] = falses_above
    response['neutral'] = neutral
    response['total_forecasts'] = total_forecasts
    response['verification_years_count'] = len(bigbag['ensemble'])
    response['verification_year_range'] = f"{min_year}-{max_year}"

    return (response, headers)


@app.route("/api/forecast_meta")
def forecast_meta():
    # Return information about the latest available forecast

    response = {}
    headers = {'Access-Control-Allow-Origin': '*'}
    
    try:
        # Load forecast data to determine available forecast months and years
        filename = f'{DATADIR}ecmwf/system51/hexgrid_p25_epsg102113/_pr.nc'
        with file_lock:
            ds = netCDF4.Dataset(filename)
            
            # Get time information and handle both 1D and 2D time arrays
            times_raw = ds['time'][:]
            times = netCDF4.num2date(times_raw, ds['time'].units)
            
            # Get valid time entries
            valid_times = [t for t in times if hasattr(t, 'year') and not pd.isna(t.year)]
            
            if not valid_times:
                response['error'] = 'No valid forecast times found'
                return (response, headers)
            
            # Get the latest forecast
            latest_time = max(valid_times)
            
            # Get available years and months
            years = sorted(list(set([t.year for t in valid_times])))
            months = sorted(list(set([t.month for t in valid_times])))
            
            response['latest_year'] = latest_time.year
            response['latest_month'] = latest_time.month
            response['latest_date'] = latest_time.strftime('%Y-%m-%d')
            response['available_years'] = years
            response['available_months'] = months
            
            ds.close()
            
    except Exception as e:
        response['error'] = f'Error reading forecast data: {str(e)}'
        return (response, headers)
    
    return (response, headers)


@app.route("/api/chart-data/regions", methods=["GET"])
def chart_data_regions():
    """Regional breakdown bar chart."""
    return jsonify({
        "labels": ["Western Cape", "Gauteng", "KZN", "Eastern Cape", "Limpopo",
                   "Mpumalanga", "North West", "Free State", "Northern Cape"],
        "values": [88, 95, 72, 61, 54, 49, 43, 38, 22],
    })


@app.route("/api/chart-data/products", methods=["GET"])
def chart_data_products():
    """Product mix bar chart."""
    return jsonify({
        "labels": ["Product A", "Product B", "Product C", "Product D", "Product E"],
        "values": [3200, 2750, 1980, 1540, 890],
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)