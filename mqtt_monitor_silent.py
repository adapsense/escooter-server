"""
Connect to MQTT Server And Monitor 001 to x for activity
"""

import config
geofence_lock = config.geofence

DEBUGGING = False

MAX_BIKE_NUMBER = 100

#Setup Logging Function
import logging
logger = logging.getLogger('MQTT_Monitor')

import pymongo
from bson import ObjectId

#Prepare Threading
import threading, math, numpy


#Functions Needed for this File
import paho.mqtt.client as paho
import time,os	#Sleep and other os config
import datetime	#Time Stamp

from json import dumps as jdumps
from json import loads as jloads


from geofence import geofence

broker_ip=config.mqtt_ip
broker_port=config.mqtt_port
broker_path=config.mqtt_path
broker_username=config.mqtt_username
broker_password=config.mqtt_password

MAX_DOWNTIME = 60

BIKECODE = "UPD-000"

mqtt_topics = ["lock/", "unlock/","location/"]

CONNECTED = "CONNECTED"
DISCONNECTED = "DISCONNECTED"
PENDING = "PENDING"

#List of Ignore List
#Content will still be Received, but will not be printed out
IGNORE_ARRAY = ["ACK","lat"]

dbclient = pymongo.MongoClient(config.backend_dbclient)
dbdatabase = dbclient["escooter"]
dblogcollection = dbdatabase["vehicleLogs"]
dbvehiclecollection = dbdatabase['vehicles']

SubbedOnce = False

#CallBack Functions
#Should be Fast and MUST not block thread >5 seconds
def on_connect(client, userdata, flags, rc):
	global SubbedOnce
	error_list = []
	#If Connection is Successful
	if rc==0:
		print('MQTT Client Connected')
		#Log Connection
		logger.info("\rMQTT Broker Status: \tConnected")
		#Set status
		userdata.status = CONNECTED
		#If This is the FIRST Connaction
		#Subscribe to what is needed
		if ((SubbedOnce == False) ):
			#Get Subscription List from Generator
			subList = userdata.subList() + ['presence']
			print("Topics to subscibe:\t",end = '')
			for subTopic in subList:
				try:
					print(subTopic, end = ", ")
					client.subscribe(subTopic)
				except Exception as e:
					logger.error("Subscribing Error: Cannot Connect to \"",subTopic,"\"")
					error_list.append(subTopic)
			print('')
			#Subcribe Done
			if len(error_list) > 0:
				logger.error("Subscribing Error: Cannot Connect to %s"%(subTopic))
			else:
				SubbedOnce = True
				logger.info("\nSubscription Completed\n")
	else:
		logging.error("Bad connection \t\tReturned code=%d"%(rc))

def on_disconnect(client, userdata, rc):
	print(('\n'+ "DISCONNECTED\t"*5 + '\n') * 5)
	if rc == 0:
		logging.info("MQTT Disconnected Properly")
	else:
		logging.error("MQTT Disconnected Unexpectedly")

def on_message(client, userdata, message):
    #Decode Message Content
	content = message.payload.decode("utf-8")
	dictmsg = jloads(str(message.payload.decode("utf-8")))
	if type(dictmsg) is dict:
		#Function to call
		if ("location" in message.topic):
			y = threading.Thread(target=userdata.monitor.update,args=(message,))
			y.start()
	elif type(dictmsg) is list:
		for sample in dictmsg:
			message.payload = jdumps(sample).encode("utf-8")
			if ("location" in message.topic):
				y = threading.Thread(target=userdata.monitor.update,args=(message,))
				y.start()

class monitor():
	def __init__(self, mqttc = None):
		self.mqtt_dict = {}
		self.bike_dict = {}
		self.geofence = geofence()
		self.max_downtime = 15 * 60
		self.mqttc = mqttc
		self.bike_active = False
		self.bike_ts = datetime.datetime.now()
		self.bike_delay = 60
		self.bike_count = 0

	def update(self,message):
		#Updates mqtt records
		self.geofence.updateGeofence()
		bike = False
		try:
			try:
				#Parse data into a dictionary
				dictmsg = jloads(str(message.payload.decode("utf-8")))
				#Update an mqtt_topic
				self.mqtt_dict[str(message.topic)] = True, dictmsg, datetime.datetime.now()
				bike = True
			except Exception as e:
				#If payload is not a json data
				print("Error while processing update.", e, '\n\n')
				self.mqtt_dict[str(message.topic)] = False, message.payload.decode("utf-8"), datetime.datetime.now()
		except Exception as e:
			print(e)
		self.display(bike = True)

	def display(self, bike = False):
		self.printupdates()
		self.sortLogs()
		self.printBikes()

	def printupdates(self):
		print('MQTT LIST')
		dtn = datetime.datetime.now()
		for key, value in self.mqtt_dict.items():
			dict_item, msg, ts = value
			t =  dtn - ts

			if dict_item:
				msg = jdumps(msg)

			try:
				if len(msg) > 140:
					print("{:30s} : {:<140s} \n(s){:184f}".format(key, msg, t.total_seconds()))
				else:
					print("{:30s} : {:<140s} (s){:10f}".format(key, msg, t.total_seconds()))

			except:

				print("{:30s} : {:<140s} (s){:10f}".format(key, msg, t.total_seconds()))

	def sortLogs(self):
		print('\n'*3, '\nSorting Filter')
		itemlist = ['name', 'lat', 'long', 'lock_status', 'message','Temperature','IAQ','Humidity','Pressure','Altitude']
		dtn = datetime.datetime.now()
		print('JLOAD')
		for key, value in self.mqtt_dict.items():
			#separate package
			dict_item, msg, ts = value
			ts1 = ts

			dbdocument = dict(msg)
			query = {"topic" : dbdocument['name']}
			print (query)
			vehiclerecord = dbvehiclecollection.find_one(query)
			print (vehiclerecord)
			bike_code_id = vehiclerecord["_id"]
			print (bike_code_id)
			dbdocument['lockStatus'] = dbdocument.pop('lock_status')
			dbdocument['closing'] = dbdocument.pop('Closing')
			dbdocument['temperature'] = dbdocument.pop('Temperature')
			dbdocument['iaq'] = dbdocument.pop('IAQ')
			dbdocument['humidity'] = dbdocument.pop('Humidity')
			dbdocument['pressure'] = dbdocument.pop('Pressure')
			dbdocument['altitude'] = dbdocument.pop('Altitude')
			del dbdocument['timestamp']
			del dbdocument['name']
			dbdocument["vehicle"] = ObjectId(bike_code_id)

			print('dict',dict_item)
			print(1, msg)
			if dict_item:
				n1 = None
				#Get bike name
				try:
					n1 = msg['name']
				except:
					print('No NAME INfo')
					n1 = 'NO NAME'

				newmsg = False
				#Check if bike is already registered

				print('check',n1)
				if n1 in self.bike_dict and n1 is not None:
					print(2)
					tdict, ts_old = self.bike_dict[n1]
					print(3)

					try:
						#Check if update or just a record
						print(4)
						if ts_old < ts: # greater total time elapsed
							print(5)
							newmsg = True
							x = dblogcollection.insert_one(dbdocument)
							print(6)
						else:
							print('old')
					except Exception as e:
						print(e)

					print(8)


				else:	#If no records yet
					print(10)
					tdict = {}

					x = dblogcollection.insert_one(dbdocument)

				print('done w check')

				try:

					if self.bike_active and (dtn-self.bike_ts).total_seconds() > self.bike_delay:
						print('DISABLE', (dtn-self.bike_ts).total_seconds())
						self.mqttc.mqttc.publish('lock/UPD-000','<DISABLE>')
						self.mqttc.mqttc.publish('unlock/UPD-000','<DISABLE>')
						self.mqttc.mqttc.publish('location/UPD-000','<DISABLE>')
						self.bike_count += 1
						if self.bike_count > 3:
							self.bike_active = False

				except Exception as e:
					print('Error Disable ', e)

				for x in itemlist:
					try:



						if msg[x] is None:
							pass
						else:
							if newmsg and x == 'message':
								newmsg = False
								try:
									if msg['name'] == 'UPD-000' and (msg[x] == 'LOCK ACK' or msg[x] == 'UNLOCK ACK'):
										if (dtn-ts1).total_seconds() < self.bike_delay:
											if ts1 > self.bike_ts:
												print('Updated')
												self.bike_active = True
												self.bike_ts = ts1
											print((dtn-self.bike_ts).total_seconds())

								except Exception as e:
									print(e)

							else:
								tdict[x] = msg[x]
					except:
						#print(x)
						#tdict[x] = None
						pass
				#print(tdict)
				self.bike_dict[n1] = tdict, ts#datetime.datetime.now()

				del n1
			else:	#Not a dictionary item
				#print('N/A')
				#print(key, dict_item, msg, ts)
				pass

	def printBikes(self):
		if len(self.bike_dict) > 0:
			print('\n'*5,'\nBike LIST')

			dtn = datetime.datetime.now()
			for key, value in self.bike_dict.items():
				tdict, ts = value
				t =  dtn - ts


				try:
					temp_str = '{lat}, {long}'.format(**tdict)
					temp_str = '{:30s}'.format(temp_str)

				except:
					temp_str = ''
					print('NO location found')


				for k, v in tdict.items():
					temp_str = temp_str + '{0} : {1}  '.format(k,v)

				if t.total_seconds() > (self.max_downtime) :
					tdict['message'] = 'DEAD'
					tdict['lock_status'] = 'Error: Timeout'
					status = 'ERROR'
					print("{:9s} : {:^10s}   {:50s} {:20s}".format(key, status, temp_str, '*' * 60))

				else:
					status = 'OK'
					print("{:9s} : {:^10s}   {:50s} ".format(key, status, temp_str))

				try:
					if np.nan(tdict['lat']):
						tdict['lat'] = 0.0

					if np.nan(tdict['long']):
						tdict['long']  = 0.0
				except:
					pass



				if geofence_lock:
					try:
						if 'locking' not in tdict:
							tdict['locking'] = 0
							tdict['last_lock'] = datetime.datetime.now()

						#Check Position
						lat, long = float(tdict['lat']), float(tdict['long'])
						inside_fence = self.geofence.check((lat,long))


						if tdict['lock_status'] != 'L':
							if inside_fence:	#Do NOthing
								pass
							else:
								print(tdict['name'],tdict['lock_status'],tdict['locking'])
								print(tdict['name'],tdict['lock_status'],tdict['locking'])
								print(tdict['name'],tdict['lock_status'],tdict['locking'])
								print(tdict['name'],tdict['lock_status'],tdict['locking'])
								print(tdict['name'],tdict['lock_status'],tdict['locking'])
								try:
									if tdict['locking'] < 3:
										tdict['last_lock'] = datetime.datetime.now()

										tdict['locking'] += 1
										self.mqttc.mqttc.publish('lock/'+tdict['name'],'<LOCK>')
										print('geofence\n'*5, inside_fence, tdict['name'], tdict['lock_status'],'<LOCK>','\ngeofence'*5)
									else:
										if (datetime.datetime.now() - tdict['last_lock'] ).total_seconds() >= 12:
											tdict['locking'] = 0


								except Exception as e:
									print(e)
									tdict['locking'] += 1
									self.mqttc.mqttc.publish('lock/'+tdict['name'],'<LOCK>')
									print('geofence\n'*25, inside_fence, tdict['name'], tdict['lock_status'],'<LOCK>','\ngeofence'*25)

						else:
							tdict['locking'] = 0

					except Exception as e:
						print("Exception\n"*5,e,"\nException"*5)
						pass




####################################################################################################



class mqtt_feed(threading.Thread):
	def __init__(self,code = BIKECODE, SL = None,gpsc = None, restartFunc = None, sensors = None):# first call
		def MQTT_inits():

			self.reportTimeStamp = None


			# Start MQTT Client
			self.mqttc = paho.Client(client_id='MQTT_MONITOR',clean_session = False, userdata = self, protocol=paho.MQTTv311,transport="websockets")
			self.status = PENDING


			#SubbedOnce = False

			#define MQTT Callbacks
			self.mqttc.on_connect=on_connect
			self.mqttc.on_message=on_message

			#SET RECONNECT PARAMETERS
			self.mqttc.reconnect_delay_set(min_delay=1, max_delay=MAX_DOWNTIME)

			#set WILL message incase of Unexpected Disconnection after MAX_DOWNTIME
			self.mqttc.will_set("presence", payload = "{!!!!!IMPROPER!!!!!}")

			#Define MQTT sub topics
			#Topic with Most ACtion
			self.createSubList()
			self.midList = []

			self.monitor = monitor(mqttc = self)
			self.geofence = geofence()

		def thread_init():
			threading.Thread.__init__(self,daemon = False)
			self.name = "Thread: MQTT Report"
			self.ALIVE = False
			self.interval = 15

		def reload_lock():
			pass



		MQTT_inits()

		thread_init()


		self.connect()
		#Start Thread That Receives Messages
		self.mqttc.loop_start()

		reload_lock()


####################################################################################################

	def __enter__(self):# called using with statement
		return self

	def connect(self):
		if True:
			print("Connecting to:\t\t%s:%d"%( broker_ip ,broker_port))
			try:
				self.mqttc.ws_set_options(path=broker_path)
				self.mqttc.tls_set()
				self.mqttc.username_pw_set(broker_username,password=broker_password)
				self.mqttc.connect(broker_ip,port = broker_port)#connect
				return 0


			except Exception as e:
				print("Error @:mqtt connect")
				print(e)
		else:
			logger.error("No Internet connection detected")
			if self.smartlock != None:
				logger.info("Lock Override Initiated")
				self.smartlock.lock(override = True)
			raise Exception("Internet Connection ERROR")




	#creates a Subscription List to Subscribe to
	def subList(self):
		return self.topics


	def createSubList(self,topics = mqtt_topics):

		#Reset Topics List
		self.topics = []


		logger.debug("BIKE ID= %s" % ('UPD-000'))
		logger.debug("Subscribing to:")

		#Make combine topics with Bikename
		for i,tpic in enumerate(topics):
			for x in range(MAX_BIKE_NUMBER+1):
				s = '{:03d}'.format(x)
				self.topics += [tpic + 'UPD-' + s]
		for item in self.topics:
			print(item)
		time.sleep(1)

####################################################################################################

	def run(self):
		self.ALIVE = True
		while self.status != CONNECTED:
			pass



		while self.ALIVE:
			if self.status == "CONNECTED":
				self.monitor.printupdates()
				#Report to Server Every Interval
				#Essential to make sure connection is active
				self.report()
				#self.mqttc.loop()
				#Check if report Reached Server
				#print("MID List Size:%d" % len(self.midList), end = '')

			time.sleep(self.interval)

	def pause(self,pause = True):
		if pause:
			print("Pausing")
			self.mqttc.loop_stop()
		elif not pause:
			print("Unpausing")
			self.mqttc.loop_start()

####################################################################################################


	def __exit__(self, *a):
		self.stop()

	def stop(self):
		self.ALIVE = False
		self.disconnect()
		self.mqttc.loop_stop() #stop loop
		logger.info("Closing MQTT for %s" % ('UPD-000'))

	def disconnect(self):
		self.mqttc.disconnect() #disconnect

####################################################################################################

	def report(self):
		#Check if Initial Report
		if self.reportTimeStamp == None:
			self.reportTimeStamp = datetime.datetime.now()

		#If not Initial Report
		else:
			#Check Last Report Timeout Reached
			if (datetime.datetime.now() - self.reportTimeStamp).seconds > 30*60:
				logger.error("Error Connecttion Should be Restarting")



		time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		#Check if Connected to MQTT Server
		if self.status == CONNECTED:
			#Publish Data
			result, mid = self.mqttc.publish('presence', 'MQTT Monitor' )

			#Log Report Time Sent
			self.reportTimeStamp = datetime.datetime.now()

			self.midList.append(mid)
			return True

		else:
			logger.debug("Calling to Report\n\nBUT\n\nNot Connected to MQTT Server\n\n")
			return False

####################################################################################################




if __name__ == '__main__':
	mm = mqtt_feed()
	mm.start()

	target = "location/UPD-000"
	while True:
		try:
			command = input("Enter Command with <>:\n target with () at both ends")

			if "{" in command and '}' in command:
				print("in Decoder")
				target = command[command.index('('): command.index(')')]
				print(target)
				print('\n\n\nNEW Target:\t {:10s}'.format(target))

			elif "<" in command and ">" in command:
				mm.mqttc.publish(target,command)
			else:
				if command.upper() == 'Q':
					break
		except Exception as e:
			print(e)
			break

	mm.stop()


	mm.join()
