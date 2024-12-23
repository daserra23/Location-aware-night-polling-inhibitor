import Domoticz
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun

class BasePlugin:
    def onStart(self):
        try:
            # Get location from Domoticz settings
            lat = Settings["Location"]["Latitude"]
            lon = Settings["Location"]["Longitude"]
            if lat == "" or lon == "":
                Domoticz.Error("Location not set in Domoticz. Please configure location in Setup->Settings->System")
                return
            
            self.latitude = float(lat)
            self.longitude = float(lon)
            
            # Store location object for reuse
            self.location = LocationInfo(latitude=self.latitude, longitude=self.longitude)
            
            # Initialize last calculation time as None
            self.last_sun_calc = None
            self.sunrise = None
            self.sunset = None
            
            Domoticz.Debug(f"Plugin initialized with location: {self.latitude}, {self.longitude}")
        except Exception as e:
            Domoticz.Error(f"Error initializing plugin: {str(e)}")
    
    def should_poll(self):
        """
        Determines if the inverter should be polled based on daylight hours
        Returns: bool indicating whether polling should occur
        """
        try:
            current_time = datetime.now()
            
            # Calculate sun times once per day or if not yet calculated
            if (self.last_sun_calc is None or 
                self.last_sun_calc.date() != current_time.date()):
                
                s = sun(self.location.observer, date=current_time)
                
                # Add buffer times (30 minutes)
                self.sunrise = s['sunrise'] - timedelta(minutes=30)
                self.sunset = s['sunset'] + timedelta(minutes=30)
                self.last_sun_calc = current_time
                
                Domoticz.Debug(f"Updated sun times - Sunrise: {self.sunrise.time()}, Sunset: {self.sunset.time()}")
            
            # Check if current time is within daylight hours (including buffer)
            should_poll = self.sunrise <= current_time <= self.sunset
            
            if not should_poll:
                Domoticz.Debug("Skipping poll - outside daylight hours (+/- 30min buffer)")
            
            return should_poll
            
        except Exception as e:
            Domoticz.Error(f"Error checking daylight hours: {str(e)}")
            # If there's an error, return True to ensure we don't miss readings
            return True
    
    def onHeartbeat(self):
        """
        Called every heartbeat. Implement the polling logic here.
        """
        if not self.should_poll():
            return
            
        # Your existing polling logic goes here
        # For example:
        # self.poll_inverter()