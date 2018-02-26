#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow
from collections import defaultdict
from collections import OrderedDict
import re
import pandas as pd
import csv
import sqlite3
import codecs
from bs4 import BeautifulSoup

loc_nodes = 'C:/Users/Administrator/Desktop/nodes.csv'
loc_node_tags = 'C:/Users/Administrator/Desktop/node_tags.csv'
loc_ways = 'C:/Users/Administrator/Desktop/ways.csv'
loc_way_tags = 'C:/Users/Administrator/Desktop/way_tags.csv'
loc_way_nodes = 'C:/Users/Administrator/Desktop/way_nodes.csv'

OSM_FILE = "C:\\Users\\Administrator\\Desktop\\isle-of-wight-latest.osm"  # Replace this with your osm file
#OSM_FILE = "C:\\Users\\Administrator\\Desktop\\sample.osm"
SAMPLE_FILE = "C:\\Users\\Administrator\\Desktop\\sample.osm"

k = 1000 # Parameter: take every k-th top level element

#def get_element(osm_file, tags=('node', 'way', 'relation')):
#    """Yield element if it is the right type of tag
#
#    Reference:
#    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
#    """
#    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
#    _, root = next(context)
#    for event, elem in context:
#        if event == 'end' and elem.tag in tags:
#            yield elem
#            root.clear()
#
#
#with open(SAMPLE_FILE, 'wb') as output:
#    output.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
#    output.write(b'<osm>\n  ')
#
#    # Write every kth top level element
#    for i, element in enumerate(get_element(OSM_FILE)):
#        if i % k == 0:
#            output.write(ET.tostring(element, encoding='utf-8'))
#
#    output.write(b'</osm>')
#    print('Done')


def file_check(osm_file):
    data = defaultdict(int)
    tree = ET.parse(osm_file)
    for item in tree.iter():
        data[item.tag]+=1
    return data

def tag_check(osm_file):
    data = defaultdict(int)
    tree = ET.parse(osm_file)
    for item in tree.iter():
        if item.tag == 'tag':
            data[item.attrib['k']]+=1
    ordered = OrderedDict(data)
    new_order = OrderedDict(sorted(ordered.items(), key=lambda x: x[1]))
    return new_order
#print(tag_check(OSM_FILE))

def street_name_check(osm_file):
    data = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=('start',)):
        if elem.tag == 'way':
            for tag in elem.iter('tag'):
                tag.attrib['k'].lower()
                if tag.attrib['k'] == 'addr:street':
                    value = tag.attrib['v']
                    if ' ' not in value:
                        value = value[0].upper() + value[1:]
                        data[value].add(value)
                    else:
                        value = [i[0].upper() + i[1:] for i in value.split(' ')]
                        data[value[-1]].add(' '.join(value))
    return data
#print(street_name_check(OSM_FILE))
                        
def update_tag(osm_file):
    tree = ET.parse(osm_file)
    for item in tree.iter('tag'):
        if item.attrib['k'] == 'roadhttp://wightpaths.co.uk/rowmaptiles/{zoom}/{x}/{y}.png':
            item.attrib['k'] = 'road'
            item.attrib['v'] = 'leeson road'
        else:
            item.attrib['k'].lower()
            item.attrib['v'].lower()
    
def tag_audit(osm_file):
    tree = ET.parse(osm_file)
    root = tree.getroot()
    target = root.find('way')
    return target
    


    
def amenity_check(osm_file):
    data = defaultdict(int)
    tree = ET.parse(osm_file)
    for item in tree.iter():
        if item.tag == 'tag':
            if item.attrib['k'] == 'amenity':
                data[item.attrib['v']] += 1
    ordered = OrderedDict(data)
    new_order = OrderedDict(sorted(ordered.items(), key=lambda x: x[1]))
    return new_order
             
    
def postcode_check(osm_file):
    data = defaultdict(int)
    tree = ET.parse(osm_file)

    for item in tree.iter():
        if item.tag == 'tag':
            if item.attrib['k'] == 'addr:postcode':
                data[item.attrib['v']] += 1
                if len(item.attrib['v']) == 4:
                    print(item.attrib['v'])
    keys = data.keys()
    pattern = re.compile(r'^[A-Z]{2}[0-9]{1,2}\s?[0-9]?[A-Z]{0,2}')
    print(all([pattern.match(key) for key in keys]))
#    for key in keys:
#        if not pattern.match(key):
#            print(key)
#    return data
                


NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']



def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    pattern = re.compile(r'.*http')

    #deals with way tags and their children tags
    if element.tag == 'way':
        nodes = element.findall('nd')
        pos = 0
        for n in range(len(way_attr_fields)):
            way_attribs[way_attr_fields[n]] = element.attrib[way_attr_fields[n]]
        way_id = way_attribs['id']
        for item in nodes:
            item_attrib = {}
            item_attrib['id'] = way_id
            item_attrib['node_id'] = item.attrib['ref']
            item_attrib['position'] = pos
            
            way_nodes.append(item_attrib)
            pos +=1

        all_tags = element.findall('tag')

        for i in all_tags:
            key = i.attrib['k'].lower()
            child_attrib = {}
            #deal with irregular street names
            if i.attrib['k'] and i.attrib['k'] == 'addr:street' and pattern.search(i.attrib['v']):
                i.attrib['v'] = i.attrib['v'].split('http')[0]
            #update street name spelling
            value = i.attrib['v']
            if 'addr:street' in key and ' ' not in value:
                value = value[0].upper() + value[1:]
            elif 'addr:street' in key and ' ' in value:
                value = ' '.join([i[0].upper() + i[1:] for i in value.split(' ')])

            
            #output child_attrib
            if ":" in key and len(key.split(":")) >= 2:
                child_attrib['type'] = key.split(':')[0]
                child_attrib['key'] = ':'.join(key.split(':')[1:])
                child_attrib['id'] = way_id
                child_attrib['value'] = value
            else:
                child_attrib['type'] = 'regular'
                child_attrib['key'] = key
                child_attrib['id'] = way_id
                child_attrib['value'] = value

            tags.append(child_attrib)

    #deal with node tags and their children tags               
    elif element.tag == 'node':
        for n in range(len(node_attr_fields)):
            node_attribs[node_attr_fields[n]] = element.attrib[node_attr_fields[n]]     
        node_id = node_attribs['id']
        
        all_tags = element.findall('tag')

        for i in all_tags:
            key = i.attrib['k'].lower()
            child_attrib = {}

            #update street name spelling
            value = i.attrib['v']
            if 'addr:street' in key and ' ' not in value:
                value = value[0].upper() + value[1:]
            elif 'addr:street' in key and ' ' in value:
#                print(value.split(' '))
                value = ' '.join([i[0].upper() + i[1:] for i in value.split(' ')]) 

      

#                value = ' '.join([i[0].upper() + i[1:] for i in value.split(' ')])
#                value = [i[0].upper() + i[1:] for i in value.split(' ')]
#                for i in value.split(' '):
#                    print(i)
#                    break
                
            #output child_attrib
            if ":" in key and len(key.split(":")) > 1:
                child_attrib['type'] = key.split(':')[0]
                child_attrib['key'] = ':'.join(key.split(':')[1:])
                child_attrib['id'] = node_id
                child_attrib['value'] = value
            else:
                child_attrib['type'] = 'regular'
                child_attrib['key'] = i.attrib['k']
                child_attrib['id'] = node_id
                child_attrib['value'] = value

            tags.append(child_attrib)


    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
    
def process_map(osm_file):
    nodes, node_tags, ways, way_tags, way_nodes = [], [], [], [], []
    
    #store data in different lists
    for _, element in ET.iterparse(osm_file):
        if element.tag == 'node':
            nodes.append(shape_element(element)['node'])
            sep_node_tags = shape_element(element)['node_tags']
            if sep_node_tags != None:
                for node_tag in range(len(sep_node_tags)):
                    node_tags.append(sep_node_tags[node_tag])
        elif element.tag == 'way':
            ways.append(shape_element(element)['way'])
            sep_way_tags = shape_element(element)['way_tags']
            if sep_way_tags != None:
                for way_tag in range(len(sep_way_tags)):
                    way_tags.append(sep_way_tags[way_tag])
                    
            sep_way_nodes = shape_element(element)['way_nodes']
            if sep_way_nodes != None:
                for way_node in range(len(sep_way_nodes)):
                    way_nodes.append(sep_way_nodes[way_node])

    #create dataframes and get ready to export            
    df_nodes, df_node_tags, df_ways, df_way_nodes, df_way_tags = pd.DataFrame(nodes), pd.DataFrame(node_tags), pd.DataFrame(ways), pd.DataFrame(way_tags), pd.DataFrame(way_nodes)    
    print('Data Created!')
    return df_nodes, df_node_tags, df_ways, df_way_nodes, df_way_tags
#    return df_node_tags.dropna()
    
    
def to_csv(OSM_FILE):
    df_nodes, df_node_tags, df_ways, df_way_nodes, df_way_tags = process_map(OSM_FILE)    
    #export dataframes to csv
    df_nodes.to_csv('nodes.csv', index=False, sep=',', encode='utf-8')
    print('Exported 1!')
    df_node_tags.to_csv('node_tags.csv', index=False, sep=',', encode='utf-8')
    print('Exported 2!')
    df_ways.to_csv('ways.csv', index=False, sep=',', encode='utf-8')
    print('Exported 3!')
    df_way_nodes.to_csv('way_nodes.csv', index=False, sep=',', encode='utf-8')
    print('Exported 4!')
    df_way_tags.to_csv('way_tags.csv', index=False, sep=',', encode='utf-8')
    print('Exported all!!!')
                

    
    
#print(process_map(OSM_FILE))
print(to_csv(OSM_FILE))

def check_irregular_tags(OSM_FILE):
    data = []
#    keys = set()
    pattern = re.compile(r'.*http')
#    pattern1 = re.compile(r'roadhttp://wightpaths.co.uk/rowmaptiles/{zoom}/{x}/{y}.png')
    for event, elem in ET.iterparse(OSM_FILE, events=('start',)):

        for item in elem.iter('tag'):

            if item.attrib['k'] == 'addr:street' and pattern.search(item.attrib['v']):
                data.append(item.attrib.items())
#                keys.add(item.attrib['k'])
    return data
#print(check_irregular_tags(OSM_FILE))



def import_csv(loc_nodes, loc_node_tags, loc_ways, loc_way_tags, loc_way_nodes):
    db_name = 'C:/Users/Administrator/Desktop/osm.db'
    conn = sqlite3.connect(db_name)
    
    with codecs.open(loc_nodes, 'r', encoding='utf-8', errors='ignore') as nodes:
        df_nodes = pd.read_csv(nodes)
    with codecs.open(loc_node_tags, 'r', encoding='utf-8', errors='ignore') as node_tags:
        df_node_tags = pd.read_csv(node_tags)
 
    with codecs.open(loc_ways, 'r', encoding='utf-8', errors='ignore') as ways:
        df_ways = pd.read_csv(ways)
    with codecs.open(loc_way_tags, 'r', encoding='utf-8', errors='ignore') as way_tags:
        df_way_tags = pd.read_csv(way_tags)
    with codecs.open(loc_way_nodes, 'r', encoding='utf-8', errors='ignore') as way_nodes:
        df_way_nodes = pd.read_csv(way_nodes)
        
#    df_nodes = pd.read_csv(loc_nodes)
#    df_node_tags = pd.read_csv(loc_node_tags)
#    df_ways = pd.read_csv(loc_ways)
#    df_way_tags = pd.read_csv(loc_way_tags)
#    df_way_nodes = pd.read_csv(loc_way_nodes)
    
#    df_nodes = csv.reader(open(loc_nodes, 'r'), delimiter=',', quotechar='"')
#    df_node_tags = csv.reader(open(loc_node_tags, 'r'), delimiter=',', quotechar='"')
#    df_ways = csv.reader(open(loc_ways, 'r'), delimiter=',', quotechar='"')
#    df_way_tags = csv.reader(open(loc_way_tags, 'r'), delimiter=',', quotechar='"')
#    df_way_nodes = csv.reader(open(loc_way_nodes, 'r'), delimiter=',', quotechar='"')
    
    df_nodes.to_sql('nodes', conn, index=False, low_memory=False)
    df_node_tags.to_sql('node_tags', conn, index=False)
    df_ways.to_sql('ways', conn, index=False)
    df_way_tags.to_sql('way_tags', conn, index=False)
    df_way_nodes.to_sql('way_nodes', conn, index=False)
    print('Done')


    
    
#print(import_csv(loc_nodes, loc_node_tags, loc_ways, loc_way_tags, loc_way_nodes))


def naptan_check(osm_file):
    #store data in different lists
    tree = ET.parse(osm_file)
    root = tree.getroot()
    for i in root.getchildren():
        if i.getchildren():
            for n in i.iter(): 
                if n.getchildren():
                    for item in n.iter():
                        if item.getchildren():
                            for lastlevel in item.iter():
                                
                                if lastlevel.tag == 'tag':
                                    if 'naptan:' in lastlevel.attrib['k']:
                                        print(ET.tostring(item))
                                        break
                        break
                break
              
            
            
            
#                        if item.attrib['k']:
#                            if 'naptan:' in item.attrib['k']:
#                                print(ET.tostring(n))
#                                break

        
        
#                if n.attrib['k'] and 'naptan:' in n.attrib['k']:
#                    print(ET.tostring(n))
#                    break
         

        
        
        

#print(naptan_check(OSM_FILE))
#print(postcode_check(OSM_FILE))
            
            
            
            
            
            
            
