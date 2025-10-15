# ui/views.py
import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse

def login_view(request):
    return render(request, "ui/login.html")  # Render the login page when visiting root URL

def logout_view(request):
    return render(request, "ui/login.html")  # Render the login page when visiting root URL

# Home page (After login)
def home(request):
    return render(request, "ui/home.html")  # This renders the home page

# Function to get AEs from IN-CSE
def get_ae_names_from_cse():
    url = 'http://54.164.106.20:8080/ColesLaptop'  
    headers = {
        'X-M2M-Origin': 'CAdmin',
        'X-M2M-RVI': '3',
        'X-M2M-RI': 'tempReq2',
        'Accept': 'application/json'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "m2m:ae" in data:
            return [data["m2m:ae"]["rn"]]  # Return the AE's name as a list
        else:
            return []  # No AE found
    else:
        return []  # If request fails

# View for device list page (View 1)
def devices_list(request):
    # Fetch AE names from IN-CSE
    devices = get_ae_names_from_cse()  # Get AE names
    return render(request, "ui/devices_list.html", {"devices": devices})  # Pass devices to template

def get_container_data(ae_name, container_name):
    url = f'http://54.164.106.20:8080/cse-in/{ae_name}/{container_name}/la'  # Modify with actual URL
    headers = {
        'X-M2M-Origin': 'CAdmin',
        'X-M2M-RVI': '3',
        'X-M2M-RI': 'tempReq2',
        'Accept': 'application/json'
    }

    response = requests.get(url, headers=headers)

    # Return the data if successful
    if response.status_code == 200:
        return response.json()  # This will be the data from the container
    else:
        return {"error": "Failed to fetch container data"}  # Error handling

# Function to get container data for a device
def device_detail(request, device_name):
    # List of containers for this device
    containers = ['battery', 'temperature', 'signal', 'humidity']
    
    # Initialize an empty dictionary to store container data
    container_data = {}

    # Loop through each container and fetch its data
    for container in containers:
        data = get_container_data(device_name, container)
        # Extract just the 'cni' value from the container data
        cni_value = data.get("m2m:cin", {}).get("con", None)
        # Store the 'cni' value in the dictionary
        container_data[container] = cni_value
    
    
    # Pass the container data as a list of tuples (container_name, cni_value)
    container_data_for_template = [(container, container_data[container]) for container in containers]

    # Render the template and pass container data
    return render(request, 'ui/device_detail.html', {'device_name': device_name, 'container_data': container_data_for_template})
