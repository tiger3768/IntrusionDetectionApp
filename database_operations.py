import pymongo
import time
from gridfs import GridFS
from bson import ObjectId

class MongoDBOperations:
    def __init__(self):
        dbfile = open("dbconnectstring.txt", "r")
        cstring = dbfile.read()
        self.client = pymongo.MongoClient(cstring)
        self.db = self.client.user_database
        self.fs = GridFS(self.db)

    def get_users_collection(self):
        return self.db.users

    def get_alerts_collection(self):
        return self.db.alerts
    
    def get_gridfs(self):
        return self.fs

    def save_alert_data(self, username, phone_number, stream_option, stream_link, screenshot_path=None):
        
        alert_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        date = time.strftime("%Y-%m-%d")
        alert_data = {
            "timestamp": alert_timestamp,
            "screenshot": screenshot_path if screenshot_path else ""
        }

        user_data = self.get_alerts_collection().find_one({"username": username})
        if user_data:
            date_data = user_data.get(date, [])
            date_exists = False
            for entry in date_data:
                if entry["stream_link"] == stream_link:
                    entry["alerts"].append(alert_data)
                    date_exists = True
                    break
            if not date_exists:
                date_data.append({"phone": phone_number, "stream_option": stream_option,
                                "stream_link": stream_link, "alerts": [alert_data]})
            user_data[date] = date_data
            self.get_alerts_collection().update_one({"username": username}, {"$set": {date: date_data}})
        else:
            self.get_alerts_collection().insert_one({"username": username, date: [{"phone": phone_number, "stream_option": stream_option,
                                                                        "stream_link": stream_link, "alerts": [alert_data]}]})
        print("Alert data saved to cloud.")
        
    def get_image_data(self, image_id):
        try:
            image_data = self.fs.get(ObjectId(image_id)).read()
            return image_data
        except Exception as e:
            print(f"Error fetching image data: {e}")
            return None

        
    def fetch_streams_data(self, username):
        user_data = self.get_alerts_collection().find_one({"username": username})
        streams_data = {}
        if user_data:
            new_streams_data = {}
            for date, date_data in user_data.items():
                if date != "_id" and date != "username":
                    new_streams_data[date] = []
                    for entry in date_data:
                        stream_entry = {
                            "phone": entry["phone"],
                            "stream_option": entry["stream_option"],
                            "stream_link": entry["stream_link"]
                        }
                        alerts = []
                        for alert in entry["alerts"]:
                            alerts.append({
                                "timestamp": alert["timestamp"],
                                "screenshot": alert["screenshot"]
                            })
                        stream_entry["alerts"] = alerts
                        new_streams_data[date].append(stream_entry)
            streams_data[username] = new_streams_data
        else:
            streams_data[username] = {}

        return streams_data
