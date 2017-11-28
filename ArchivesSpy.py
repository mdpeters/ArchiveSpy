#!/usr/bin/env python
import requests, json, csv, getpass, argparse, sys, logging, os, urllib
from requests_toolbelt import exceptions
from requests_toolbelt.downloadutils import stream
			
class ASpace():
	def __init__(self, url="http://localhost:8089", verifySSL=False, repository="2"):
		self.url = url
		self.verifySSL = verify_SSL
		self.auth = None
		self.session = None
		self.headers = None
		self.repository_uri = "/repositories/" + repository
		self.repository_url = self.url + self.repositoryUri
				
	def post_request(self, url, request_data=None):
		if self.headers is not None:
			if request_data is not None:
				return request.post(url, data=request_data, headers=self.headers, verify=self.verify_SSL)
			else:
				return request.post(url, headers=self.headers, verify=self.verify_SSL)
		else:
			if request_data is not None:
				return request.post(url, data=request_data, verify=self.verify_SSL)
			else:
				return request.post(url, verify=self.verify_SSL)
	
	def get_request(self, url, request_paramaters=None):
		if request_paramaters is not None:
			return requests.get(url, params=request_parameters, headers=self.headers, verify=self.verify_SSL)
		else:
			return requests.get(url, headers=self.headers, verify=self.verify_SSL)
	
	def init_session(self, username="admin", password="admin"):
		try:
			escaped_password = urllib.quote(password)
			response = self.post_request(self.url+'/users/'+username+'/login?password='+escaped_password)
			#response = requests.post(self.url+'/users/'+username+'/login?password='+safe_password, verify=self.verifySSL)
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
			
	def get_repositories(self):
		return self.get_request(self.url+'/repositories')
	
	#Update to be more generic, pass repository number or name to set
	def set_repository(self, repository_number):
		self.repository_uri = "/repositories/" + str(repository)
		self.repository_url = self.url + self.repositoryUri
		
	def set_repository_url(self):
		self.repositoryUrl = self.url + self.repositoryUri
		
	def search_repository(self, search):
		return self.get_request(self.repositoryUrl+'/search?page=1&q='+search)
		
	def get_agent_corp_by_ID(self, agent_ID):
		return self.get_request(self.url+'/agents/corporate_entities/'+agent_ID)
		
	def get_agent_person_by_ID(self, agent_ID):
		return self.get_request(self.url+'/agents/people/'+agentID)
		
	def get_all_archival_object_IDs(self):
		return self.get_request(self.repository_url+'/archival_objects?all_ids=true')
	
	def get_archival_object_by_ref_ID(self, ref_ID):
		parameters = {"ref_id[]":ref_ID}
		archival_object_lookup = self.get_request(self.repository_url+'/find_by_id/archival_objects', parameters).json()
		archival_object_uri = archival_object_lookup['archival_objects'][0]['ref']
		return self.get_request(self.url+archival_object_uri)
		
	def update_archival_object(self, archival_object_uri, json_data):
		return self.post_request(self.url + archival_object_uri, data=json_data)
		
	def update_resource_record(self, resource_uri, json_data):
		return self.post_request(self.url+resource_uri, json_data)
	
	def get_all_resource_IDs(self):
		return self.get_request(self.repository_url+'/resources?all_ids=true')
		
	def getResourceByID(self, resource_ID):
		return self.get_request(self.repository_url+'/resources/'+str(resource_ID)) 
		
	def get_resource_ID_by_EAD_ID(self, ead_ID):
		resource_IDs = self.get_all_resource_IDs().json()
		logging.info('--- Getting a list of all resources ---')
		for r in resource_IDs:
			resource = self.get_resource_by_ID(str(r)).json()
			try:
				if ead_ID in resource["ead_id"]:
					return str(r)
			except KeyError as e:
				logging.warning("Resource %s does not contain an eadID", str(r))
		return None
		
	def get_resource_ID_by_identifiers(self, id_0=None, id_1=None, id_2=None, id_3=None):
		resource_IDs = self.get_all_resource_IDs().json()
		logging.info('--- Getting a list of all resources ---')
		for r in resourceIDs:
			resource = self.get_resource_by_ID(str(r)).json()
			print "id_0: ", resource["id_0"], " id_1: ", resource["id_1"], " id_2: ", resource["id_2"], " id_3: ", resource["id_3"]
		
	#Creates a digital object in ASpace from passed JSON
	def create_digital_object(self, dig_obj_json):
		#dig_obj_data = json.dumps(dig_obj_json)
		return self.post_request(self.repositoryUrl+'/digital_objects', dig_obj_json)
		
	def get_all_events(self):
		return self.get_request(self.repositoryUrl+'/events?all_ids=true')
	
	def get_event_by_ID(self, event_ID):
		return self.get_request(self.repositoryUrl+'/events/'+str(event_ID))
	
	def create_event(self, event_json):
		return self.post_request(self.repositoryUrl+'/events', event_json)
		
	def update_event(self, event_URI, event_json):
		return self.post_request(self.url+event_URI, event_json)
		
	def get_linked_record(self, link_ref):
		return self.get_request(self.url+link_ref)
		
	def get_all_accessions(self):
		return self.get_request(self.repository_url+'/accessions?all_ids=true')
		
	def get_accession_record(self, acc_ID):
		return self.get_request(self.repository_url+'/accessions/'+ str(acc_ID))
		
	def update_accession_record(self, json_data, acc_uri):
		return self.post_request(self.url+acc_uri, json_data)
		
	def export_EAD(self, destination, resource_ID, ead_ID, export_unpublished, export_daos, number_cs, export_pdf):
		if not os.path.exists(destination):
		    os.makedirs(destination)
		try:
		    with open(os.path.join(destination, ead_ID), 'wb') as fd:
		    	logging.info("%s export begin", ead_ID)
		        ead = self.get_request(self.repository_url +'/resource_descriptions/'+str(resource_ID)+'.xml?include_unpublished={exportUnpublished}&include_daos={exportDaos}&numbered_cs={number_cs}&print_pdf={exportPdf}'.format(exportUnpublished=export_unpublished, exportDaos=export_daos, number_cs=number_cs, exportPdf=export_pdf), headers=self.headers, verify=self.verifySSL, stream=True)
		        filename = stream.stream_response_to_file(ead, path=fd)
		        fd.close
		        logging.info('%s exported to %s', ead_ID, os.path.join(destination,resource_ID))
		except exceptions.StreamingError as e:
		    logging.warning(e.message)
		    
		
	def printJson(self, jsonData):
		print json.dumps(jsonData, sort_keys=True, indent=4, separators=(',', ': '))
