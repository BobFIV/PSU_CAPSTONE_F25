import requests
from django.shortcuts import render
from django.http import JsonResponse

# ---------------- CONFIG ----------------
BASE_URL = "http://54.164.106.20:8080"
HEADERS = {
    "X-M2M-Origin": "CAdmin",
    "X-M2M-RVI": "3",
    "Accept": "application/json",
}

# List of known AEs and their URLs 
# ADD YOUR AE ENDPOINT HERE
AE_ENDPOINTS = {
    "Device_2": f"{BASE_URL}/CDevice2",
    "DummyData": f"{BASE_URL}/ColesLaptop",  
    "Device_1": f"{BASE_URL}/CDevice1",      
}

def login_view(request):
    return render(request, "ui/login.html")  # Render the login page when visiting root URL

def logout_view(request):
    return render(request, "ui/login.html")  # Render the login page when visiting root URL

# Home page (After login)
def home(request):
    return render(request, "ui/home.html")  # This renders the home page

# ---------------- AE FETCH HELPER ----------------
def get_ae_name_from_url(url):
    """
    Reusable helper to fetch AE name from a given URL.
    Returns AE name string if found, else None.
    """
    headers = HEADERS | {"X-M2M-RI": "req_getAE"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            ae_name = data.get("m2m:ae", {}).get("rn")
            return ae_name
    except requests.exceptions.RequestException:
        pass
    return None

# ---------------- DEVICE LIST VIEW ----------------
def devices_list(request):
    """
    Fetch all AE names from known endpoints and display in devices list.
    """
    devices = []

    for label, url in AE_ENDPOINTS.items():
        ae_name = get_ae_name_from_url(url)
        if ae_name:
            devices.append(ae_name)
    devices.sort(key=lambda name: name.lower())
    return render(request, "ui/devices_list.html", {"devices": devices})

# ---------------- CONTAINER DATA HELPER ----------------
def get_container_data(ae_name, container_name):
    """
    Fetch latest content instance for a given AE/container.
    """
    url = f"{BASE_URL}/cse-in/{ae_name}/{container_name}/la"
    headers = HEADERS | {"X-M2M-RI": f"req_{ae_name}_{container_name}"}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return {}

# ---------------- DEVICE DETAIL VIEW ----------------
def device_detail(request, device_name):
    """
    Display all container values for a given AE.
    """
    containers = ['battery', 'temperature', 'signal', 'humidity']
    container_data = {}

    for container in containers:
        data = get_container_data(device_name, container)
        container_data[container] = data.get("m2m:cin", {}).get("con")

    container_data_for_template = [
        (name, container_data[name]) for name in containers
    ]

    return render(
        request,
        'ui/device_detail.html',
        {'device_name': device_name, 'container_data': container_data_for_template},
    )
