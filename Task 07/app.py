from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from datetime import datetime
from config import Config

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
CORS(app)  # Enable CORS for frontend integration 

class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
    def get_current_weather(self, city, units="metric"):
        """Get current weather for a city"""
        url = f"{self.base_url}/weather"
        params = {
            'q': city,
            'appid': self.api_key,
            'units': units
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("API Key Invalid: Your OpenWeatherMap API key is not working. Possible reasons: (1) Key not yet activated - wait 1-2 hours after creating it, (2) Email not verified - check your inbox, (3) Invalid key - generate a new one at https://home.openweathermap.org/api_keys")
            elif e.response.status_code == 404:
                raise Exception(f"City '{city}' not found. Please check the spelling.")
            else:
                raise Exception(f"Weather API error: {str(e)}")
        except requests.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    def get_weather_by_coordinates(self, lat, lon, units="metric"):
        """Get weather by coordinates"""
        url = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': units
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("API Key Invalid: Your OpenWeatherMap API key is not working. Possible reasons: (1) Key not yet activated - wait 1-2 hours after creating it, (2) Email not verified - check your inbox, (3) Invalid key - generate a new one at https://home.openweathermap.org/api_keys")
            elif e.response.status_code == 400:
                raise Exception(f"Invalid coordinates: lat={lat}, lon={lon}")
            else:
                raise Exception(f"Weather API error: {str(e)}")
        except requests.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    def get_forecast(self, city, units="metric", days=5):
        """Get 5-day weather forecast"""
        url = f"{self.base_url}/forecast"
        params = {
            'q': city,
            'appid': self.api_key,
            'units': units
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("API Key Invalid: Your OpenWeatherMap API key is not working. Possible reasons: (1) Key not yet activated - wait 1-2 hours after creating it, (2) Email not verified - check your inbox, (3) Invalid key - generate a new one at https://home.openweathermap.org/api_keys")
            elif e.response.status_code == 404:
                raise Exception(f"City '{city}' not found for forecast.")
            else:
                raise Exception(f"Forecast API error: {str(e)}")
        except requests.RequestException as e:
            raise Exception(f"Network error: {str(e)}")

# Initialize weather service
weather_service = WeatherService(app.config['WEATHER_API_KEY'])

def format_weather_response(weather_data):
    """Format weather data for consistent API response"""
    return {
        'city': weather_data['name'],
        'country': weather_data['sys']['country'],
        'temperature': {
            'current': weather_data['main']['temp'],
            'feels_like': weather_data['main']['feels_like'],
            'min': weather_data['main']['temp_min'],
            'max': weather_data['main']['temp_max']
        },
        'humidity': weather_data['main']['humidity'],
        'pressure': weather_data['main']['pressure'],
        'visibility': weather_data.get('visibility', 'N/A'),
        'weather': {
            'main': weather_data['weather'][0]['main'],
            'description': weather_data['weather'][0]['description'],
            'icon': weather_data['weather'][0]['icon']
        },
        'wind': {
            'speed': weather_data['wind']['speed'],
            'direction': weather_data['wind'].get('deg', 'N/A')
        },
        'coordinates': {
            'lat': weather_data['coord']['lat'],
            'lon': weather_data['coord']['lon']
        },
        'sunrise': datetime.fromtimestamp(weather_data['sys']['sunrise']).strftime('%H:%M:%S'),
        'sunset': datetime.fromtimestamp(weather_data['sys']['sunset']).strftime('%H:%M:%S'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@app.route('/', methods=['GET'])
def home():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/api', methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        'message': 'Flask Weather App API',
        'version': '1.0.0',
        'endpoints': {
            'current_weather': '/api/weather/current?city=<city_name>&units=<metric|imperial|kelvin>',
            'weather_by_coords': '/api/weather/coordinates?lat=<latitude>&lon=<longitude>&units=<metric|imperial|kelvin>',
            'forecast': '/api/weather/forecast?city=<city_name>&units=<metric|imperial|kelvin>',
            'health': '/api/health'
        }
    })

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """Get current weather for a city"""
    city = request.args.get('city')
    units = request.args.get('units', 'metric')
    
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400
    
    if units not in ['metric', 'imperial', 'kelvin']:
        return jsonify({'error': 'Units must be metric, imperial, or kelvin'}), 400
    
    try:
        weather_data = weather_service.get_current_weather(city, units)
        formatted_data = format_weather_response(weather_data)
        formatted_data['units'] = units
        
        return jsonify({
            'success': True,
            'data': formatted_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather/coordinates', methods=['GET'])
def get_weather_by_coordinates():
    """Get weather by latitude and longitude"""
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    units = request.args.get('units', 'metric')
    
    if not lat or not lon:
        return jsonify({'error': 'Both lat and lon parameters are required'}), 400
    
    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return jsonify({'error': 'Invalid coordinates format'}), 400
    
    if units not in ['metric', 'imperial', 'kelvin']:
        return jsonify({'error': 'Units must be metric, imperial, or kelvin'}), 400
    
    try:
        weather_data = weather_service.get_weather_by_coordinates(lat, lon, units)
        formatted_data = format_weather_response(weather_data)
        formatted_data['units'] = units
        
        return jsonify({
            'success': True,
            'data': formatted_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather/forecast', methods=['GET'])
def get_forecast():
    """Get 5-day weather forecast"""
    city = request.args.get('city')
    units = request.args.get('units', 'metric')
    
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400
    
    if units not in ['metric', 'imperial', 'kelvin']:
        return jsonify({'error': 'Units must be metric, imperial, or kelvin'}), 400
    
    try:
        forecast_data = weather_service.get_forecast(city, units)
        
        # Format forecast data
        formatted_forecast = {
            'city': forecast_data['city']['name'],
            'country': forecast_data['city']['country'],
            'coordinates': {
                'lat': forecast_data['city']['coord']['lat'],
                'lon': forecast_data['city']['coord']['lon']
            },
            'units': units,
            'forecast': []
        }
        
        for item in forecast_data['list']:
            forecast_item = {
                'datetime': datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d %H:%M:%S'),
                'date': datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d'),
                'time': datetime.fromtimestamp(item['dt']).strftime('%H:%M:%S'),
                'temperature': {
                    'temp': item['main']['temp'],
                    'feels_like': item['main']['feels_like'],
                    'min': item['main']['temp_min'],
                    'max': item['main']['temp_max']
                },
                'weather': {
                    'main': item['weather'][0]['main'],
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon']
                },
                'humidity': item['main']['humidity'],
                'pressure': item['main']['pressure'],
                'wind': {
                    'speed': item['wind']['speed'],
                    'direction': item['wind'].get('deg', 'N/A')
                },
                'clouds': item['clouds']['all']
            }
            formatted_forecast['forecast'].append(forecast_item)
        
        return jsonify({
            'success': True,
            'data': formatted_forecast
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Ensure API key is configured
    if not app.config.get('WEATHER_API_KEY'):
        print("Warning: WEATHER_API_KEY not configured. Please set your OpenWeatherMap API key.")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )