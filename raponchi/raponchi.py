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
import random
import urllib.request
import glob
import tweepy
from bing_image_downloader import downloader #using Bing for more cringe

# Environment
loglevel = os.getenv('LOGLEVEL', default="INFO") # Log level
path_to_frogs = os.getenv('PATH_TO_FROGS', default="dataset") # Path where frog images will be stored 
frog_number = os.getenv('FROG_NUMBER', default=5) # Number of frog images downloaded in each batch
frog_scheduler_interval = os.getenv('FROG_SCHEDULER_INTERVAL', default=30) # How frequently the scheduler will look for pending jobs.
frog_names_url = os.getenv('FROG_NAMES_URL', default="https://raw.githubusercontent.com/olea/lemarios/master/nombres-propios-es.txt") #Online source for frogs
tw_consumer_key = os.getenv('TW_CONSUMER_KEY')
tw_consumer_secret = os.getenv('TW_CONSUMER_SECRET')
tw_access_token = os.getenv('TW_ACCESS_TOKEN')
tw_access_token_secret = os.getenv('TW_ACCESS_TOKEN_SECRET')


# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=loglevel)
logger = logging.getLogger(__name__)


# Components functions

def frog_imager(keywords,operation_id):
    # Frog Imager scrapes Bing in search of a list of frog images, 
    # an download it in a temporal, ephemeral directory.
    logger.info(operation_id+" - Time to go for some Frogs images")
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
    logger.info(operation_id+" - Creating a list of frog images files.")
    frog_images_list = glob.glob(path_to_frogs+"/"+keywords+"/*", recursive=True)
    return frog_images_list

def frog_namer(frog_names_url, operation_id):
    # Frog Namer compose a random name based on lists
    # Get name list from URL
    logger.info(operation_id+" - Let's retrieve Frog Names from Internet.")
    path_to_frog_names = os.path.join(path_to_frogs, "names")
    path_to_frog_names_file = os.path.join(path_to_frog_names, "names")
    path_to_frog_names_mode = 0o755
    try:
        if os.path.exists(path_to_frogs) and os.path.isdir(path_to_frogs):
            os.mkdir(path_to_frog_names, path_to_frog_names_mode)
        urllib.request.urlretrieve(frog_names_url, path_to_frog_names_file)
    except:
        logging.exception(operation_id+" - Got exception on main handler")
    # Create a list with it and return it
    logger.info(operation_id+" - Generating names list and selecting two random ones.")
    frog_names_list = open(path_to_frog_names_file).readlines()
    return frog_names_list

def frog_creator(frog_images_list, frog_names_list, operation_id):
    # Will use the list of photos and the list of names to generate a random, almost unique identity for our frog
    logger.info(operation_id+" - Get random photo for our frog")
    # Randomly select one image from downloaded ones
    global frog_photo
    frog_photo = random.choice(frog_images_list).rstrip()
    # Randomly select two names
    logger.info(operation_id+" - Get two random names from the list and generate a new name for our frog")
    frog_name = random.choice(frog_names_list).rstrip()
    frog_surname = random.choice(frog_names_list).rstrip()
    # Return a concatenation of both names, separated by a space
    global frog_full_name
    frog_full_name = frog_name + " " + frog_surname
    logger.info(operation_id+" - Photo: " +  frog_photo + ", Name: " + frog_full_name)
    # Return photo and name
    return frog_full_name, frog_photo

def frog_poster(frog_full_name, frog_photo):
    twitter_auth_keys = {
        "consumer_key"        : tw_consumer_key,
        "consumer_secret"     : tw_consumer_secret,
        "access_token"        : tw_access_token,
        "access_token_secret" : tw_access_token_secret
    }

    auth = tweepy.OAuthHandler(
            twitter_auth_keys['consumer_key'],
            twitter_auth_keys['consumer_secret']
            )

    auth.set_access_token(
            twitter_auth_keys['access_token'],
            twitter_auth_keys['access_token_secret']
            )

    api = tweepy.API(auth)
    tweet = "Another day, another #scifi #book and a cup of #coffee"
    status = api.update_status(status=tweet)

# Auxiliary functions

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

# Job Scheduler

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
        schedule.run_all(delay_seconds=10)
        time.sleep(frog_scheduler_interval)


def frog_generator():
    operation_id = "uuid: " +str(uuid.uuid4())
    logger.info(operation_id + " - Standard Frog Generator Job started.")
    frog_cleaner(path_to_frogs,operation_id)
    frog_creator(frog_imager('rana', operation_id), frog_namer(frog_names_url, operation_id), operation_id)
    frog_poster(frog_full_name, frog_photo)
    frog_cleaner(path_to_frogs,operation_id)
    logger.info(operation_id + " - Standard Frog Generator finished.")


if __name__ == '__main__':
    logger.info("RAPONCHI starting.")
    frog_scheduler()
