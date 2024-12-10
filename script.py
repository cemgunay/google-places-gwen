import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GOOGLE_API_KEY')
TEXT_SEARCH_URL = 'https://places.googleapis.com/v1/places:searchText'
PLACE_DETAILS_URL_BASE = 'https://places.googleapis.com/v1/places'

headers_placeId = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': API_KEY,
    'X-Goog-FieldMask': 'places.id'
}

headers_details = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': API_KEY,
    'X-Goog-FieldMask': 'displayName,types,rating,userRatingCount,priceLevel,priceRange,googleMapsUri,formattedAddress,addressComponents'
}

df = pd.read_csv('titles.csv', header=None)

addresses = [item for sublist in df.values.tolist() for item in sublist]

# Create an empty DataFrame to store results
results_df = pd.DataFrame(columns=[
    'Name', 'Types', 'Rating', 'User Ratings Count', 'Price Level', 'Start Price', 'End Price', 'Formatted Address', 'Google Maps URL', 'Error'
])

processed_count = 0
added_count = 0
filtered_count = 0

def get_with_retry(url, headers, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}. Retrying {retries + 1}/{max_retries}...")
            retries += 1
            time.sleep(2 ** retries)  # Exponential backoff
    raise Exception("Max retries exceeded")


def get_place_id(address):
    data = {
        'textQuery': address
    }
    response = requests.post(TEXT_SEARCH_URL, headers=headers_placeId, json=data)
    response_json = response.json()
    if len(response_json) == 0:
        return None
    results = response_json.get('places')
    if results:
        return results[0].get('id')
    return None

def get_place_details(place_id):
    url = f'{PLACE_DETAILS_URL_BASE}/{place_id}'
    response = get_with_retry(url, headers=headers_details)
    place_details = response.json()

    # Debugging: Print full address components for visibility
    address_components = place_details.get('addressComponents', [])

    # Safely filter the address components for 'country' and 'France'
    filtered_data = [
        item for item in address_components
        if 'country' in item.get('types', []) and item.get('longText', '') == 'France'
    ]

    # If no matching 'France' component is found, handle gracefully
    if not filtered_data:
        print(f"Place ID {place_id} is not in France.")
        return {"error": "Place is not in France"}
    
    # Remove the full addressComponents from the result (optional)
    if 'addressComponents' in place_details:
        del place_details['addressComponents']
    
    return place_details


def main():
    global results_df, processed_count, added_count, filtered_count
    for address in addresses:
        processed_count += 1
        print(f"Processing address {processed_count}/{len(addresses)}: {address}")
        place_id = get_place_id(address)
        if place_id:
            details = get_place_details(place_id)
            if "error" not in details:
                # Extract price range details
                price_range = details.get('priceRange', {})
                start_price = price_range.get('startPrice', {})
                end_price = price_range.get('endPrice', {})
                
                # Add valid places to the DataFrame
                if details.get("displayName", {}).get("text"):  # Ensure valid data before concatenating
                    results_df = pd.concat([results_df, pd.DataFrame([{
                        'Name': details.get('displayName', {}).get('text'),
                        'Types': ', '.join(details.get('types', [])),
                        'Rating': details.get('rating'),
                        'User Ratings Count': details.get('userRatingCount'),
                        'Price Level': details.get('priceLevel', None),
                        'Start Price': f"{start_price.get('units', '')} {start_price.get('currencyCode', '')}" if start_price else None,
                        'End Price': f"{end_price.get('units', '')} {end_price.get('currencyCode', '')}" if end_price else None,
                        'Formatted Address': details.get('formattedAddress'),
                        'Google Maps URL': details.get('googleMapsUri'),
                        'Error': None
                    }])], ignore_index=True)
                    added_count += 1
            else:
                filtered_count += 1
                print(f"Filtered out: {details['error']}")
        else:
            filtered_count += 1
            print(f"Place ID not found for address: {address}")
        
    # Save to Excel
    results_df.to_excel('places_in_france.xlsx', index=False)
    print("\nSummary:")
    print(f"Total Addresses Processed: {processed_count}")
    print(f"Total Places Added: {added_count}")
    print(f"Total Places Filtered: {filtered_count}")
    print("Results saved to 'places_in_france.xlsx'")

if __name__ == '__main__':
    main()
