# encoding=utf8
import sys
import csv, re, os
import json
import requests
from pprint import pprint
import datetime

from unidecode import unidecode # This module does its best
# to convert Unicode (like "smart" quotes) to their ASCII
# equivalents.

reload(sys) # These lines, and the two at the top of the file, are
sys.setdefaultencoding('utf8') # needed to defeat this error:
#       UnicodeDecodeError: 'ascii' codec can't decode byte XXXXX

# The above is a Python 2 solution to this problem.
# There is another solution that I have used elsewhere that
# is reputed to be better.

def cast_to_utf8(u):
    if u is None:
        return u''
    return unicode(u).encode('utf-8')

def write_to_csv(filename,list_of_dicts,keys):
    # Stolen from parking-data util.py file.
    with open(filename, 'wb') as g:
        g.write(','.join(keys)+'\n')
    with open(filename, 'ab') as output_file:
        dict_writer = csv.DictWriter(output_file, keys, extrasaction='ignore', lineterminator='\n')
        #dict_writer.writeheader()
        dict_writer.writerows(list_of_dicts)

def convert_string_to_dt(s):
    s = re.sub("-\d\d:\d\d$","",s)
    dt = datetime.datetime.strptime(s,"%Y-%m-%dT%H:%M:%S")
    return dt

def remove_crs(s):
    # Replace carriage returns with slashes.
    s = re.sub("\r\n","/",s)
    s = re.sub("\n","/",s)
    return s

#url = "http://fishfry.codeforpgh.com/api/fishfrys/" # 2017 URL
url = "http://fishfry.codeforpgh.com/api/fishfries/" # 2018 URL

r = requests.get(url)
locations = r.json()['features']

print(locations[0])

list_of_fries = []
for feature in locations:
    fry = {}
    properties = feature['properties']
    for key in properties:
        if key == 'menu':
            fry['menu_text'] = unidecode(unicode(cast_to_utf8(properties[key]['text'])))
            fry['menu_url'] = unidecode(unicode(cast_to_utf8(properties[key]['url'])))

        elif key not in ['events','uuid']:
            fry[key] = properties[key]
            if isinstance(fry[key], unicode):
                fry[key] = remove_crs(unidecode(unicode(cast_to_utf8(fry[key]))))
        # It's actually OK if the menu has carriage returns in it. It makes
        # the CSV file look like it has more entries than it actually does, but
        # it gets imported into the Datastore properly.

                
    if 'cartodb_id' in fry:
        fry['id'] = fry['cartodb_id']
        del fry['cartodb_id']

    if 'geometry' in feature and feature['geometry'] is not None and 'coordinates' in feature['geometry']:
        lon, lat = feature['geometry']['coordinates']
        fry['latitude'] = lat
        fry['longitude'] = lon
    else:
        lat = lon = None

    if 'events' in properties:
        events = []
        for e in properties['events']:
            start = convert_string_to_dt(e['dt_start'])
            end = convert_string_to_dt(e['dt_end'])
            output = "{} from {} to {}".format(
                datetime.datetime.strftime(start,"%A %b %-d"),
                datetime.datetime.strftime(start,"%-I:%M %p"),
                datetime.datetime.strftime(end,"%-I:%M %p")
            )
            events.append(output)
        if events != []:
            fry['events'] = ', '.join(events)

    list_of_fries.append(fry)
pprint(list_of_fries[0])


keys = ['validated', 'venue_name', 'venue_type', 'venue_address', 'website', 'events', 'etc', 'menu_url', 'menu_text', 'venue_notes', 'phone', 'email',  'homemade_pierogies', 'take_out', 'alcohol', 'lunch', 'handicap', 'publish', 'id', 'latitude', 'longitude']

filename = '{}_Pittsburgh_Fish_Fry_Locations.csv'.format(datetime.datetime.now().year)
write_to_csv(filename,list_of_fries,keys)
