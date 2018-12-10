'''
Created on Dec 8, 2018

@author: eric
'''

import requests
import datetime
import sys
import re

from pandas.io.json import json_normalize
from prettytable import PrettyTable

class MyClass(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.list_of_cities=None
        self.selected_cities={}
        self.gmaps_api_key="AIzaSyDfsQ2w4w23PjXME9L_IVCkfA5xOWRcZKg"
    
    def retrieve_cities(self, country, percentile):
        
        '''
        This function gets the cities from OpenDataSoft.
        Then it passes the json data to a pandas dataframe.
        After that, it filters the cities by population given a specified percentile.
        
        Regarding the row number in the URL (rows=10000), is it the maximum you can obtain using a GET query from the API.
        
        '''
        
        quantile_from_percentile=self.percentile_to_quantile(percentile)
        url='https://public.opendatasoft.com/api/records/1.0/search/?dataset=worldcitiespop&rows=10000&sort=population&facet=country&refine.country={}'.format(country.lower())
        world_city_data=self.get_data_from_url(url)
        
        world_city_data_normalized=json_normalize(world_city_data["records"])
          
        self.list_of_cities=world_city_data_normalized[world_city_data_normalized["fields.population"] >= world_city_data_normalized["fields.population"].quantile(quantile_from_percentile)]
    
        sys.stderr.write("Found {} cities\n".format(len(self.list_of_cities.index)))
        
    def percentile_to_quantile(self,percentile):
        '''
        This function passes the percentile as integer to a quantile as a float, so it can be used by pandas dataframe in retrieve_cities function
        '''
        quantile=float(1)-float(percentile/100)
        return quantile
    
    def calculate_travel(self):
        '''
        This function calculates the travel time from the selected cities to Victoria Station, London by using Google Maps Directions API.
        '''
        
        driving_url="https://maps.googleapis.com/maps/api/directions/json?origin={}&destination=Victoria+Station+London&key={}"
        transit_url="https://maps.googleapis.com/maps/api/directions/json?origin={}&destination=Victoria+Station+London&mode=transit&key={}"
        
        self.selected_cities={key: {"Population":int(value)} for (key,value) in zip(self.list_of_cities["fields.accentcity"].tolist(),self.list_of_cities["fields.population"].tolist())}
        
        for city,information in self.selected_cities.items():
            car_time,car_distance=self.get_traveltime(city, driving_url)
            pb_time,pb_distance=self.get_traveltime(city, transit_url)
            if car_time is not None and pb_time is not None:
                car_time_minutes=(car_time.hour*60)+car_time.minute
                pb_time_minutes=(pb_time.hour*60)+pb_time.minute
                ratio=round(pb_time_minutes/car_time_minutes,2)
            else:
                ratio=None
            information.update({"pb_time":pb_time,"pb_distance":pb_distance,"car_time":car_time,"car_distance":car_distance,"ratio":ratio})
            
        sys.stderr.write("Travel times and distances obtained\n")
    
        
    def get_traveltime(self,city,url):
        '''
        For each city, we format each url to get the travel time
        '''
        travel_data=self.get_data_from_url(url.format(city,self.gmaps_api_key))
        
        if travel_data["status"] == "OK":
            '''
            For all the cities showing an OK status we can retrieve the travel time and distance
            '''
            
            travel_data_normalized=json_normalize(travel_data["routes"][0]["legs"])
            travel_time, travel_distance = travel_data_normalized["duration.text"][0],travel_data_normalized["distance.text"][0]
            formated_travel_time = self.manage_time(travel_time)
            
            return formated_travel_time.time(), travel_distance
        else:
            '''
            In this case, for all the cities that show a NO_STATUS we return None.
            '''
            
            return None,None
    
    def show_top_cities(self):
        '''
        Here we create a table using the package PrettyTable so we can visualize the results in an attractive manner
        '''
        headers=['City']
        for value in self.selected_cities.values():
            headers.extend(value.keys())
            break
        
        table=PrettyTable(headers)
        for key,values in self.selected_cities.items():
            row=[key]
            for value in values.values():
                row.append(value)
            table.add_row(row)
        
        print(table)
        
    def manage_time(self,time_string):
        '''
        This function returns a proper datetime object to easily make calculations
        '''
        time=list(map(int, re.findall(r'\d+', time_string)))
        
        if len(time)> 1:
            hour_minute_time=':'.join(map(str,time))
            hour_minute_time_format=self.format_time(hour_minute_time)
            return hour_minute_time_format
        else:
            minute_time=':'.join(['00',str(time[0])])
            minute_time_format=self.format_time(minute_time)
            return minute_time_format
        
    def format_time(self,time_to_format):
        '''
        This function passes the time string to a datetime object
        '''
        format_time=datetime.datetime.strptime(time_to_format,'%H:%M')
        
        return format_time
        
    def get_data_from_url(self,url):
        '''
        Uses requests package to apply the GET method of RESTful APIs to retrieve data from API
        '''
        response=requests.get(url)
        data=response.json()
        return data
    
if __name__ == '__main__':
    
    m = MyClass()
    m.retrieve_cities(country='GB',percentile=5)
    m.calculate_travel()
    m.show_top_cities()
    