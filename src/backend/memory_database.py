"""
In-memory database for testing without MongoDB
"""

from argon2 import PasswordHasher

# In-memory storage
activities_data = {}
teachers_data = {}

class MemoryCollection:
    def __init__(self, data_store):
        self.data_store = data_store
    
    def count_documents(self, filter_dict):
        return len(self.data_store)
    
    def insert_one(self, document):
        key = document.get('_id')
        if key:
            self.data_store[key] = {k: v for k, v in document.items() if k != '_id'}
        return type('Result', (), {'inserted_id': key})()
    
    def find_one(self, filter_dict):
        if '_id' in filter_dict:
            key = filter_dict['_id']
            if key in self.data_store:
                result = {'_id': key}
                result.update(self.data_store[key])
                return result
        return None
    
    def find(self, filter_dict):
        results = []
        for key, value in self.data_store.items():
            # Simple filtering logic for activities
            if self._matches_filter(key, value, filter_dict):
                result = {'_id': key}
                result.update(value)
                results.append(result)
        return results
    
    def _matches_filter(self, key, value, filter_dict):
        if not filter_dict:
            return True
        
        # Handle schedule_details.days filter
        if "schedule_details.days" in filter_dict:
            days_filter = filter_dict["schedule_details.days"]
            if "$in" in days_filter:
                target_days = days_filter["$in"]
                activity_days = value.get("schedule_details", {}).get("days", [])
                if not any(day in activity_days for day in target_days):
                    return False
        
        # Handle time filters
        if "schedule_details.start_time" in filter_dict:
            gte_filter = filter_dict["schedule_details.start_time"]
            if "$gte" in gte_filter:
                min_time = gte_filter["$gte"]
                activity_start = value.get("schedule_details", {}).get("start_time", "00:00")
                if activity_start < min_time:
                    return False
        
        if "schedule_details.end_time" in filter_dict:
            lte_filter = filter_dict["schedule_details.end_time"]
            if "$lte" in lte_filter:
                max_time = lte_filter["$lte"]
                activity_end = value.get("schedule_details", {}).get("end_time", "23:59")
                if activity_end > max_time:
                    return False
        
        return True
    
    def aggregate(self, pipeline):
        # Simple aggregation for getting unique days
        if len(pipeline) >= 2 and pipeline[0].get("$unwind") == "$schedule_details.days":
            unique_days = set()
            for key, value in self.data_store.items():
                days = value.get("schedule_details", {}).get("days", [])
                unique_days.update(days)
            
            return [{"_id": day} for day in sorted(unique_days)]
        return []
    
    def update_one(self, filter_dict, update_dict):
        if '_id' in filter_dict:
            key = filter_dict['_id']
            if key in self.data_store:
                if '$push' in update_dict:
                    for field, value in update_dict['$push'].items():
                        if field not in self.data_store[key]:
                            self.data_store[key][field] = []
                        self.data_store[key][field].append(value)
                        return type('Result', (), {'modified_count': 1})()
                elif '$pull' in update_dict:
                    for field, value in update_dict['$pull'].items():
                        if field in self.data_store[key] and value in self.data_store[key][field]:
                            self.data_store[key][field].remove(value)
                            return type('Result', (), {'modified_count': 1})()
        return type('Result', (), {'modified_count': 0})()

# Create collections
activities_collection = MemoryCollection(activities_data)
teachers_collection = MemoryCollection(teachers_data)

# Methods
def hash_password(password):
    """Hash password using Argon2"""
    ph = PasswordHasher()
    return ph.hash(password)

def init_database():
    """Initialize database if empty"""

    # Initialize activities if empty
    if activities_collection.count_documents({}) == 0:
        for name, details in initial_activities.items():
            activities_collection.insert_one({"_id": name, **details})
            
    # Initialize teacher accounts if empty
    if teachers_collection.count_documents({}) == 0:
        for teacher in initial_teachers:
            teachers_collection.insert_one({"_id": teacher["username"], **teacher})

# Initial database if empty
initial_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Mondays and Fridays, 3:15 PM - 4:45 PM",
        "schedule_details": {
            "days": ["Monday", "Friday"],
            "start_time": "15:15",
            "end_time": "16:45"
        },
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 7:00 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "07:00",
            "end_time": "08:00"
        },
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Morning Fitness": {
        "description": "Early morning physical training and exercises",
        "schedule": "Mondays, Wednesdays, Fridays, 6:30 AM - 7:45 AM",
        "schedule_details": {
            "days": ["Monday", "Wednesday", "Friday"],
            "start_time": "06:30",
            "end_time": "07:45"
        },
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and compete in basketball tournaments",
        "schedule": "Wednesdays and Fridays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Wednesday", "Friday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore various art techniques and create masterpieces",
        "schedule": "Thursdays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Thursday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Monday", "Wednesday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and prepare for math competitions",
        "schedule": "Tuesdays, 7:15 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "07:15",
            "end_time": "08:00"
        },
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Friday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "amelia@mergington.edu"]
    },
    "Weekend Robotics Workshop": {
        "description": "Build and program robots in our state-of-the-art workshop",
        "schedule": "Saturdays, 10:00 AM - 2:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "10:00",
            "end_time": "14:00"
        },
        "max_participants": 15,
        "participants": ["ethan@mergington.edu", "oliver@mergington.edu"]
    },
    "Science Olympiad": {
        "description": "Weekend science competition preparation for regional and state events",
        "schedule": "Saturdays, 1:00 PM - 4:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "13:00",
            "end_time": "16:00"
        },
        "max_participants": 18,
        "participants": ["isabella@mergington.edu", "lucas@mergington.edu"]
    },
    "Sunday Chess Tournament": {
        "description": "Weekly tournament for serious chess players with rankings",
        "schedule": "Sundays, 2:00 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Sunday"],
            "start_time": "14:00",
            "end_time": "17:00"
        },
        "max_participants": 16,
        "participants": ["william@mergington.edu", "jacob@mergington.edu"]
    },
    "Manga Maniacs": {
        "description": "Explore the fantastic stories of the most interesting characters from Japanese Manga (graphic novels).",
        "schedule": "Tuesdays, 7:00 PM - 8:00 PM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "19:00",
            "end_time": "20:00"
        },
        "max_participants": 15,
        "participants": []
    }
}

initial_teachers = [
    {
        "username": "mrodriguez",
        "display_name": "Ms. Rodriguez",
        "password": hash_password("art123"),
        "role": "teacher"
     },
    {
        "username": "mchen",
        "display_name": "Mr. Chen",
        "password": hash_password("chess456"),
        "role": "teacher"
    },
    {
        "username": "principal",
        "display_name": "Principal Martinez",
        "password": hash_password("admin789"),
        "role": "admin"
    }
]