from flask import Flask,request,jsonify,render_template
import requests
app=Flask(__name__)
WEATHER_API_KEY="307518bddc8418002ed239f699021f44"
WEATHER_API_URL="http://api.openweathermap.org/data/2.5/weather"
@app.route('/')
def home_page():
    return render_template('design lab8.html')
@app.route('/weather',methods=['GET'])
def fetch_weather():
    city_name=request.args.get('city')
    if not city_name:
        return jsonify({"error":"City name is required"}),400
    query_parameters={"q":city_name,"appid":WEATHER_API_KEY,"units":"metric"}
    weather_response=requests.get(WEATHER_API_URL,params=query_parameters)
    if weather_response.status_code!=200:
        return jsonify({"error":"Unable to retrieve weather details"}),weather_response.status_code
    weather_data=weather_response.json()
    formatted_weather_info={"city":weather_data["name"],"temperature":weather_data["main"]["temp"],"weather_condition":weather_data["weather"][0]["description"],"humidity_level":weather_data["main"]["humidity"]}
    return jsonify(formatted_weather_info)

if __name__=='__main__':
    app.run(debug=True)
