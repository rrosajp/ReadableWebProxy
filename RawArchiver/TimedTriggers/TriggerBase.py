

import logging
import abc
import datetime
import psycopg2
import traceback
import urllib.parse
import sqlalchemy.exc
import common.database as db
import common.LogBase

class TriggerBaseClass(common.LogBase.LoggerMixin, metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def pluginName(self):
		return None

	@abc.abstractmethod
	def go(self):
		return None


	def __init__(self):
		super().__init__()
		self.loggerPath = "Main.RawTrigger.%s" % self.loggerPath
		self.db = db
		self.log.info("Loading %s Runner", self.pluginName)


	def _go(self):
		self.log.info("Checking %s for updates", self.pluginName)

		self.go()
		self.log.info("Update check for %s finished.", self.pluginName)


	def __raw_retrigger_with_cursor(self, url, cursor):

		self.log.info("Retriggering fetch for URL: %s", url)

		#  Fucking huzzah for ON CONFLICT!
		cmd = """

				INSERT INTO
					raw_web_pages
					(url, starturl, netloc, distance, is_text, priority, addtime, state)
				VALUES
					(%(url)s, %(starturl)s, %(netloc)s, %(distance)s, %(is_text)s, %(priority)s, %(addtime)s, %(state)s)
				ON CONFLICT (url) DO
					UPDATE
						SET
							state           = %(state)s,
							distance        = LEAST(EXCLUDED.distance, raw_web_pages.distance),
							priority        = LEAST(EXCLUDED.priority, raw_web_pages.priority),
							addtime         = LEAST(EXCLUDED.addtime, raw_web_pages.addtime),
							ignoreuntiltime = LEAST(EXCLUDED.addtime, raw_web_pages.addtime, %(ignoreuntiltime)s)
						WHERE
						(
								(raw_web_pages.state = 'complete' OR raw_web_pages.state = 'new' OR raw_web_pages.state = 'fetching' OR raw_web_pages.state = 'error')
							AND
								raw_web_pages.url = %(url)s
						)
				RETURNING
					raw_web_pages.state, raw_web_pages.url
					;

			""".replace("	", " ").replace("\n", " ")

		url_netloc = urllib.parse.urlsplit(url).netloc

		assert url.startswith("http")
		assert url_netloc


		# Forward-data the next walk, time, rather then using now-value for the thresh.
		data = {
			'url'             : url,
			'starturl'        : url,
			'netloc'          : url_netloc,
			'distance'        : 0,
			'is_text'         : True,
			'priority'        : db.DB_HIGH_PRIORITY,
			'state'           : "new",
			'addtime'         : datetime.datetime.now(),

			# Don't retrigger unless the ignore time has elaped.
			'ignoreuntiltime' : datetime.datetime.min,
			}

		cursor.execute(cmd, data)
		ret = cursor.fetchall()
		if not ret:
			self.log.warning("Row appears to already be in the new state: %s", url)
		return ret

	def retriggerUrlList(self, urlList):

		sess = self.db.get_db_session()

		raw_cur = sess.connection().connection.cursor()
		commit_each = False

		while 1:
			loopcnt = 0
			try:
				for url in urlList:
					loopcnt += 1
					self.__raw_retrigger_with_cursor(url, raw_cur)
					if commit_each or (loopcnt % 250) == 0:
						self.log.info("Committing!")
						raw_cur.execute("COMMIT;")
				raw_cur.execute("COMMIT;")
				break

			except psycopg2.Error:
				if commit_each is False:
					self.log.warning("psycopg2.Error - Retrying with commit each.")
				else:
					self.log.warning("psycopg2.Error - Retrying.")
					traceback.print_exc()

				raw_cur.execute("ROLLBACK;")
				commit_each = True



	def retriggerUrl(self, url, conditional=None):

		sess = self.db.get_db_session()

		raw_cur = sess.connection().connection.cursor()
		while 1:
			try:
				self.__raw_retrigger_with_cursor(url, raw_cur)
				raw_cur.execute("COMMIT;")
				break

			except psycopg2.Error:
				self.log.warning("psycopg2.Error - Retrying.")
				traceback.print_exc()
				raw_cur.execute("ROLLBACK;")


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=True):

		run = Runner()
		run.go()
