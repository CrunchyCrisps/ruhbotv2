import requests
import json
import time
import os.path

start_time = time.time()
last_time = time.time()
url = 'https://swarfarm.com/api/bestiary'
r1 = requests.get(url, headers={'Accept':'application/json',
                                'Content-Type':'application/json',})
response1 = r1.json()
updated = []

for monster in response1:
    url2 = monster['url']
    name = monster['name']
    r2 = requests.get(url2, headers={'Accept':'application/json',
                                'Content-Type':'application/json',})
    data = r2.json()

    if data['is_awakened'] is False:
        name = '{} {}'.format(monster['element'], name)

    if os.path.isfile('monsters/{}.json'.format(name)):
        current_data = open('monsters/{}.json'.format(name))
        data2 = json.load(current_data)
    else:
        data2 = data

    if data == data2:
        print('{} - Data unchanged. - {}'.format(name, time.time()-last_time))
        last_time = time.time()
    else:
        with open('monsters/{}.json'.format(name), 'w') as outfile:
            json.dump(data, outfile)
        print('{} - Data changed. - {}'.format(name, time.time()-last_time))
        last_time = time.time()
        updated.append(name)

print(time.time()-start_time)
print(updated)
