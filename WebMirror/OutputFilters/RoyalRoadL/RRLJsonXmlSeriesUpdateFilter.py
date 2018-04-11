
import pprint
import re
import bs4
import collections
import datetime
import json

import xml.etree.ElementTree as et
import xmljson
import WebMirror.OutputFilters.FilterBase

import common.util.urlFuncs
import common.database as db

MIN_RATING = 5

########################################################################################################################
#
#	##     ##    ###    #### ##    ##     ######  ##          ###     ######   ######
#	###   ###   ## ##    ##  ###   ##    ##    ## ##         ## ##   ##    ## ##    ##
#	#### ####  ##   ##   ##  ####  ##    ##       ##        ##   ##  ##       ##
#	## ### ## ##     ##  ##  ## ## ##    ##       ##       ##     ##  ######   ######
#	##     ## #########  ##  ##  ####    ##       ##       #########       ##       ##
#	##     ## ##     ##  ##  ##   ###    ##    ## ##       ##     ## ##    ## ##    ##
#	##     ## ##     ## #### ##    ##     ######  ######## ##     ##  ######   ######
#
########################################################################################################################

def clean_parsed_data(d):
	d = dict(d)
	for key in list(d.keys()):
		if isinstance(d[key], (dict, collections.OrderedDict)):
			d[key] = clean_parsed_data(d[key])
		elif isinstance(d[key], (list, tuple)):
			d[key] = [clean_parsed_data(tmp) for tmp in d[key]]
		elif isinstance(d[key], str):
			d[key] = d[key].strip()

		if key in ['FirstUpdate', 'LastUpdate', 'Date']:
			d[key] = datetime.datetime.utcfromtimestamp(d[key])
	return d

class RRLJsonXmlSeriesUpdateFilter(WebMirror.OutputFilters.FilterBase.FilterBase):


	wanted_mimetypes = [
							'text/xml',
							'application/xml',
							'text/json',
							'application/json',
						]
	want_priority    = 50

	loggerPath = "Main.Filter.RoyalRoad.XmlJsonSeries"


	@staticmethod
	def wantsUrl(url):
		want = set([
			'https://royalroadl.com/api/',
			'http://royalroadl.com/api/',
			'https://www.royalroadl.com/api/',
			'http://www.royalroadl.com/api/',
		])
		url = url.lower()
		if any([url.startswith(tmp) for tmp in want]):

			print("RRLJsonXmlSeriesUpdateFilter Wants url: '%s'" % url)
			return True
		# print("RRLJsonXmlSeriesUpdateFilter doesn't want url: '%s'" % url)
		return False

	def __init__(self, **kwargs):

		self.kwargs     = kwargs


		self.pageUrl    = kwargs['pageUrl']

		self.content    = kwargs['pgContent']
		self.mtype      = kwargs['mimeType']
		self.db_sess    = kwargs['db_sess']

		print(kwargs.keys())

		self.log.info("Processing RoyalRoadL Json/XML Item")
		super().__init__(**kwargs)


##################################################################################################################################
##################################################################################################################################
##################################################################################################################################


	def extractSeriesReleases(self, seriesPageUrl, soup):

		containers = soup.find_all('div', class_='fiction-list-item')
		# print(soup)
		# print("container: ", containers)
		if not containers:
			return []
		urls = []
		for item in containers:
			div = item.find('h2', class_='fiction-title')
			a = div.find("a")
			if a:
				url = common.util.urlFuncs.rebaseUrl(a['href'], seriesPageUrl)
				urls.append(url)
			else:
				self.log.error("No series in container: %s", item)

		return set(urls)


	def retrigger_pages(self, releases):
		self.log.info("Total releases found on page: %s. Forcing retrigger of item pages.", len(releases))

		for release_url in releases:
			self.retrigger_page(release_url)

	def load_xml(self):
		xmlstring = re.sub(' xmlns="[^"]+"', '', self.content, count=1)
		tree = et.fromstring(xmlstring)
		data = xmljson.parker.data(tree)
		data = clean_parsed_data(data)

		print(data)

	def load_json(self):
		loaded = json.loads(self.content)
		content = {'ApiFictionInfoWithChapters' : loaded}
		content = clean_parsed_data(content)
		print(content)

	def processParsedData(self, loaded):
		print(loaded)


	def processPage(self, url, content):
		self.log.info("processPage() call: %s, %s", self.mtype, self.pageUrl)

		if self.mtype in ['text/xml', 'application/xml']:
			loaded = self.load_xml()
		elif self.mtype in ['text/json', 'application/json']:
			loaded = self.load_json()
		else:
			self.log.error("Unknown content type (%s)!", self.mtype)

		self.processParsedData(loaded)


##################################################################################################################################
##################################################################################################################################
##################################################################################################################################



	def extractContent(self):
		# print("Call to extract!")
		# print(self.amqpint)

		self.processPage(self.pageUrl, self.content)



def test():
	print("Test mode!")
	import logSetup
	import settings
	from WebMirror.Engine import SiteArchiver

	logSetup.initLogging()


	# urls = [
	# 		'https://royalroadl.com/api/fiction/updates?apiKey=' + settings.RRL_API_KEY,
	# 		# 'https://royalroadl.com/api/fiction/newreleases?apiKey=' + settings.RRL_API_KEY,
	# ]

	# for url in urls:
	# 	with db.session_context() as sess:
	# 		archiver = SiteArchiver(None, sess, None)
	# 		archiver.synchronousJobRequest(url, ignore_cache=True)

	with open("fiction_updates.xml", "r") as fp:
		content = fp.read()

	instance = RRLJsonXmlSeriesUpdateFilter(pageUrl="https://royalroadl.com/api/fiction/updates?apiKey=" + settings.RRL_API_KEY, pgContent=content, mimeType="application/xml", db_sess=None)
	print(instance)
	extracted = instance.extractContent()
	print("Extracted:", extracted)

	with open("json_reenc.json", "r") as fp:
		content2 = fp.read()

	instance = RRLJsonXmlSeriesUpdateFilter(pageUrl="https://royalroadl.com/api/fiction/updates?apiKey=" + settings.RRL_API_KEY, pgContent=content2, mimeType="application/json", db_sess=None)
	print(instance)
	extracted = instance.extractContent()
	print("Extracted:", extracted)


if __name__ == "__main__":
	test()


