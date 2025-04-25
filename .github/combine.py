import json
from glob import glob
from collections import defaultdict

files = sorted(glob("byLocations/byLocation-*.json"))

final_dict = {
    "totalProfiles": 0,
    "locations": {
        "totalCountries": 0,
        "byNames": set(),
        "byCountryCode": set()
    },
    "profilesByCountryCode": defaultdict(list),
    "profilesByCountryName": defaultdict(list)
}

for file in files:
    with open(file, "r") as f:
        data = json.load(f)

        final_dict["totalProfiles"] += data.get("totalProfiles", 0)

        final_dict["locations"]["byNames"].update(data["locations"]["byNames"])
        final_dict["locations"]["byCountryCode"].update(data["locations"]["byCountryCode"])

        for k, urls in data.get("profilesByCountryCode", {}).items():
            final_dict["profilesByCountryCode"][k].extend(urls)

        for k, urls in data.get("profilesByCountryName", {}).items():
            final_dict["profilesByCountryName"][k].extend(urls)

# Remove duplicates at the end
for k in final_dict["profilesByCountryCode"]:
    final_dict["profilesByCountryCode"][k] = list(set(final_dict["profilesByCountryCode"][k]))

for k in final_dict["profilesByCountryName"]:
    final_dict["profilesByCountryName"][k] = list(set(final_dict["profilesByCountryName"][k]))

final_dict["locations"]["byNames"] = list(final_dict["locations"]["byNames"])
final_dict["locations"]["byCountryCode"] = list(final_dict["locations"]["byCountryCode"])
final_dict["locations"]["totalCountries"] = len(final_dict["locations"]["byCountryCode"])

final_dict["profilesByCountryCode"] = dict(final_dict["profilesByCountryCode"])
final_dict["profilesByCountryName"] = dict(final_dict["profilesByCountryName"])

with open("byLocations/merged.json", "w") as f:
    json.dump(final_dict, f, indent=2)
