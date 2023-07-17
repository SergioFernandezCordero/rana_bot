#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
"""
Raponchi - Just stupid, fake and absolutely futile information about frogs - by ElAutoestopista
Raponchi will post a random image of a frog with a silly in an (still) undetermined social network
based on the schedule you propose.
"""

import logging
import os
import shutil
import schedule
import time
import uuid
from bing_image_downloader import downloader #using Bing for more cringe

# Environment
loglevel = os.getenv('LOGLEVEL', default="INFO") # Log level
path_to_frogs = os.getenv('PATH_TO_FROGS', default="dataset") # Path where frog images will be stored 
frog_number = os.getenv('FROG_NUMBER', default=5) # Number of frog images downloaded in each batch
frog_scheduler_interval = os.getenv('FROG_SCHEDULER_INTERVAL', default=30) # How frequently the scheduler will look for pending jobs.

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=loglevel)
logger = logging.getLogger(__name__)


# Components

def frog_imager(keywords,operation_id):
    # Frog Imager scrapes Bing in search of a list of frog images, 
    # an download it in a temporal, ephemeral directory.
    logger.info(operation_id+" - Time to go for a RWANA")
    try:
        downloader.download(
            keywords, 
            limit=frog_number,
            filter='photo',
            output_dir=path_to_frogs, 
            adult_filter_off=False, 
            force_replace=False, # Setting to true breaks the code due to stupid bug in original code I don't want to patch on deployment. See frog_cleaner function 
            timeout=5, 
            verbose=False
            )
    except:
            logging.exception(operation_id+" - Got exception on main handler")

def frog_namer():
    # Frog Namer compose a random name based on lists
    print("TODO")

def frog_cleaner(path_to_frogs,operation_id):
    # Frog Cleaner is an auxiliary function which cleanups the images downloaded by Frog Imager
    # I do this because I'm to lazy to patch others code, specially when it looks abandoned.
    logger.info(operation_id+" - Will try cleanup path_to_frogs folder and its content")
    logger.info(operation_id+" - Cleanup "+path_to_frogs)
    if os.path.exists(path_to_frogs) and os.path.isdir(path_to_frogs):
        try:
            shutil.rmtree(path_to_frogs)
            logger.info(operation_id+" - Directory "+path_to_frogs+ " is deleted")
        except OSError as x:
            logger.error(operation_id+" - Error occured: %s : %s" % (path_to_frogs, x.strerror))
    else:
        logger.warning(operation_id+" - Directory "+path_to_frogs+" doesn't exists or is not a directory")


def frog_scheduler():
    # Frog Scheduler is, as its name says, the job schedule for tasks
    logger.info("SCHEDULER - Initializing Frog Schedulers")
    try:
        # Tell the frog when to appear!
        schedule.every().day.at("08:00").do(frog_generator)
        schedule.every(2).minutes.do(frog_generator)
        all_jobs = schedule.get_jobs()
        logger.info("SCHEDULER - The current Frogs Schedulers have been correctly intialized:")
        for i in all_jobs:
            logger.info("+ "+str(i))
    except:
        logger.error("SCHEDULER - An error initializing schedules happened. Clearing scheduler and exiting...")
        schedule.clear()
        exit(1)

    while True:
        scheduled_jobs = schedule.idle_seconds()
        logger.info("SCHEDULER - Next job set to run on "+ str(round(scheduled_jobs)) + " seconds.")
        schedule.run_pending()
        time.sleep(frog_scheduler_interval)


def frog_generator():
    operation_id = "uuid: " +str(uuid.uuid4())
    logger.info(operation_id + " - Standard Frog Generator Job started.")
    frog_imager('rana', operation_id)
    frog_cleaner(path_to_frogs,operation_id)
    logger.info(operation_id + " - Standard Frog Generator finished.")


if __name__ == '__main__':
    logger.info("RAPONCHI starting.")
    frog_scheduler()
