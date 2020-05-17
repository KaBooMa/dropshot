#!/usr/bin/python3
"""
Goals of Project:
Easily spin up/down my development server
Allow spinning up the server with a few different cpu/mem options by choice
Perform a snapshot before shutting down. Use snapshot when creating to maintain my "state"
"""

import requests, config, json, time

headers = {
    'Authorization': 'Bearer %s' % config.token
}

###########
# Droplets
def get_droplets():
    response = requests.get('https://api.digitalocean.com/v2/droplets', headers=headers)
    data = response.json()['droplets']
    return data


def get_managed_droplet():
    droplets = get_droplets()
    for droplet in droplets:
        if droplet['name'] == config.droplet_name:
            if droplet['status'] != 'active':
                time.sleep(1)
                return get_managed_droplet()
            else:
                return droplet

    return None


def delete_droplet():
    print('Deleting droplet...')
    droplet = get_managed_droplet()
    droplet_id = droplet['id']
    requests.delete(f'https://api.digitalocean.com/v2/droplets/{droplet_id}', headers=headers)

def get_sizes():
    print('Collecting size options...')
    response = requests.get('https://api.digitalocean.com/v2/sizes', headers=headers)
    data = response.json()['sizes']
    return data


def get_regions():
    print('Collecting region options...')
    response = requests.get('https://api.digitalocean.com/v2/regions', headers=headers)
    data = response.json()['regions']
    return data


def get_images():
    print('Collecting image options...')
    response = requests.get('https://api.digitalocean.com/v2/images?type=distribution', headers=headers)
    data = response.json()['images']
    return data


def get_keys():
    print('Collecting SSH Key options...')
    response = requests.get('https://api.digitalocean.com/v2/account/keys', headers=headers)
    data = response.json()['ssh_keys']
    return data


def print_results(results, columns):
    for result in results:
        result_values = []
        for column in columns:
            value = result[column]
            result_values.append(str(value))

        print(', '.join(result_values))


def create_droplet(size, image_id):
    print('Creating droplet...')
    droplet_info = {
        'name': config.droplet_name,
        'region': config.region,
        'size': size,
        'image': image_id or config.default_image,
        'backups': False,
        'ipv6': False,
        'private_networking': False,
        'ssh_keys': config.ssh_keys
    }
    response = requests.post('https://api.digitalocean.com/v2/droplets', headers=headers, data=droplet_info)
    data = response.json()


def managed_ipv4():
    print('Collecting IPv4...')
    droplet = get_managed_droplet()
    networks = droplet['networks']
    v4 = networks['v4']
    first_entry = v4[0]
    ip_address = first_entry['ip_address']
    return ip_address


############
# Snapshots
def get_snapshots():
    print('Collecting snapshot data...')
    response = requests.get('https://api.digitalocean.com/v2/snapshots', headers=headers)
    data = response.json()
    print(data)
    if 'snapshots' in data:
        return data['snapshots']

    print('No Snapshots Found')
    return [] 

def get_managed_snapshot():
    snapshots = get_snapshots()
    for snapshot in snapshots:
        if snapshot['name'] == config.snapshot_name:
            return snapshot

    return None

def delete_snapshot():
    print('Deleting snapshot...')
    snapshot = get_managed_snapshot()
    snapshot_id = snapshot['id']
    response = requests.delete(f'https://api.digitalocean.com/v2/snapshots/{snapshot_id}', headers=headers)


def snapshot_droplet():
    print('Creating snapshot...')
    droplet = get_managed_droplet()
    droplet_id = droplet['id']
    request_data = {
        'type': 'snapshot',
        'name': config.snapshot_name 
    }
    response = requests.post(f'https://api.digitalocean.com/v2/droplets/{droplet_id}/actions', headers=headers, data=request_data)
    data = response.json()


def spin_down():
    snapshot_droplet()
    snapshot = get_managed_snapshot()
    while not snapshot:
        print('Waiting for snapshot to complete...')
        time.sleep(1)
        snapshot = get_managed_snapshot()

    delete_droplet()
    print('Droplet successfully spun down')


def spin_up():
    sizes = get_sizes()
    print_results(sizes, ['slug', 'price_monthly', 'vcpus', 'memory', 'disk'])
    size = input(f'Which size would you prefer? [default: {config.default_size}]: ')
    if size == '':
        size = config.default_size
    
    snapshot = get_managed_snapshot()
    if snapshot['id']:
        snapshot_id = snapshot['id']
    else:
        snapshot_id = config.default_image

    create_droplet(size, snapshot_id)
    ip_address = managed_ipv4()
    delete_snapshot()
    print('Droplet IP:', ip_address)


def main():
    droplet = get_managed_droplet()
    if droplet:
       print('Droplet currently running')
       ans = input('Would you like to spin it down? [y/n] ')
       if ans.lower() == 'y':
           spin_down()
           exit()
    else:
        print('Droplet currently destroyed')
        ans = input('Would you like to spin it up? [y/n] ')
        if ans.lower() == 'y':
            spin_up()
            exit()
    
    print()
    print('What would you like to do?')
    print('1. List SSH Keys')
    print('2. List Sizes')
    print('3. List Regions')
    print('4. List Images')
    ans = input(': ')
    if ans == '1':
        keys = get_keys()
        print_results(keys, ['id', 'name'])
    elif ans == '2':
        sizes = get_sizes()
        print_results(sizes, ['slug', 'price_monthly', 'memory', 'vcpus', 'disk'])
    elif ans == '3':
        regions = get_regions()
        print_results(regions, ['slug', 'name'])
    elif ans == '4':
        images = get_images()
        print_results(images, ['id', 'name', 'distribution'])

main()
