import datetime
import pandas as pd
import os
import requests
import zipfile
import io
import json
import base64

print("Starting the script...")

# Stupid approach to hide the link
DOWNLOADER_LINK = "".join([
    base64.b64decode("aHR0cHM6Ly9hdWRpb2Nkbi5lY29ub21pc3QuY29tL3NpdGVzL2RlZmF1bHQvZmlsZXMvQXVkaW9BcmNoaXZlLw==").decode("utf-8"),
    "{0}/{2}",
    base64.b64decode("L0lzc3VlXw==").decode("utf-8"),
    "{1}_{2}",
    base64.b64decode("X1RoZV9FY29ub21pc3RfRnVsbF9lZGl0aW9uLnppcA==").decode("utf-8")])


def generate_link() -> str:
    all_links = []

    schedule_day = pd.date_range(
        start=pd.to_datetime("1/1/2024").tz_localize("Europe/Berlin"),
        end=pd.to_datetime(datetime.datetime.now()).tz_localize("Europe/Berlin")
        ,freq='W-SAT')
    weeks=0

    for i in schedule_day:
        year = i.strftime('%Y')
        month = i.strftime('%m')
        day = i.strftime('%d')
        date = i.strftime('%Y%m%d')
        issue = 9378+weeks
        if ((int(month) != 12) or (int(day) < 25)):
            if not ((int(year) >= 2022) and (int(year) <=2023) and (int(month) == 8) and (int(day) <= 7)):
                all_links.append(DOWNLOADER_LINK.format(year, issue, date))
                weeks=weeks+1
                
    return all_links[-1]


# Function to load configuration from a file
def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
            return config
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error parsing the configuration file {config_file}.")
        exit(1)


# Function to check if URL was previously downloaded
def is_downloaded(url, download_tracker_file):
    if os.path.exists(download_tracker_file):
        with open(download_tracker_file, 'r') as file:
            downloaded_urls = file.read().splitlines()
        return url in downloaded_urls
    return False

# Function to append a URL to the download tracker file
def mark_as_downloaded(url, download_tracker_file):
    with open(download_tracker_file, 'a') as file:
        file.write(url + '\n')

# Function to extract the ZIP file name from the URL
def get_zip_file_name(url):
    return os.path.basename(url)

# Function to download and extract the zip file
def download_and_extract_zip(url, output_dir, download_tracker_file):
    try:
        # Check if URL has already been downloaded
        if is_downloaded(url, download_tracker_file):
            print(f"{url} has already been downloaded.")
            return

        # Download the zip file
        print(f"Downloading {url}...")
        response = requests.get(url)
        response.raise_for_status()
        print(f"Finished download...")

        # Extract the ZIP file name to use as the subfolder name (without .zip extension)
        zip_file_name = get_zip_file_name(url)
        if zip_file_name.endswith('.zip'):
            output_subfolder = zip_file_name[:-4]  # Remove '.zip' extension
        else:
            output_subfolder = zip_file_name

        # Create subfolder inside the output directory
        subfolder_path = os.path.join(output_dir, output_subfolder)
        os.makedirs(subfolder_path, exist_ok=True)

        # Extract the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(subfolder_path)

        # Mark URL as downloaded
        mark_as_downloaded(url, download_tracker_file)
        print(f"Downloaded and extracted: {url} into {subfolder_path}")

    except requests.exceptions.RequestException as req_err:
        print(f"Error downloading {url}: {req_err}")
    except zipfile.BadZipFile as zip_err:
        print(f"Error extracting zip file: {zip_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage
if __name__ == "__main__":
    # Load the configuration file
    config_file = 'config.json'
    config = load_config(config_file)
    
    output_dir = config.get('output_dir', './output')  # Default to './output' if not specified

    download_tracker_file =  config.get('download_log', 'downloaded_files.txt')  # File to track downloaded URLs

    # Download and extract the last URL in the list
    download_and_extract_zip(generate_link(), output_dir, download_tracker_file)
print("Finished running the script.")