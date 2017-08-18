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
		self.asBaseURL = self.config.get('ArchivesSpace', 'baseURL')
		if self.config.get('ArchivesSpace', 'verifySSL') == 'True':
			self.asSSLVerify = True
		else:
			self.asSSLVerify = False
		self.asRepository = self.config.get('ArchivesSpace', 'repository')
		self.exportUnpublished = self.config.get('EADexport', 'exportUnpublished')
		self.exportDaos = self.config.get('EADexport', 'exportDaos')
		self.number_cs = self.config.get('EADexport', 'exportNumbered')
		self.exportPdf = self.config.get('EADexport', 'exportPdf')
		self.exportDestination = self.config.get('EADexport', 'eadFilepath')
		self.ppDestination = self.config.get('PrettyPrintExport', 'ppFilepath')
		self.aspace = ArchivesSpy.ASpace(self.asBaseURL, self.asSSLVerify, self.asRepository)
		logging.basicConfig(filename=self.config.get('Logging', 'filename'), format=config.get('Logging', 'format', 1), datefmt=config.get('Logging', 'datefmt', 1), level=config.get('Logging', 'level', 0))

	def processXSL(self, sourcepath, xslpath, outputpath):
		sourceflag = "-s:" + sourcepath
		xslflag = "-xsl:" + xslpath
		outputflag = "-o:" + outputpath
		subprocess.call(['java', '-jar', 'saxon9he.jar', sourceflag, xslflag, outputflag])
	
	
	def outputHTML(self, ead):
		sourcepath = self.exportDestination + ead + ".xml"
		xslpath = self.config.get('HTMLexport', 'htmlStylesheet')
		outputpath = self.config.get('HTMLexport', 'htmlFilepath') + ead + ".html"
		self.processXSL(sourcepath, xslpath, outputpath)
		
	def prettyprintEAD(self, eadID):
		sourcepath = self.exportDestination + eadID
		xslpath = self.config.get('PrettyPrintExport', 'ppStylesheet')
		outputpath = self.config.get('PrettyPrintExport', 'ppFilepath') + eadID
		self.processXSL(sourcepath, xslpath, outputpath)
			
	def outputOAC(self, eadID):
		sourcepath = self.exportDestination + eadID
		xslpath = self.config.get('OACexport', 'oacStylesheet')
		outputpath = self.config.get('OACexport', 'oacFilepath') + eadID
		self.processXSL(sourcepath, xslpath, outputpath)
			
	def processEAD(self, resourceID, ead, eadID, processOAC):
		print "--- Exporting ", eadID, " to ", self.exportDestination, " ---"
		ts = datetime.datetime.now()
		self.aspace.exportEAD(self.exportDestination, resourceID, eadID, self.exportUnpublished, self.exportDaos, self.number_cs, self.exportPdf)
		tf = datetime.datetime.now()
		te = tf - ts
		print "--- Export completed in: ", te, " ---"
		print "--- Prettifying xml ---"
		self.prettyprintEAD(eadID)
		print "--- Processing html ---"
		self.outputHTML(ead)
		if processOAC:
			print "--- Processing for OAC ---"
			self.outputOAC(eadID)
	
	def exportAll(self, processOAC):
		print "--- Exporting all finding aids ---"
		ts = datetime.datetime.now()
		resourceIDs = self.aspace.getAllResourceIDs().json()
		for r in resourceIDs:
			resource = self.aspace.getResourceByID(str(r)).json()
			try:
				eadID=resource["ead_id"]
				ead=eadID[:-4]
				print ead
				self.processEAD(str(r), ead, eadID, processOAC)
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
		exporter.exportAll(args.oac)
	else:
		for ead in args.eadid:
			if ead.lower() == 'all':
				exporter.exportAll(args.oac)
			else:
				eadID = ead + '.xml'
				resourceID = exporter.aspace.getResourceIDByEADID(eadID)
				if resourceID != None:
					exporter.processEAD(resourceID, ead, eadID, args.oac)
				else:
					print "--- EAD: ", ead, " not found ---"
		
	
if __name__ == '__main__':
	main()