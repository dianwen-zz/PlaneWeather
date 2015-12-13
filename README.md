# PlaneWeather

Implements this API: https://bitbucket.org/snippets/plotwatt/q7oR

The SITA Aero API is used to look up airports by IATA code: https://www.developer.aero/Airport-API/API-Overview
forecast.io is used to look up weather forcast info: http://forecast.io/

The endpoint is hosted at https://fierce-crag-5651.herokuapp.com

Example requests:
- https://fierce-crag-5651.herokuapp.com/forecast/lhr/rdu/2015-03-01T00:00:00/500/2
- https://fierce-crag-5651.herokuapp.com/resolve/lax
- https://fierce-crag-5651.herokuapp.com/resolve/5,5

Note:
- The flight departure time should be provided in UTC. This is how the reference backend is implemented.
- This doesn't plug into http://flight-forecaster.herokuapp.com/. But with no visibility into how the frontend renders the info, debugging is difficult.
- Less weather information is available than expected from forecast.io (such as in the middle of the sea), but it may also be due to the intolerance of non-exact request parameters. However, we are able to get the time offset from UTC for all coordinates.
