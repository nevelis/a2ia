import requests
import sys

def get_current_weather(zip_code, api_key):
    """Get current weather for a ZIP code using OpenWeatherMap API"""
    try:
        url = f'http://api.openweathermap.org/data/2.5/weather?zip={zip_code},US&appid={api_key}&units=imperial'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract relevant weather information
        temp_f = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        description = data['weather'][0]['description']
        
        # Format and return the result
        return (f"Current Weather in Moraga (ZIP 94556):
""
        f"Temperature: {temp_f}Â°F (Feels like: {feels_like}Â°F)
"
        f"Humidity: {humidity}%
"
        f"Wind Speed: {wind_speed} mph
"
        f"Conditions: {description.capitalize()}"
)
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"

if __name__ == "__main__":
    # Replace with your OpenWeatherMap API key (get one at https://openweathermap.org/api)
    API_KEY = "your_api_key_here"
    
    if len(sys.argv) > 1:
        zip_code = sys.argv[1]
    else:
        zip_code = "94556"
    
    weather_info = get_current_weather(zip_code, API_KEY)
    print(weather_info)