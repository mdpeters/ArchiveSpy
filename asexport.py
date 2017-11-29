#!/usr/bin/env python
import ArchivesSpy
import requests
import argparse
import ConfigParser
import logging
import subprocess
import datetime
import sys
import getpass

class ASExport():
	
	def __init__(self, config):
		self.config = config
		self.as_base_URL = self.config.get('ArchivesSpace', 'baseURL')
		if self.config.get('ArchivesSpace', 'verifySSL') == 'True':
			self.as_SSL_verify = True
		else:
			self.as_SSL_verify = False
		self.as_repository = self.config.get('ArchivesSpace', 'repository')
		self.export_unpublished = self.config.get('EADexport', 'exportUnpublished')
		self.export_daos = self.config.get('EADexport', 'exportDaos')
		self.number_cs = self.config.get('EADexport', 'exportNumbered')
		self.export_pdf = self.config.get('EADexport', 'exportPdf')
		self.export_destination = self.config.get('EADexport', 'eadFilepath')
		self.pp_destination = self.config.get('PrettyPrintExport', 'ppFilepath')
		self.aspace = ArchivesSpy.ASpace(self.as_base_URL, self.as_SSL_verify, self.as_repository)
		logging.basicConfig(filename=self.config.get('Logging', 'filename'), format=config.get('Logging', 'format', 1), datefmt=config.get('Logging', 'datefmt', 1), level=config.get('Logging', 'level', 0))

	def process_XSL(self, sourcepath, xslpath, outputpath, params=None):
		sourceflag = "-s:" + sourcepath
		xslflag = "-xsl:" + xslpath
		outputflag = "-o:" + outputpath
		if params != None:
			subprocess.call(['java', '-jar', 'saxon9he.jar', sourceflag, xslflag, outputflag, params])
		else:
			subprocess.call(['java', '-jar', 'saxon9he.jar', sourceflag, xslflag, outputflag])	
	
	def output_HTML(self, ead, params):
		sourcepath = self.export_destination + ead + ".xml"
		xslpath = self.config.get('HTMLexport', 'htmlStylesheet')
		outputpath = self.config.get('HTMLexport', 'htmlFilepath') + ead + ".html"
		self.process_XSL(sourcepath, xslpath, outputpath, params)
		
	def prettyprint_EAD(self, ead_ID):
		sourcepath = self.export_destination + ead_ID
		xslpath = self.config.get('PrettyPrintExport', 'ppStylesheet')
		outputpath = self.config.get('PrettyPrintExport', 'ppFilepath') + eadID
		self.process_XSL(sourcepath, xslpath, outputpath)
			
	def output_OAC(self, ead_ID):
		sourcepath = self.export_destination + ead_ID
		xslpath = self.config.get('OACexport', 'oacStylesheet')
		outputpath = self.config.get('OACexport', 'oacFilepath') + eadID
		self.process_XSL(sourcepath, xslpath, outputpath)
			
	def process_EAD(self, resource_ID, ead, ead_ID, process_OAC, no_daos):
		print "--- Exporting ", ead_ID, " to ", self.export_destination, " ---"
		ts = datetime.datetime.now()
		self.aspace.export_EAD(self.export_destination, resource_ID, ead_ID, self.export_unpublished, self.export_daos, self.number_cs, self.export_pdf)
		tf = datetime.datetime.now()
		te = tf - ts
		html_params = None
		if no_daos:
			html_params = "outputDAOs='false'"
		print "--- Export completed in: ", te, " ---"
		print "--- Prettifying xml ---"
		self.prettyprint_EAD(eadID)
		print "--- Processing html ---"
		self.outputHTML(ead, html_params)
		if processOAC:
			print "--- Processing for OAC ---"
			self.outputOAC(eadID)
	
	def export_all(self, process_OAC, no_dao):
		print "--- Exporting all finding aids ---"
		ts = datetime.datetime.now()
		resource_IDs = self.aspace.get_all_resource_IDs().json()
		for r in resource_IDs:
			resource = self.aspace.get_resource_by_ID(str(r)).json()
			try:
				ead_ID=resource["ead_id"]
				ead=ead_ID[:-4]
				print ead
				self.process_EAD(str(r), ead, ead_ID, process_OAC, no_dao)
			except KeyError as e:
				print "Resource ", r, " does not contain an eadID"
		tf = datetime.datetime.now()
		te = tf - ts
		print "--- Export all completed in: ", te, " ---"

def main():
	configFilePath = './export_config.cfg'
	config = ConfigParser.ConfigParser()
	config.read(configFilePath)
	exporter = ASExport(config)
	requests.packages.urllib3.disable_warnings()
	
	argsparser = argparse.ArgumentParser()
	argsparser.add_argument('eadid', help='EAD ID value (without the .xml extension)', nargs='*')
	argsparser.add_argument('-o', '--oac', help='Output OAC compliant version of EAD', action='store_true')
	argsparser.add_argument('-a', '--ar', help='Export all resource records from the selected repository', action='store_true')
	argsparser.add_argument('-n', '--nodao', help='Export without digital object links', action='store_true')
	args = argsparser.parse_args()
	
	try:
		py3 = sys.version_info[0] > 2
		if py3:
			username = input("Username: ")
		else:
			username = raw_input("Username: ")
			
		password = getpass.getpass()
		exporter.aspace.init_session(username, password)
	except SystemExit:
		print "Program terminated"
		return
	
	if args.ar:
		exporter.export_all(args.oac, args.nodao)
	else:
		for ead in args.eadid:
			if ead.lower() == 'all':
				exporter.exportAll(args.oac, args.nodao)
			else:
				ead_ID = ead + '.xml'
				resource_ID = exporter.aspace.get_resource_ID_by_EAD_ID(ead_ID)
				if resourceID != None:
					exporter.process_EAD(resourceID, ead, eadID, args.oac, args.nodao)
				else:
					print "--- EAD: ", ead, " not found ---"
		
	
if __name__ == '__main__':
	main()