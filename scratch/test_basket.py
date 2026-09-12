import urllib.request
import json

url = "http://127.0.0.1:8000/api/v1/scrape/basket"
try:
    with urllib.request.urlopen(url) as response:
        res = json.loads(response.read().decode('utf-8'))
        print(f"Total routes: {len(res.get('routes', []))}")
        print(f"National Jevons Index: {res.get('national_basket_jevons_index')}")
        print(f"Mean Fare: Rs {res.get('basket_mean_fare_inr')}")
        print(f"Spread: Rs {res.get('basket_spread_inr')} (Min: Rs {res.get('basket_min_fare_inr')}, Max: Rs {res.get('basket_max_fare_inr')})")
        print("\nAggregate Breakdown:")
        for k, v in res.get('aggregate_breakdown', {}).items():
            print(f"  {k}: {v}")
        print("\nAll 15 Corridors:")
        for r in res.get('routes', []):
            ub = r['unbundled_fare']
            print(f"  {r['route']}: Fare=Rs {r['current_fare_inr']} | Carrier={r['carrier']} {r['flight_number']} | Dep={r['departure_time']} | Dur={r['duration']} | Mode={r['data_mode']}")
            print(f"      -> Base: Rs {ub['base_fare_inr']} ({ub['base_pct']}%) | Fuel: Rs {ub['fuel_surcharge_inr']} ({ub['fuel_pct']}%) | UDF: Rs {ub['udf_psf_inr']} ({ub['udf_pct']}%) | GST: Rs {ub['gst_inr']} ({ub['gst_pct']}%) | Conv: Rs {ub['convenience_fee_inr']} ({ub['conv_pct']}%)")
except Exception as e:
    import traceback
    traceback.print_exc()
