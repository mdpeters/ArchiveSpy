#!/usr/bin/env python
import requests, json, csv, getpass, argparse, sys, logging, os, urllib
from requests_toolbelt import exceptions
from requests_toolbelt.downloadutils import stream
			
class ASpace():
	def __init__(self, url="http://localhost:8089", verifySSL=False, repository="2"):
		self.url = url
		self.verifySSL = verifySSL
		self.auth = ''
		self.session = ''
		self.headers = ''
		self.repositoryUri = "/repositories/" + repository
		self.repositoryUrl = self.url + self.repositoryUri
		self.py3 = sys.version_info[0] > 2 #creates boolean value to test that Python major version > 2
	
	def init_session(self, username="admin", password="admin"):
		try:
			safe_password = urllib.quote(password)
			response = requests.post(self.url+'/users/'+username+'/login?password='+safe_password, verify=self.verifySSL)
			if response.status_code == 200:
				self.auth = response.json()
				self.session = self.auth["session"]
				self.headers = {'X-ArchivesSpace-Session':self.session}
				print "Connected to " + self.url
			elif response.status_code == 403:
				print "Invalid login"
				sys.exit()
			else:
				print "Something went horribly wrong"
		except SystemExit:
			raise	
		except:
			print "Unexpected error:", sys.exc_info()[0]			
			
	def getRepositories(self):
		return requests.get(self.url + '/repositories', headers=self.headers, verify=self.verifySSL)
	
	#Update to be more generic, pass repository number or name to set
	def setRepository(self):
		repositories = requests.get(self.url + '/repositories', headers=self.headers, verify=self.verifySSL).json()
		print '\nPlease choose a repository:\n'
		for repository in repositories:
			print repository['repo_code']
		if self.py3:
			repo = input("\nRepository: ")
		else:
			repo = raw_input("\nRepository: ")
		for repository in repositories:
			if repo == repository['repo_code']:
				self.repositoryUri = repository['uri']
		self.setRepositoryUrl()
		print '\nUsing: ' + self.repositoryUrl
		
	def setRepositoryUrl(self):
		self.repositoryUrl = self.url + self.repositoryUri
		
	def searchRepository(self, search):
		return requests.get(self.repositoryUrl + '/search?page=1&q=' + search, headers=self.headers, verify=self.verifySSL)
		
	def getAgentCorpByID(self, agentID):
		return requests.get(self.url + '/agents/corporate_entities/' + agentID, headers=self.headers, verify=self.verifySSL)
		
	def getAgentPersonByID(self, agentID):
		return requests.get(self.url + '/agents/people/' + agentID, headers=self.headers, verify=self.verifySSL)
		
	def getAllArchivalObjectIDs(self):
		return requests.post(self.repositoryUrl + '/archival_objects?all_ids=true', headers=self.headers, verify=self.verifySSL)
	
	def getArchivalObjectByRefID(self, refID):
		parameters = {"ref_id[]":refID}
		archival_object_lookup = requests.get(self.repositoryUrl + '/find_by_id/archival_objects', params=parameters, headers=self.headers, verify=self.verifySSL).json()
		archival_object_uri = archival_object_lookup['archival_objects'][0]['ref']
		return requests.get(self.url+archival_object_uri, headers=self.headers, verify=self.verifySSL)
		
	def updateArchivalObject(self, archivalObjectUri, jsonData):
		return requests.post(self.url + archivalObjectUri,headers=self.headers, data=jsonData, verify=self.verifySSL)
		
	def updateResourceRecord(self, resourceUri, jsonData):
		return requests.post(self.url + resourceUri, headers=self.headers, data=jsonData, verify=self.verifySSL)
	
	def getAllResourceIDs(self):
		return requests.get(self.repositoryUrl + '/resources?all_ids=true', headers=self.headers, verify=self.verifySSL)
		
	def getResourceByID(self, resourceID):
		return requests.get(self.repositoryUrl + '/resources/' + str(resourceID), headers=self.headers, verify=self.verifySSL) 
		
	def getResourceIDByEADID(self, eadID):
		resourceIDs = self.getAllResourceIDs().json()
		logging.info('--- Getting a list of all resources ---')
		for r in resourceIDs:
			resource = self.getResourceByID(str(r)).json()
			try:
				if eadID in resource["ead_id"]:
					return str(r)
			except KeyError as e:
				logging.warning("Resource %s does not contain an eadID", str(r))
		return None
		
	def getResourceIDbyIdentifiers(self, id_0=None, id_1=None, id_2=None, id_3=None):
		resourceIDs = self.getAllResourceIDs().json()
		logging.info('--- Getting a list of all resources ---')
		for r in resourceIDs:
			resource = self.getResourceByID(str(r)).json()
			print "id_0: ", resource["id_0"], " id_1: ", resource["id_1"], " id_2: ", resource["id_2"], " id_3: ", resource["id_3"]
		
	#Creates a digital object in ASpace from passed JSON
	def createDigitalObject(self, dig_obj_json):
		#dig_obj_data = json.dumps(dig_obj_json)
		return requests.post(self.repositoryUrl+'/digital_objects', headers=self.headers, data=dig_obj_json, verify=self.verifySSL)
		
	def getAllEvents(self):
		parameters = {"all_ids":True}
		return requests.get(self.repositoryUrl+'/events?all_ids=true', headers=self.headers, verify=self.verifySSL)
	
	def getEventByID(self, eventID):
		return requests.get(self.repositoryUrl+'/events/'+str(eventID), headers=self.headers, verify=self.verifySSL)
	
	def createEvent(self, eventJson):
		return requests.post(self.repositoryUrl+'/events', data=eventJson, headers=self.headers, verify=self.verifySSL)
		
	def updateEvent(self, eventURI, eventJson):
		return requests.post(self.url+eventURI, data=eventJson, headers=self.headers, verify=self.verifySSL)
		
	def getLinkedRecord(self, linkref):
		return requests.get(self.url+linkref, headers=self.headers, verify=self.verifySSL)
		
	def getAllAccessions(self):
		return requests.get(self.repositoryUrl+'/accessions?all_ids=true', headers=self.headers, verify=self.verifySSL)
		
	def getAccessionRecord(self, accId):
		return requests.get(self.repositoryUrl+'/accessions/'+ str(accId), headers=self.headers, verify=self.verifySSL)
		
	def updateAccessionRecord(self, jsonData, accUri):
		return requests.post(self.url + accUri,headers=self.headers, data=jsonData, verify=self.verifySSL)
		
	def exportEAD(self, destination, resourceID, eadID, exportUnpublished, exportDaos, number_cs, exportPdf):
		if not os.path.exists(destination):
		    os.makedirs(destination)
		try:
		    with open(os.path.join(destination, eadID), 'wb') as fd:
		    	logging.info("%s export begin", eadID)
		        ead = requests.get(self.repositoryUrl +'/resource_descriptions/'+str(resourceID)+'.xml?include_unpublished={exportUnpublished}&include_daos={exportDaos}&numbered_cs={number_cs}&print_pdf={exportPdf}'.format(exportUnpublished=exportUnpublished, exportDaos=exportDaos, number_cs=number_cs, exportPdf=exportPdf), headers=self.headers, verify=self.verifySSL, stream=True)
		        filename = stream.stream_response_to_file(ead, path=fd)
		        fd.close
		        logging.info('%s exported to %s', eadID, os.path.join(destination,resourceID))
		except exceptions.StreamingError as e:
		    logging.warning(e.message)
		    
		
	def printJson(self, jsonData):
		print json.dumps(jsonData, sort_keys=True, indent=4, separators=(',', ': '))
