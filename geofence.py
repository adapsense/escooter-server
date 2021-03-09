
import csv

from shapely.geometry import MultiPoint, Point

import config
import threading

import pymongo
from bson import ObjectId

dbclient = pymongo.MongoClient(config.backend_dbclient)
dbdatabase = dbclient["escooter"]
dbGeoSetcollection = dbdatabase["geofences"]
dbGeoStatuscollection = dbdatabase['geofenceStatuses']

class geofence():
	def __init__(self):
		self._lock = threading.Lock()
		self.coords = []
		self.coordsPoint = []
		self.coordsArray = []
		self.borders = []
		setCounter = 0

		query = {"name" : "Active"}
		geoStatus = dbGeoStatuscollection.find_one(query)
		geoActiveId = geoStatus["_id"]
		query = {"geofenceStatus": ObjectId(config.backend_query)}
		geoSetActiveList = dbGeoSetcollection.find(query,{"polygon":1})
		for geoSet in geoSetActiveList:
			geoPointList = geoSet["polygon"]["coordinates"][0]
			for geoPoint in geoPointList:
				self.coordsPoint.append([geoPoint[1],geoPoint[0]])
				self.coords.append((float(geoPoint[0]), float(geoPoint[1])))
			self.borders.append(MultiPoint(self.coords).convex_hull)
			self.coordsArray.append(self.coordsPoint)
			setCounter = setCounter + 1
			self.coords = []
			self.coordsPoint = []


	def check(self, location):
		with self._lock:
			point = Point(location)
			for borderItem in self.borders:
				#print("Checking borders: ",borderItem)
				isInside = point.within(borderItem)
				if isInside:
					print("Point: ",point,"is within border",borderItem)
					return isInside
				print("Point: ",point," is not within border: ",borderItem)
			return False

	def updateGeofence(self):
		with self._lock:
			self.coords = []
			self.coordsPoint = []
			self.coordsArray = []
			self.borders = []
			setCounter = 0
			print("++Updating Geofence++")

			query = {"geofenceStatus": ObjectId(config.backend_query)}
			geoSetActiveList = dbGeoSetcollection.find(query,{"polygon":1})
			for geoSet in geoSetActiveList:
				geoPointList = geoSet["polygon"]["coordinates"][0]
				for geoPoint in geoPointList:
					self.coordsPoint.append([geoPoint[0],geoPoint[1]])
					self.coords.append((float(geoPoint[1]), float(geoPoint[0])))
				self.borders.append(MultiPoint(self.coords).convex_hull)
				self.coordsArray.append(self.coordsPoint)
				setCounter = setCounter + 1
				self.coords = []
				self.coordsPoint = []
