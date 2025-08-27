import os
import requests
import time
import threading
from datetime import datetime
from queue import Queue

task_queue = Queue()

TIMEZONE = ''                       # Europe/Munich
DOMAIN = ''                         # https://www.myaudiobookserver.com
LIBRARY_ID = ''                     # Audiobookshelf > Settings > Libraries
MAX_PARALLEL_CONVERSIONS = 2        # Recommend no more than the number of CPU cores
TOKEN = ''                          # Audiobookshelf > Settings > Users > (username) > API Token
CODEC = 'aac'                       # aac, mp3, or copy

mandatory_vars = {
    'DOMAIN': DOMAIN,
    'LIBRARY_ID': LIBRARY_ID,
    'TOKEN': TOKEN
}

for var_name, var_value in mandatory_vars.items():
    if not var_value:
        print(f'{var_name} is mandatory, exiting')
        exit()

def extract_items(response_obj):
    items = []
    if isinstance(response_obj, list):
        for item in response_obj:
            items.extend(extract_items(item))
    elif isinstance(response_obj, dict):
        if all(key in response_obj for key in ['id', 'libraryId', 'media']):
            if response_obj['mediaType'] == 'book' and 'title' in response_obj['media']['metadata']:
                items.append(response_obj)
    return items

def get_item(item_id):
    try:
        response = requests.get(f"{DOMAIN}/api/items/{item_id}", 
                                headers={'Authorization': f'Bearer {TOKEN}'})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching item {item_id}: {e}")
        return None

def construct_conversion_url(item_id, item_bitrate, item_channels):
    """Constructs the request URL for item conversion based on the codec."""
    request_url = f"{DOMAIN}/api/tools/item/{item_id}/encode-m4b?token={TOKEN}"

    if CODEC == 'copy':
        request_url += "&codec=copy"
    else:
        standard_bitrate = convert_bitrate_to_standard(item_bitrate)

        request_url += f"&codec={CODEC}&bitrate={standard_bitrate}&channels={item_channels}"

    return request_url

def convert_bitrate_to_standard(bitrate_bytes):
    bitrate_kbps = bitrate_bytes / 1024
    standard_bitrates = [64, 128, 192, 256, 320]

    nearest_bitrate = min(standard_bitrates, key=lambda x: abs(x - bitrate_kbps))

    return f"{nearest_bitrate}k"

def convert_item(item):
    item_id = item['id']
    expected_library_id = item['libraryId']

    try:
        item_data = get_item(item_id)

        if has_audio_files(item_data):
            item_codec = item_data['media']['audioFiles'][0]['codec']
            item_bitrate = item_data['media']['audioFiles'][0]['bitRate']
            item_channels = item_data['media']['audioFiles'][0]['channels']

            if CODEC == 'copy' or CODEC != item_codec:
                request_url = construct_conversion_url(item_id, item_bitrate, item_channels)

                response = requests.post(request_url)
                response.raise_for_status()
                print(f"Item {item_id} conversion queued successfully. "
                      f"(Bitrate: {item_bitrate}. Channels: {item_channels}. "
                      f"Original Codec: {item_codec}. Requested Codec: {CODEC})")
                task_queue.put(item_id)
            else:
                print(f"Item {item_id} conversion not queued. "
                      f"(Bitrate: {item_bitrate}. Channels: {item_channels}. "
                      f"Original Codec: {item_codec}. Requested Codec: {CODEC})")
    except requests.RequestException as e:
        print(f"Error converting item {item_id}: {e}")

def has_audio_files(item_data):
    if (item_data and 
        'media' in item_data and 
        'audioFiles' in item_data['media'] and 
        isinstance(item_data['media']['audioFiles'], list) and 
        len(item_data['media']['audioFiles']) > 0):
        return True
    else:
        return False

def monitor_tasks():
    while True:
        if not task_queue.empty():
            library_item_id = task_queue.get()
            try:
                response = requests.get(f"{DOMAIN}/api/tasks", headers={'Authorization': f'Bearer {TOKEN}'})
                response.raise_for_status()
                tasks = response.json().get('tasks', [])

                task = next((task for task in tasks if task['data']['libraryItemId'] == library_item_id), None)

                if task:
                    print(f"Task ID: {task['id']} | Status: {'Finished' if task['isFinished'] else 'In Progress' if not task['isFailed'] else 'Failed'}")

                    if task['isFinished']:
                        print("Task completed successfully.")
                        post_scan_request(library_item_id)
                        continue
                    elif task['isFailed']:
                        print("Task failed.")
                        continue
                else:
                    print(f"No task found for library item ID {library_item_id}. Assuming task is completed.")
                    post_scan_request(library_item_id)
                    continue

            except requests.RequestException as e:
                print(f"Error checking task status: {e}")

            task_queue.put(library_item_id)

        time.sleep(30)

def post_scan_request(library_item_id):
    try:
        response = requests.post(f"{DOMAIN}/api/items/{library_item_id}/scan", headers={'Authorization': f'Bearer {TOKEN}'})
        response.raise_for_status()
        print(f"Scan request posted successfully for library item ID {library_item_id}.")
    except requests.RequestException as e:
        print(f"Error posting scan request for library item ID {library_item_id}: {e}")

def count_running_tasks():
    try:
        response = requests.get(f"{DOMAIN}/api/tasks", headers={'Authorization': f'Bearer {TOKEN}'})
        response.raise_for_status()
        tasks = response.json().get('tasks', [])

        running_tasks = sum(1 for task in tasks if task['action'] == 'encode-m4b' and not task['isFinished'] and not task['isFailed'])
        return running_tasks
    except requests.RequestException as e:
        print(f"Error counting running tasks: {e}")
        return 0

def start_conversion_process():
    page = 0
    limit = 50
    total_items = 0
    current_tasks = 0

    while True:
        try:
            url = f"{DOMAIN}/api/libraries/{LIBRARY_ID}/items?limit={limit}&page={page}"
            headers = {'Authorization': f'Bearer {TOKEN}'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            total_items = data.get('total', 0)
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Fetching page {page} | Total items: {total_items}")

            items = extract_items(data.get('results', []))
            print(f"Extracted {len(items)} items from page {page}.")

            if not items:
                print("No items to process, exiting.")
                break

            for item in items:
                while count_running_tasks() >= MAX_PARALLEL_CONVERSIONS:
                    print("Maximum number of running tasks reached. Waiting...")
                    time.sleep(30)

                convert_item(item)

            if (page + 1) * limit >= total_items:
                print("All items have been processed.")
                break

            page += 1

        except requests.RequestException as e:
            print(f"Error: {e}")
            break

monitor_thread = threading.Thread(target=monitor_tasks, daemon=True)
monitor_thread.start()

if __name__ == "__main__":
    start_conversion_process()
