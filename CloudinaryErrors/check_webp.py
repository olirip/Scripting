import json
import urllib.request
import urllib.error
import time

# Read the rolex no-rswi JSON file
print("Reading cloudinary_errors_rolex_no_rswi.json...")
with open('cloudinary_errors_rolex_no_rswi.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Track statistics
total_webp_jpg_found = 0
checked_urls = set()  # To avoid checking the same URL multiple times
webp_checks_to_add = []  # Store checks to add after iteration

print("Scanning for .webp.jpg images and checking their .webp versions...")
print("-" * 80)

# Process the data
for url_key, url_value in data.items():
    if isinstance(url_value, dict):
        for user_agent, user_agent_value in url_value.items():
            if isinstance(user_agent_value, dict):
                for status_code, status_value in user_agent_value.items():
                    if isinstance(status_value, dict):
                        for image_key, image_urls in list(status_value.items()):
                            if isinstance(image_urls, list):
                                for image_url in image_urls:
                                    # Check if the URL ends with .webp.jpg
                                    if image_url.endswith('.webp.jpg'):
                                        # Create the .webp version URL
                                        webp_url = image_url[:-4]  # Remove the .jpg extension

                                        # Skip if we've already checked this URL
                                        if webp_url in checked_urls:
                                            continue

                                        checked_urls.add(webp_url)
                                        total_webp_jpg_found += 1

                                        # Check the webp version
                                        try:
                                            print(f"Checking [{total_webp_jpg_found}]: {webp_url}")
                                            req = urllib.request.Request(
                                                webp_url,
                                                method='HEAD'
                                            )
                                            with urllib.request.urlopen(req, timeout=10) as response:
                                                webp_status = response.status
                                            print(f"  → Status: {webp_status}")

                                            # Store the check result
                                            webp_checks_to_add.append({
                                                'url_key': url_key,
                                                'user_agent': user_agent,
                                                'status_code': status_code,
                                                'image_key': image_key,
                                                'check_data': {
                                                    "original_url": image_url,
                                                    "webp_url": webp_url,
                                                    "webp_status": webp_status
                                                }
                                            })

                                            # Be nice to the server
                                            time.sleep(0.5)

                                        except urllib.error.HTTPError as e:
                                            print(f"  → HTTP Status: {e.code}")
                                            # Store the check result
                                            webp_checks_to_add.append({
                                                'url_key': url_key,
                                                'user_agent': user_agent,
                                                'status_code': status_code,
                                                'image_key': image_key,
                                                'check_data': {
                                                    "original_url": image_url,
                                                    "webp_url": webp_url,
                                                    "webp_status": e.code
                                                }
                                            })
                                            time.sleep(0.5)
                                        except Exception as e:
                                            print(f"  → Error: {str(e)}")
                                            # Store the check result
                                            webp_checks_to_add.append({
                                                'url_key': url_key,
                                                'user_agent': user_agent,
                                                'status_code': status_code,
                                                'image_key': image_key,
                                                'check_data': {
                                                    "original_url": image_url,
                                                    "webp_url": webp_url,
                                                    "webp_status": f"error: {str(e)}"
                                                }
                                            })
                                            time.sleep(0.5)

print("-" * 80)
print(f"\nTotal .webp.jpg images found and checked: {total_webp_jpg_found}")

# Now add all the webp checks to the data
print("\nAdding webp check results to the JSON data...")
for check in webp_checks_to_add:
    url_key = check['url_key']
    user_agent = check['user_agent']
    status_code = check['status_code']
    image_key = check['image_key']
    check_data = check['check_data']

    status_value = data[url_key][user_agent][status_code]

    if "webp_check" not in status_value:
        status_value["webp_check"] = {}
    if image_key not in status_value["webp_check"]:
        status_value["webp_check"][image_key] = []

    status_value["webp_check"][image_key].append(check_data)

# Write the updated JSON back
print(f"Writing updated JSON to cloudinary_errors_rolex_no_rswi_with_webp_check.json...")
with open('cloudinary_errors_rolex_no_rswi_with_webp_check.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\nDone! Updated file created:")
print("- cloudinary_errors_rolex_no_rswi_with_webp_check.json")
