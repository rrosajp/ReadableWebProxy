
import calendar
import datetime
import json
import os
import os.path
import shutil
import tqdm
import traceback
from concurrent.futures import ThreadPoolExecutor

import urllib.error
import urllib.parse

import WebRequest

from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import sqlalchemy.exc

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()

import common.database as db
import common.Exceptions
import common.management.util
import common.management.file_cleanup
import common.management.WebMirrorManage

import WebMirror.processor.RssProcessor
import flags
import pprint
import config
from config import C_RAW_RESOURCE_DIR

from WebMirror.Engine import SiteArchiver
import WebMirror.OutputFilters.rss.FeedDataParser
import WebMirror.OutputFilters.util.feedNameLut
import common.util.urlFuncs as urlFuncs

from app.sub_views.rss_views import proto_process_releases

def exposed_sort_json(json_name):
	'''
	Load a file of feed missed json entries, and sort it into
	a much nicer to read output format.

	Used internally by the rss_db/rss_day/week/month functionality.
	'''
	with open(json_name) as fp:
		cont = fp.readlines()
	print("Json file has %s lines." % len(cont))

	data = {}
	for line in cont:
		val = json.loads(line)
		name = val['SourceName']
		if not name in data:
			data[name] = []

		data[name].append(val)
	out = []
	for key in data:

		out.append((len(data[key]), data[key]))

	out.sort(key=lambda x: (x[0], x[1]*-1))
	out.sort(key=lambda x: (x[1]*-1))

	key_order = [
		"SourceName",
		"Title",
		"Tags",
		"Feed URL",
		"Vol",
		"Chp",
		"Frag",
		"Postfix",
		"GUID",
	]

	outf = json_name+".pyout"
	try:
		os.unlink(outf)
	except FileNotFoundError:
		pass

	with open(outf, "w") as fp:
		for item in out:
			# print(item[1])
			items = item[1]
			_ = [tmp['Tags'].sort() for tmp in items]
			items.sort(key=lambda x: (x['Tags'], x['Title']))

			for value in items:
				for key in key_order:
					fp.write("%s, " % ((key, value[key]), ))
				fp.write("\n")



def exposed_missing_lut(fetchTitle=False):
	'''
	Iterate over distinct RSS feed sources in database,
	and print any for which there is not an entry in
	feedDataLut.py to the console.
	'''
	with db.session_context() as sess:
		wg = WebRequest.WebGetRobust()
		rules = WebMirror.rules.load_rules()
		feeds = [item['feedurls'] for item in rules]
		feeds = [item for sublist in feeds for item in sublist]
		# feeds = [urllib.parse.urlsplit(tmp).netloc for tmp in feeds]
		for feed in feeds:
			if not WebMirror.OutputFilters.util.feedNameLut.getNiceName(sess, feed):
				netloc = urllib.parse.urlsplit(feed).netloc
				meta = netloc
				if fetchTitle:
					chunks = feed.split("/")
					baseurl = "/".join(chunks[:3])
					meta = common.management.util.get_page_title(wg, baseurl)
				print('Missing: "%s" %s: "%s",' % (netloc, " " * (50 - len(netloc)), meta))

def exposed_fetch_rss(tgt):
	'''
	Identical to `test_retrieve`, except debug printing is supressed and RSS debugging is enabled.
	'''
	common.management.WebMirrorManage.exposed_fetch(tgt, debug=False, rss_debug=True)


def exposed_test_all_rss():
	'''
	Fetch all RSS feeds and process each. Done with 8 parallel workers.
	'''
	print("fetching and debugging RSS feeds")
	rules = WebMirror.rules.load_rules()
	feeds = [item['feedurls'] for item in rules]
	feeds = [item for sublist in feeds for item in sublist]

	flags.RSS_DEBUG = True
	with ThreadPoolExecutor(max_workers=8) as executor:
		for url in feeds:
			try:
				executor.submit(common.management.WebMirrorManage.exposed_fetch, url, debug=False)
			except common.Exceptions.DownloadException:
				print("failure downloading page!")
			except urllib.error.URLError:
				print("failure downloading page!")


def delete_bad_rss_by_url():

	with db.session_context() as sess:

		bad_sources = 	sess.query(db.RssFeedUrlMapper) \
				.filter(or_(

					db.RssFeedUrlMapper.feed_url.like("%/comments/%"),
					db.RssFeedUrlMapper.feed_url.like("%pokegirls.org%"),
					db.RssFeedUrlMapper.feed_url.like("%tracking.feedpress.it%"),
					db.RssFeedUrlMapper.feed_url.like("%40pics.com%"),
					db.RssFeedUrlMapper.feed_url.like("%storiesonline.org%"),
					db.RssFeedUrlMapper.feed_url.like("%www.miforcampuspolice.com%"),
					db.RssFeedUrlMapper.feed_url.like("%198.199.119.217%"),
					db.RssFeedUrlMapper.feed_url.like("%www.fictionmania.tv%"),
					db.RssFeedUrlMapper.feed_url.like("%www.asstr.org%"),
					db.RssFeedUrlMapper.feed_url.like("%storiesonline.net%"),
					db.RssFeedUrlMapper.feed_url.like("%www.booksiesilk.com%"),
					db.RssFeedUrlMapper.feed_url.like("%www.miforcampuspolice.com%"),
					db.RssFeedUrlMapper.feed_url.like("%wordpress-8932-19922-46194.cloudwaysapps.com%"),
					db.RssFeedUrlMapper.feed_url.like("%wordpress-8932-48656-126389.cloudwaysapps.com%"),
					db.RssFeedUrlMapper.feed_url.like("%www.mcstories.com%"),
					db.RssFeedUrlMapper.feed_url.like("%www.asstr.org%"),

					db.RssFeedUrlMapper.feed_url.like("%www.miforcampuspolice.com%"),
					db.RssFeedUrlMapper.feed_url.like("%#comment-%"),
					db.RssFeedUrlMapper.feed_url.like("%CommentsForInMyDaydreams%"),
					db.RssFeedUrlMapper.feed_url.like("%www.fanfiction.net%"),
					db.RssFeedUrlMapper.feed_url.like("%www.fictionpress.com%"),
					db.RssFeedUrlMapper.feed_url.like("%?showComment=%"),
					db.RssFeedUrlMapper.feed_url.like("%www.booksie.com%")))    \
				.order_by(db.RssFeedUrlMapper.feed_url) \
				.all()
		bad_sources = list(bad_sources)
		print("Bad sources")
		print(bad_sources)

		bad = sess.query(db.RssFeedPost) \
				.filter(or_(

					db.RssFeedPost.contenturl.like("%/comments/%"),
					db.RssFeedPost.contenturl.like("%pokegirls.org%"),
					db.RssFeedPost.contenturl.like("%tracking.feedpress.it%"),
					db.RssFeedPost.contenturl.like("%40pics.com%"),
					db.RssFeedPost.contenturl.like("%storiesonline.org%"),
					db.RssFeedPost.contenturl.like("%www.miforcampuspolice.com%"),
					db.RssFeedPost.contenturl.like("%198.199.119.217%"),
					db.RssFeedPost.contenturl.like("%www.fictionmania.tv%"),
					db.RssFeedPost.contenturl.like("%www.asstr.org%"),
					db.RssFeedPost.contenturl.like("%storiesonline.net%"),
					db.RssFeedPost.contenturl.like("%www.booksiesilk.com%"),
					db.RssFeedPost.contenturl.like("%www.miforcampuspolice.com%"),
					db.RssFeedPost.contenturl.like("%wordpress-8932-19922-46194.cloudwaysapps.com%"),
					db.RssFeedPost.contenturl.like("%wordpress-8932-48656-126389.cloudwaysapps.com%"),
					db.RssFeedPost.contenturl.like("%www.mcstories.com%"),
					db.RssFeedPost.contenturl.like("%www.asstr.org%"),

					db.RssFeedPost.contenturl.like("%www.miforcampuspolice.com%"),
					db.RssFeedPost.contenturl.like("%#comment-%"),
					db.RssFeedPost.contenturl.like("%CommentsForInMyDaydreams%"),
					db.RssFeedPost.contenturl.like("%www.fanfiction.net%"),
					db.RssFeedPost.contenturl.like("%www.fictionpress.com%"),
					db.RssFeedPost.contenturl.like("%?showComment=%"),
					db.RssFeedPost.contenturl.like("%www.booksie.com%")))    \
				.order_by(db.RssFeedPost.contenturl) \
				.all()

		count = 0
		for bad in bad:
			print(bad.contenturl)

			while bad.author:
				bad.author.pop()
			while bad.tags:
				bad.tags.pop()
			sess.delete(bad)
			count += 1
			if count % 1000 == 0:
				print("Committing at %s" % count)
				sess.commit()

		print("Done. Committing...")
		print("Total changed rows: %s" % count)
		sess.commit()

def delete_bad_by_check():
	with db.session_context() as sess:
		print("Fetching all rows to scan")
		all_bad = sess.query(db.RssFeedPost).all()
		all_bad = list(all_bad)
		print("Processing %s rows." % len(all_bad))

		count = 0
		deleted = False
		for bad in all_bad:
			post_dict = {
				'srcname' : WebMirror.OutputFilters.util.feedNameLut.getNiceName(sess, bad.contenturl),
				'title'   : bad.title,
				'linkUrl' : bad.contenturl,
				'guid'    : bad.contentid,
			}
			if WebMirror.OutputFilters.rss.FeedDataParser.should_ignore_feed_post(post_dict):
				print(post_dict)
				sess.delete(bad)
				deleted = True
			count += 1
			if count % 1000 == 0:
				print("Processed %s of %s" % (count, len(all_bad)))
				if deleted:
					print("Committing...", end='')
					sess.commit()
					deleted = False
					print("Committed")
		if deleted:
			print("Committing...", end='')
			sess.commit()
			print("Committed")

		print("Done")

def exposed_delete_comment_feed_items():
	'''
	Iterate over all retreived feed article entries, and delete any that look
	like they're comment feed articles.
	'''
	delete_bad_rss_by_url()
	delete_bad_by_check()


def exposed_delete_feed(feed_name, do_delete, search_str):
	'''
	Feed name is the readable name of the feed, from feedNameLut.py.
	do delete is a boolean that determines if the deletion is actually done, or the actions are
		just previewed. Unless do_delete.lower() == "true", no action will actually be
		taken.
	search_str is the string of items to search for. Searches are case sensitive, and the only
		component of the feed that are searched within is the title.
		search_str is split on the literal character "|", for requiring multiple substrings
		be in the searched title.

	Delete the rss entries for a feed, using a search key.

	'''

	with db.session_context() as sess:
		items = sess.query(db.RssFeedPost)               \
			.filter(db.RssFeedPost.feed_entry.feed_name == feed_name) \
			.all()

		do_delete = "true" in do_delete.lower()

		searchitems = search_str.split("|")
		for item in items:
			itemall = " ".join([item.title] + item.tags)
			if all([searchstr in itemall for searchstr in searchitems]):
				print(itemall)
				if do_delete:
					print("Deleting item")
					sess.delete(item)

		sess.commit()



def exposed_rss_db_sync(target = None, days=False, silent=False):
	'''
	Feed RSS feed history through the feedparsing system, generating a log
	file of the feed articles that were not captured by the feed parsing system.

	Target is an optional netloc. If not none, only feeds with that netloc are
		processed.
	Days is the number of days into the past to process. None results in all
		available history being read.
	Silent suppresses some debug printing to the console.
	'''

	json_file = 'rss_filter_misses-1.json'

	config.C_DO_RABBIT = False

	write_debug = True
	if silent:
		config.C_DO_RABBIT = False
	if target:
		config.C_DO_RABBIT = False
		flags.RSS_DEBUG    = True
		write_debug = False
	else:
		try:
			os.unlink(json_file)
		except FileNotFoundError:
			pass


	with db.session_context() as sess:

		parser = WebMirror.processor.RssProcessor.RssProcessor(loggerPath   = "Main.RssDb",
																pageUrl     = 'http://www.example.org',
																pgContent   = '',
																type        = 'application/atom+xml',
																transfer    = False,
																debug_print = True,
																db_sess     = sess,
																write_debug = write_debug)


		print("Getting feed items....")

		if target:
			print("Limiting to '%s' source." % target)
			feed_items = sess.query(db.RssFeedPost) \
					.filter(db.RssFeedPost.feed_entry.feed_name == target)    \
					.order_by(db.RssFeedPost.title)           \
					.all()

		elif days:
			print("RSS age override: ", days)
			cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
			feed_items = sess.query(db.RssFeedPost) \
					.filter(db.RssFeedPost.published > cutoff)  \
					.order_by(db.RssFeedPost.title)             \
					.all()
		else:
			feed_items = sess.query(db.RssFeedPost) \
					.order_by(db.RssFeedPost.title)           \
					.all()


		print("Feed items: ", len(feed_items))

		for item in feed_items:
			ctnt = {}
			ctnt['srcname']   = item.feed_entry.feed_name
			ctnt['title']     = item.title
			ctnt['tags']      = item.tags
			ctnt['linkUrl']   = item.contenturl
			ctnt['guid']      = item.contentid
			ctnt['published'] = calendar.timegm(item.published.timetuple())

			# Pop()ed off in processFeedData().
			ctnt['contents']  = 'wat'

			try:
				ret = parser.processFeedData(sess, ctnt, tx_raw=False, tx_parse=not bool(days))
				print(ret)
			except ValueError:
				pass
			# print(ctnt)
		if target is None:
			exposed_sort_json(json_file)

def exposed_rss_db_silent():
	'''
	Eqivalent to rss_db_sync(None, False, True)
	'''
	exposed_rss_db_sync(silent=True)

def exposed_rss_day():
	'''
	Eqivalent to rss_db_sync(1)

	Effectively just processes the last day of feed entries.
	'''
	exposed_rss_db_sync(days=1)

def exposed_rss_week():
	'''
	Eqivalent to rss_db_sync(7)

	Effectively just processes the last week of feed entries.
	'''
	exposed_rss_db_sync(days=7)

def exposed_rss_month():
	'''
	Eqivalent to rss_db_sync(45)

	Effectively just processes the last 45 days of feed entries.
	'''
	exposed_rss_db_sync(days=45)

def exposed_process_qidian_feeds():
	'''
	Scan the qidian feed items, and extract the book url segments which are not
	in the feedparser url-seg -> title map.

	Given those segments, then do a HTTP fetch, and pull out the page title.
	Finally, print that information in a nice table for updating the
	scraper func.
	'''

	with db.session_context() as sess:

		parser = WebMirror.processor.RssProcessor.RssProcessor(loggerPath   = "Main.RssDb",
																pageUrl     = 'http://www.example.org',
																pgContent   = '',
																type        = 'application/atom+xml',
																transfer    = False,
																debug_print = True,
																db_sess     = sess,
																write_debug = False)


		print("Getting feed items....")

		feed_item = sess.query(db.RssFeedEntry) \
				.filter(db.RssFeedEntry.feed_name == "Qidian")    \
				.one()

		feed_url = feed_item.urls[0].feed_url
		pfunc = feed_item.get_func()

		missing = []

		for release in feed_item.releases:
			item = {}
			item['title']    = release.title
			item['guid']     = release.contentid
			item['linkUrl']  = release.contenturl

			item['feedUrl']  = feed_url
			item['srcname']  = "wat"
			item['published']  = "wat"

			ret = pfunc(item)
			if not ret:
				missing.append(release.contenturl)

		urls = {}
		for url in missing:
			root, _ = url.rsplit("/", 1)
			urls[root] = url

		wg = WebRequest.WebGetRobust()

		lines = []
		for root, url in urls.items():
			urlfrag = root.split("www")[-1]
			meta = common.management.util.get_page_title(wg, url)
			title =  meta['title']
			outstr = "		('www{}/', '{}', '?'),".format(urlfrag, title)
			lines.append(outstr)

		for outstr in lines:
			print(outstr)

def exposed_fetch_unmapped_qidian_items():
	'''
	'''
	from app import app
	from flask import g

	# with app.app_context():
	with app.test_request_context(""):
		app.preprocess_request()

		print("Querying for rss feed items.")
		# Hard coded for my database. Because fuk u \
		releases = g.session.query(db.RssFeedPost)   \
			.filter(db.RssFeedPost.feed_id == 2578)   \
			.all()

		print("Processing items")
		urls = [item.contenturl for item in releases]

		relmap = {}
		for release in releases:
			if "/rssbook/" in release.contenturl:
				continue
			trimmed = "/".join(release.contenturl.split("/")[:5])+"/"
			relmap.setdefault(trimmed, [])
			relmap[trimmed].append(release)

		print("Fetched %s urls, %s distinct series" % (len(urls), len(relmap)))

		for itemlist in relmap.values():
			itemlist.sort(key=lambda x: x.id)

		truncated_releases = [tmp[0] for tmp in relmap.values()]

		print("Truncated releases: %s" % len(truncated_releases))

		items = proto_process_releases(truncated_releases)
		print("Processing resulted in %s feed items" % len(items['missed']))

		feed_urls = [tmp[1]['linkUrl'] for tmp in items['missed']]
		trimmed = ["/".join(tmp.split("/")[:5])+"/" for tmp in feed_urls]

		new_series_urls = list(set(trimmed))
		print("Releases consolidated to %s distinct series" % len(new_series_urls))

	bad_names = [
		'12testett11223355',
		'webnovel test003',
		'www.webnovel.com',
	]
	wg = WebRequest.WebGetRobust()
	for url in new_series_urls:
		meta = common.management.util.get_page_title(wg, url)
		if not any([tmp in meta['title'] for tmp in bad_names]):
			print('Missing: "%s" %s: "%s",' % (url, " " * (50 - len(url)), meta))
			itemid = url.split("/")
			itemid = [tmp for tmp in itemid if tmp]
			itemid = itemid[-1]
			print("'%s' : ('%s',                                                                     '%s')," % (itemid, meta['title'].strip(), 'oel' if 'is-orig' in meta and meta['is-orig'] else 'translated'))

def chunks(l, n):
	"""Yield successive n-sized chunks from l."""
	for i in range(0, len(l), n):
		yield l[i:i + n]

def exposed_retrigger_feed_urls():
	'''
	Retrigger the content urls from each feed item.
	'''

	# RssFeedPost attributes:
	# 	id
	# 	type
	# 	feed_id
	# 	contenturl
	# 	contentid
	# 	title
	# 	contents
	# 	updated
	# 	published
	# 	tag_rel
	# 	author_rel
	# 	tags
	# 	author

	urls = set()
	with db.session_context() as sess:
		processor = WebMirror.processor.RssProcessor.RssProcessor(loggerPath   = "Main.RssDb",
																pageUrl     = 'http://www.example.org',
																pgContent   = '',
																type        = 'application/atom+xml',
																transfer    = False,
																debug_print = True,
																db_sess     = sess,
																write_debug = False)

		print("Loading posts....")
		items = sess.query(db.RssFeedPost).all()
		print("Loaded %s rows" % len(items))
		have_content = [tmp for tmp in items if tmp.contents]
		print("%s rows have content" % len(have_content))

		pbar = tqdm.tqdm(items, desc="Retriggering RSS URLs")
		for post in pbar:
			if post.contenturl.startswith("tag:blogger.com"):
				continue

			if post.contenturl and not '#comment_' in post.contenturl:
				urls.add(post.contenturl)

			if post.contents and post.contents != 'Disabled?' and post.contents != 'wat':
				soup = WebRequest.as_soup(post.contents)
				# print(post.contents)
				# Make all the page URLs fully qualified, so they're unambiguous
				soup = urlFuncs.canonizeUrls(soup, post.contenturl)

				# pull out the page content and enqueue it. Filtering is
				# done in the parent.
				plainLinks = processor.extractLinks(soup, post.contenturl)
				imageLinks = processor.extractImages(soup, post.contenturl)

				# if plainLinks or imageLinks:
				# 	print((len(plainLinks), len(imageLinks)))

				urls.update(plainLinks)
				urls.update(imageLinks)
			# pbar.set_description("Links: %s" % len(urls))

	urls = list(urls)

	urld = {}
	for url in [tmp for tmp in urls if tmp]:
		nl = urllib.parse.urlsplit(url).netloc
		if nl:
			urld.setdefault(nl, [])
			urld[nl].append(url)

	print("Extracted %s unique links for %s netlocs" % (len(urls), len(urld)))

	# rules = WebMirror.rules.load_rules()
	# feeds = [item['feedurls'] for item in rules]
	# feeds = [item for sublist in feeds for item in sublist]
	# url = feeds[0]
	# parsed = urllib.parse.urlparse(url)
	# root = urllib.parse.urlunparse((parsed[0], parsed[1], "", "", "", ""))
	# print("Using feed url %s for job base" % url)

	try:
		with db.session_context() as sess:
			archiver = SiteArchiver(None, sess, None)
			for key, urls in tqdm.tqdm(urld.items(), desc='Source Netlocs'):
				sel_url = urls[0]
				parsed = urllib.parse.urlparse(sel_url)
				root = urllib.parse.urlunparse((parsed[0], parsed[1], "", "", "", ""))

				job = db.WebPages(
					url       = sel_url,
					starturl  = root,
					netloc    = key,
					distance  = 0,
					is_text   = True,
					priority  = db.DB_LOW_PRIORITY,
					type      = 'unknown',
					fetchtime = datetime.datetime.now(),
					)
				for chunk in chunks(urls, 500):
					archiver.upsertResponseLinks(job, plain=chunk, resource=[], debug=True, interactive=True)

	except Exception as e:
		traceback.print_exc()
