import sys
import multiprocessing
import threading
import time
import traceback
import queue
import random
import datetime
import signal

# import sqlalchemy.exc
# from sqlalchemy.sql import text

import psycopg2
import sys

import settings
import common.LogBase as LogBase
import WebMirror.OutputFilters.AmqpInterface
import runStatus

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



NO_JOB_TIMEOUT_MINUTES = 5


largv = [tmp.lower() for tmp in sys.argv]
if "twoprocess" in largv or "oneprocess" in largv:
	MAX_IN_FLIGHT_JOBS = 10
else:
	# MAX_IN_FLIGHT_JOBS = 75
	# MAX_IN_FLIGHT_JOBS = 250
	MAX_IN_FLIGHT_JOBS = 500
	# MAX_IN_FLIGHT_JOBS = 1000
	# MAX_IN_FLIGHT_JOBS = 3000

def buildjob(
			module,
			call,
			dispatchKey,
			jobid,
			args           = [],
			kwargs         = {},
			additionalData = None,
			postDelay      = 0
		):

	job = {
			'call'         : call,
			'module'       : module,
			'args'         : args,
			'kwargs'       : kwargs,
			'extradat'     : additionalData,
			'jobid'        : jobid,
			'dispatch_key' : dispatchKey,
			'postDelay'    : postDelay,
		}
	return job



class RawJobFetcher(LogBase.LoggerMixin):

	loggerPath = "Main.RawJobFetcher"

	def __init__(self):
		# print("Job __init__()")
		super().__init__()

		self.last_rx = datetime.datetime.now()
		self.active_jobs = 0
		self.jobs_out = 0
		self.jobs_in = 0


		self.db_interface = psycopg2.connect(
				database = settings.DATABASE_DB_NAME,
				user     = settings.DATABASE_USER,
				password = settings.DATABASE_PASS,
				host     = settings.DATABASE_IP,
			)

		# This queue has to be a multiprocessing queue, because it's shared across multiple processes.
		self.normal_out_queue  = multiprocessing.Queue()

		self.j_fetch_proc = threading.Thread(target=self.queue_filler_proc)
		self.j_fetch_proc.start()

		self.print_mod = 0

	def get_queue(self):
		return self.normal_out_queue

	def join_proc(self):
		runStatus.raw_job_run_state.value = 0
		self.j_fetch_proc.join(0)

	def fill_jobs(self):

		while self.normal_out_queue.qsize() < MAX_IN_FLIGHT_JOBS:
			old = self.normal_out_queue.qsize()
			num_new = self._get_task_internal()
			self.log.info("Need to add jobs to the job queue (%s active, %s added)!", self.active_jobs, self.active_jobs-old)

			if runStatus.run_state.value != 1:
				return

			# If there weren't any new items, stop looping because we're not going anywhere.
			if num_new == 0:
				break


	def queue_filler_proc(self):

		try:
			signal.signal(signal.SIGINT, signal.SIG_IGN)
		except ValueError:
			self.log.warning("Cannot configure job fetcher task to ignore SIGINT. May be an issue.")

		self.log.info("Job queue fetcher starting.")

		msg_loop = 0
		while runStatus.raw_job_run_state.value == 1:
			self.fill_jobs()

			msg_loop += 1
			time.sleep(2.5)
			if msg_loop > 20:
				self.log.info("Job queue filler process. Current job queue size: %s (out: %s, in: %s). Runstate: %s", self.active_jobs, self.jobs_out, self.jobs_in, runStatus.raw_job_run_state.value==1)
				msg_loop = 0

		self.log.info("Job queue fetcher saw exit flag. Halting.")
		self.log.info("Job queue filler process. Current job queue size: %s. Runstate: %s", self.active_jobs, runStatus.raw_job_run_state.value==1)
		self.log.info("Job queue fetcher halted.")


	def _get_task_internal(self):

		cursor = self.db_interface.cursor()
		# Hand-tuned query, I couldn't figure out how to
		# get sqlalchemy to emit /exactly/ what I wanted.
		# TINY changes will break the query optimizer, and
		# the 10 ms query will suddenly take 10 seconds!
		raw_query = '''
				UPDATE
				    raw_web_pages
				SET
				    state = 'fetching'
				WHERE
				    raw_web_pages.id IN (
				        SELECT
				            raw_web_pages.id
				        FROM
				            raw_web_pages
				        WHERE
				            raw_web_pages.state = 'new'
				        AND
				            raw_web_pages.priority = (
				               SELECT
				                    min(priority)
				                FROM
				                    raw_web_pages
				                WHERE
				                    state = 'new'::dlstate_enum
				                AND
				                    distance < 1000000
				                AND
				                    raw_web_pages.ignoreuntiltime < now() + '5 minutes'::interval
				            )
				        AND
				            raw_web_pages.distance < 1000000
				        AND
				            raw_web_pages.ignoreuntiltime < now() + '5 minutes'::interval
				        LIMIT {in_flight}
				    )
				AND
				    raw_web_pages.state = 'new'
				RETURNING
				    raw_web_pages.id, raw_web_pages.netloc, raw_web_pages.url;
			'''.format(in_flight=min((MAX_IN_FLIGHT_JOBS, 50)))


		start = time.time()

		while runStatus.run_state.value == 1:
			try:
				cursor.execute(raw_query)
				rids = cursor.fetchall()
				self.db_interface.commit()
				break
			except psycopg2.Error:
				delay = random.random() / 3
				# traceback.print_exc()
				self.log.warn("Error getting job (psycopg2.Error)! Delaying %s.", delay)
				time.sleep(delay)
				self.db_interface.rollback()

		if runStatus.run_state.value != 1:
			return 0

		if not rids:
			return 0

		rids = list(rids)
		# If we broke because a user-interrupt, we may not have a
		# valid rids at this point.
		if runStatus.run_state.value != 1:
			return 0

		xqtim = time.time() - start

		if len(rids) == 0:
			self.log.warning("No jobs available! Sleeping for 5 seconds waiting for new jobs to become available!")
			for dummy_x in range(5):
				if runStatus.run_state.value == 1:
					time.sleep(1)
			return 0

		if xqtim > 0.5:
			self.log.error("Query execution time: %s ms. Fetched job IDs = %s", xqtim * 1000, len(rids))
		elif xqtim > 0.1:
			self.log.warn("Query execution time: %s ms. Fetched job IDs = %s", xqtim * 1000, len(rids))
		else:
			self.log.info("Query execution time: %s ms. Fetched job IDs = %s", xqtim * 1000, len(rids))

		for rid, netloc, joburl in rids:
			self.normal_out_queue.put(rid)

		cursor.close()

		return len(rids)


def test2():
	import logSetup
	import pprint
	logSetup.initLogging()

	agg = RawJobAggregator()
	outq = agg.get_queues()
	for x in range(20):
		print("Sleeping, ", x)
		time.sleep(1)
		try:
			j = outq.get_nowait()
			print("Received job! %s", len(j))
			with open("jobs.txt", "a") as fp:
				fp.write("\n\n\n")
				fp.write(pprint.pformat(j))
			print(j)
		except queue.Empty:
			pass
	print("Joining on the aggregator")
	agg.join_proc()
	print("Joined.")

if __name__ == "__main__":
	test2()

