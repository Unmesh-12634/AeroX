import urllib.request
import json

base_url = "http://localhost:8000"

def test_endpoints():
    results = {}
    
    # 1. HTML check
    with urllib.request.urlopen(f"{base_url}/") as res:
        html = res.read().decode('utf-8')
        results["html_status"] = res.status
        results["has_view_section"] = "id=\"view-airfare-index\"" in html
        results["has_granularity_switcher"] = "id=\"apixGranularitySwitcher\"" in html
        results["has_recalc_button"] = "id=\"btnRecalculateApix\"" in html
        results["has_basket_table"] = "id=\"tableApixBasketRoutes\"" in html
        results["has_methodology"] = "id=\"apixMethodologyCard\"" in html
        results["has_sim_card"] = "apix-sim-card" in html
        results["cache_buster_v4_6"] = "style.css?v=4.6" in html and "app.js?v=4.6" in html

    # 2. Daily time series
    with urllib.request.urlopen(f"{base_url}/api/v1/apix/time-series?granularity=daily") as res:
        daily_json = json.loads(res.read().decode('utf-8'))
        results["daily_status"] = res.status
        results["daily_headline"] = daily_json.get("headline_apix")
        results["daily_series_count"] = len(daily_json.get("series", []))
        results["daily_routes_count"] = len(daily_json.get("routes_ledger", []))
        results["daily_bias"] = daily_json.get("substitution_bias_pts")

    # 3. Weekly time series
    with urllib.request.urlopen(f"{base_url}/api/v1/apix/time-series?granularity=weekly") as res:
        weekly_json = json.loads(res.read().decode('utf-8'))
        results["weekly_status"] = res.status
        results["weekly_headline"] = weekly_json.get("headline_apix")
        results["weekly_series_count"] = len(weekly_json.get("series", []))

    # 4. Monthly time series
    with urllib.request.urlopen(f"{base_url}/api/v1/apix/time-series?granularity=monthly") as res:
        monthly_json = json.loads(res.read().decode('utf-8'))
        results["monthly_status"] = res.status
        results["monthly_headline"] = monthly_json.get("headline_apix")
        results["monthly_series_count"] = len(monthly_json.get("series", []))

    # 5. Basket routes
    with urllib.request.urlopen(f"{base_url}/api/v1/apix/basket-routes") as res:
        basket_json = json.loads(res.read().decode('utf-8'))
        results["basket_routes_status"] = res.status
        results["basket_routes_count"] = basket_json.get("count")

    # 6. Recalculate
    req = urllib.request.Request(f"{base_url}/api/v1/apix/recalculate", method='POST')
    with urllib.request.urlopen(req) as res:
        recalc_json = json.loads(res.read().decode('utf-8'))
        results["recalc_status"] = res.status
        results["recalc_processed"] = recalc_json.get("observations_processed")

    print(json.dumps(results, indent=2))

test_endpoints()
