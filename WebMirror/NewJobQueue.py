


import multiprocessing
import time
import traceback
import queue
import random
import signal
import logSetup

import sqlalchemy.exc
import WebMirror.database as db
import WebMirror.LogBase as LogBase
import runStatus
from sqlalchemy.sql import text


if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()


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


class JobAggregator(LogBase.LoggerMixin):

	loggerPath = "Main.JobAggregator"

	def __init__(self, job_queue):
		# print("Job __init__()")
		super().__init__()


		self.db      = db

		self.out_queue = job_queue


		self.j_fetch_proc = multiprocessing.Process(target=self.queue_filler_proc)
		self.j_fetch_proc.start()

	def join_proc(self):
		runStatus.job_run_state.value = 0
		self.j_fetch_proc.join(0)


	def queue_filler_proc(self):

		signal.signal(signal.SIGINT, signal.SIG_IGN)

		self.log.info("Job queue fetcher starting.")

		self.db_sess = self.db.checkout_session()

		while runStatus.job_run_state.value == 1:
			if self.out_queue.qsize() < 200:
				self._get_task_internal()
			else:
				time.sleep(1)

		self.log.info("Job queue fetcher saw exit flag. Halting.")
		self.db.release_session(self.db_sess)

		# Consume the remaining items in the output queue so it shuts down cleanly.
		try:
			while not self.out_queue.empty():
				self.out_queue.get_nowait()
		except queue.Empty:
			pass
		self.log.info("Job queue fetcher halted.")


	def _get_task_internal(self):

		# Hand-tuned query, I couldn't figure out how to
		# get sqlalchemy to emit /exactly/ what I wanted.
		# TINY changes will break the query optimizer, and
		# the 10 ms query will suddenly take 10 seconds!
		raw_query = text('''
				UPDATE
				    web_pages
				SET
				    state = 'fetching'
				WHERE
				    web_pages.id IN (
				        SELECT
				            web_pages.id
				        FROM
				            web_pages
				        WHERE
				            web_pages.state = 'new'
				        AND
				            normal_fetch_mode = true
				        AND
				            web_pages.priority = (
				               SELECT
				                    min(priority)
				                FROM
				                    web_pages
				                WHERE
				                    state = 'new'::dlstate_enum
				                AND
				                    distance < 1000000
				                AND
				                    normal_fetch_mode = true
				                AND
				                    web_pages.ignoreuntiltime < current_timestamp + '5 minutes'::interval
				            )
				        AND
				            web_pages.distance < 1000000
				        AND
				            web_pages.ignoreuntiltime < current_timestamp + '5 minutes'::interval
				        LIMIT 250
				    )
				AND
				    web_pages.state = 'new'
				RETURNING
				    web_pages.id;
			''')


		start = time.time()

		while runStatus.run_state.value == 1:
			try:
				rids = self.db_sess.execute(raw_query)
				self.db_sess.commit()
				break
			except sqlalchemy.exc.OperationalError:
				delay = random.random() / 3
				# traceback.print_exc()
				self.log.warn("Error getting job (OperationalError)! Delaying %s.", delay)
				time.sleep(delay)
				self.db_sess.rollback()
				self.db_sess.flush()
				self.db_sess.expire_all()
			except sqlalchemy.exc.InvalidRequestError:
				traceback.print_exc()
				self.log.warn("Error getting job (InvalidRequestError)!")
				self.db_sess.rollback()
				self.db_sess.flush()
				self.db_sess.expire_all()

		if not rids:
			return

		rids = [tmp[0] for tmp in rids]
		# If we broke because a user-interrupt, we may not have a
		# valid rids at this point.
		if runStatus.run_state.value != 1:
			return False

		xqtim = time.time() - start


		if xqtim > 0.5:
			self.log.error("Query execution time: %s ms. Fetched job IDs = %s", xqtim * 1000, len(rids))
		elif xqtim > 0.1:
			self.log.warn("Query execution time: %s ms. Fetched job IDs = %s", xqtim * 1000, len(rids))
		else:
			self.log.info("Query execution time: %s ms. Fetched job IDs = %s", xqtim * 1000, len(rids))

		for rid in rids:
			self.out_queue.put(rid)


def test2():
	logSetup.initLogging()

	jque = multiprocessing.Queue()
	agg = JobAggregator(jque)

	for x in range(20):
		print("Sleeping, ", x)
		time.sleep(1)
	agg.join_proc()

if __name__ == "__main__":
	test2()

