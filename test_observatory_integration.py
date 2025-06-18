import requests
import json

# Test if the app is running
try:
    response = requests.get("http://127.0.0.1:8052/")
    print(f"App is running: {response.status_code == 200}")
except Exception as e:
    print(f"App not accessible: {e}")
    exit(1)

# Test if we can access the Observatory page by simulating navigation
# Dash apps use a specific format for callback requests
callback_url = "http://127.0.0.1:8052/_dash-update-component"

# Simulate clicking on the Observatory nav button
nav_click_payload = {
    "output": "..main-content-area.children.....active-page-store.data.....nav-pricing-monkey.style.....nav-analysis.style.....nav-greek-analysis.style.....nav-logs.style.....nav-project-docs.style.....nav-scenario-ladder.style.....nav-actant-eod.style.....nav-actant-pnl.style.....nav-observatory.style..",
    "outputs": [
        {"id": "main-content-area", "property": "children"},
        {"id": "active-page-store", "property": "data"},
        {"id": "nav-pricing-monkey", "property": "style"},
        {"id": "nav-analysis", "property": "style"},
        {"id": "nav-greek-analysis", "property": "style"},
        {"id": "nav-logs", "property": "style"},
        {"id": "nav-project-docs", "property": "style"},
        {"id": "nav-scenario-ladder", "property": "style"},
        {"id": "nav-actant-eod", "property": "style"},
        {"id": "nav-actant-pnl", "property": "style"},
        {"id": "nav-observatory", "property": "style"}
    ],
    "inputs": [
        {"id": "nav-pricing-monkey", "property": "n_clicks", "value": None},
        {"id": "nav-analysis", "property": "n_clicks", "value": None},
        {"id": "nav-greek-analysis", "property": "n_clicks", "value": None},
        {"id": "nav-logs", "property": "n_clicks", "value": None},
        {"id": "nav-project-docs", "property": "n_clicks", "value": None},
        {"id": "nav-scenario-ladder", "property": "n_clicks", "value": None},
        {"id": "nav-actant-eod", "property": "n_clicks", "value": None},
        {"id": "nav-actant-pnl", "property": "n_clicks", "value": None},
        {"id": "nav-observatory", "property": "n_clicks", "value": 1}  # Simulate click on Observatory
    ],
    "state": [
        {"id": "active-page-store", "property": "data", "value": "pricing-monkey"}
    ],
    "changedPropIds": ["nav-observatory.n_clicks"]
}

try:
    headers = {"Content-Type": "application/json"}
    response = requests.post(callback_url, json=nav_click_payload, headers=headers)
    
    if response.status_code == 200:
        print("Observatory navigation successful")
        data = response.json()
        
        # Check if response contains error
        if "error" in data.get("response", {}):
            print(f"Error in response: {data['response']['error']}")
        else:
            print("Observatory page loaded successfully")
            # The first output should be the page content
            if data.get("response") and len(data["response"]) > 0:
                content = data["response"]["main-content-area"]["children"]
                # Check if it's an error div
                if isinstance(content, dict) and content.get("props", {}).get("style", {}).get("color") == "red":
                    print(f"Error loading Observatory: {content.get('props', {}).get('children', 'Unknown error')}")
                else:
                    print("Observatory content loaded without errors")
    else:
        print(f"Failed to navigate to Observatory: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"Error testing Observatory: {e}") 