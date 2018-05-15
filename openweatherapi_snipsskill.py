# encoding: utf-8
from __future__ import unicode_literals

import datetime
import json

import paho.mqtt.client as mqtt
import requests

fromtimestamp = datetime.datetime.fromtimestamp

# MQTT client to connect to the bus
mqtt_client = mqtt.Client()
HOST = "localhost"
PORT = 1883
WEATHER_TOPICS = ['hermes/intent/temperatureintent',
                  'hermes/intent/weatherintent',
                  'hermes/intent/cloudsintent',
                  'hermes/intent/windintent',
                  'hermes/intent/humidityintent']

# WEATHER API
WEATHER_API_BASE_URL = "http://api.openweathermap.org/data/2.5"
WEATHER_API_KEY = "668c3c522414b12cbfe11e5e3f02de12"
DEFAULT_CITY_NAME = "Ratingen"
UNITS = "metric" 
LANGUAGE = "de"



# Subscribe to the important messages
def on_connect(client, userdata, flags, rc):
    for topic in WEATHER_TOPICS:
        mqtt_client.subscribe(topic)


# Process a message as it arrives
def on_message(client, userdata, msg):
    print msg.topic

    if msg.topic not in WEATHER_TOPICS:
        return

    slots = parse_slots(msg)
    weather_forecast = get_weather_forecast(slots)


    if msg.topic == 'hermes/intent/temperatureintent':
        '''
        temperature-focused answer: 
            - location
            - temperature
        ''' 
        response = ("In {1} sind es momentan {2}Grad Celcius ").format(
            weather_forecast["location"], 
            weather_forecast["temperature"], 
        )
    
    elif msg.topic == 'hermes/intent/weatherintent':
        '''
        descriptive answer:
            - location
            - description
        ''' 
        response = "In {1} beträgt die Luftfeuchtigkeit {2} Prozent".format(
            weather_forecast["location"], 
            weather_forecast["description"]
        )
    elif msg.topic == 'hermes/intent/humidityintent':
        '''
        humidity-focused answer:
            - location
            - humidity
        ''' 
        response = "In {1} ist es momentan {2} ".format(
            weather_forecast["location"], 
            weather_forecast["humidity"]
        )
    elif msg.topic == 'hermes/intent/windintent':
        '''
        windspeed-focused answer: 
            - location
            - windspeed
        ''' 
        response = ("In {1} beträgt die Windgeschwindigkeit {2} Meter pro Sekunde").format(
            weather_forecast["location"],
            weather_forecast["windspeed"], 
        ) 
    elif msg.topic == 'hermes/intent/cloudintent':
        '''
        cloudiness-focused answer: 
            - location
            - cloudiness
        ''' 
        response = ("In {1} ist es momentan {2} Prozent bewölkt").format(
            weather_forecast["location"],
            weather_forecast["cloudiness"], 
        )
    session_id = parse_session_id(msg)
    say(session_id, response)


def parse_slots(msg):
    '''
    We extract the slots as a dict
    '''
    data = json.loads(msg.payload)
    return {slot['slotName']: slot['rawValue'] for slot in data['slots']}


def parse_session_id(msg): 
    '''
    Extract the session id from the message
    '''
    data = json.loads(msg.payload)
    return data['sessionId']
  
  
def say(session_id, text):
    '''
    Print the output to the console and to the TTS engine
    '''
    print(text)
    mqtt_client.publish('hermes/dialogueManager/endSession', json.dumps({'text': text, "sessionId" : session_id}))


def parse_open_weather_map_forecast_response(response, location):
    '''
    Parse the output of Open Weather Map's forecast endpoint
    '''
    
    description=response.weather[0]["description"]
    temperature=response.main["temp"] 
    humidity=response.main["humidity"]
    windspeed=response.wind["speed"]
    cloudiness=response.clouds["all"]
    
    return {
        "location": location,      
        "description": int(description),
        "temperature": int(temperature),
        "humidity": int(humidity),
        "windspeed": int(windspeed),
        "cloudiness": int(cloudiness)
        
    }


def get_weather_forecast(slots):
    '''
    Parse the query slots, and fetch the weather forecast from Open Weather Map's API
    '''
    location = slots.get("forecast_locality", None) \
            or slots.get("forecast_country", None)  \
            or slots.get("forecast_region", None)  \
            or slots.get("forecast_geographical_poi", None) \
            or slots.get("cityname", None)  \
            or DEFAULT_CITY_NAME
    forecast_url = "{0}/weather?q={1}&APPID={2}&units={3}&lang={4}".format(
        WEATHER_API_BASE_URL, location, WEATHER_API_KEY, UNITS, LANGUAGE)
    r_forecast = requests.get(forecast_url)
    return parse_open_weather_map_forecast_response(r_forecast.json(), location)

if __name__ == '__main__':
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(HOST, PORT)
    mqtt_client.loop_forever()
