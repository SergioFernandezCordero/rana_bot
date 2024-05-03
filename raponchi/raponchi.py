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
import urllib3
import argparse
from opensearch_logger import OpenSearchHandler

from tzlocal import get_localzone
from bing_image_downloader import downloader  # using Bing for more cringe

# Environment
timezone = os.getenv('TIMEZONE', default=get_localzone())  # Timezone
loglevel = os.getenv('LOGLEVEL', default="INFO")  # Default log level

# Frog generation parameters
frogword = os.getenv('FROGWORD', default='rana').replace(" ", "-")  # Keyword to search, defaults to "rana"
path_to_frogs = os.getenv('PATH_TO_FROGS', default="dataset")  # Temporary path where frog images will be stored
frog_number = os.getenv('FROG_NUMBER', default=5)  # Number of frog images downloaded in each batch
frog_scheduler_interval = os.getenv('FROG_SCHEDULER_INTERVAL', default=30)  # How frequently the scheduler will run
frog_names_url = os.getenv(
    'FROG_NAMES_URL',
    default="https://raw.githubusercontent.com/olea/lemarios/master/nombres-propios-es.txt"
    )  # Online source for frogs names

# Twitter publication parameters
tw_consumer_key = os.getenv('TW_CONSUMER_KEY')  # Twitter Consumer Key
tw_consumer_secret = os.getenv('TW_CONSUMER_SECRET')  # Twitter Consumer Secret
tw_access_token = os.getenv('TW_ACCESS_TOKEN')  # Twitter Access Token
tw_access_token_secret = os.getenv('TW_ACCESS_TOKEN_SECRET')  # Twitter Access Token Secret

# ElasticSearch logging parameters
# Assumes TLS is enabled and credentials needed, but can disable TLS verification for development purposes.
elk_url = os.getenv('ELK_URL')  # ELK URL for logging
elk_port = os.getenv('ELK_PORT')  # ELK Port
elk_user = os.getenv('ELK_USER')  # ELK User
elk_pass = os.getenv('ELK_PASS')  # ELK Password
elk_flush_freq = os.getenv('ELK_FLUSH_FREQ', default=2)  # Interval between flushes. Defaults to 2 seconds.
elk_tls_verify = os.getenv('ELK_TLS_VERIFY', default="True")  # Allows disabling TLS verification for ELK. Default to True
elk_index = os.getenv('ELK_INDEX', default="raponchi-log")  # ELK Index where logs will be logged

# Input parameters
parser = argparse.ArgumentParser(description='Post futile and absurd info about frogs in Twitter')
parser.add_argument("--now",
                    action='store_true',
                    help='Runs all scheduled jobs now, without waiting to its execution time')
args = parser.parse_args()
run_now = args.now

# Disable TLS exceptions, will warn manually later
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ## Initialize logging
logger = logging.getLogger('raponchi')
logger.setLevel(loglevel)

# # Create Handlers
# Create formatter for console handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Add Console Handler
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)
consoleHandler.setFormatter(formatter)
consoleHandler.setLevel(loglevel)
# Add ElasticSearch Handler if variables defined
if elk_url and elk_port:
    elk_host = "%s:%s" % (elk_url, elk_port)
    elasticHandler = OpenSearchHandler(
        index_name=elk_index,
        hosts=[elk_host],
        http_auth=(elk_user, elk_pass),
        http_compress=True,
        index_rotate="WEEKLY",
        use_ssl=True,
        verify_certs=eval(elk_tls_verify),
        ssl_assert_hostname=eval(elk_tls_verify),
        ssl_show_warn=False
    )
    logger.addHandler(elasticHandler)
    elasticHandler.setLevel(loglevel)
    logger.info("Logging to ElasticSearch enabled - URL: %s, User: %s" % (elk_host, elk_user))
    if eval(elk_tls_verify) is False:
        logger.warning("ElasticSearch TLS Verification disabled. Please note this is insecure.")

# Inform loglevel in all handlers
logger.info("Loglevel is %s", loglevel)


# Components functions


def frog_imager(keywords, operation_id):
    # Frog Imager scrapes Bing in search of a list of frog images, 
    # and download it in a temporal, ephemeral directory.
    logger.info(operation_id + " - Time to go for some Frogs images")
    try:
        print("################### BEGIN BING SEARCH OUTPUT ###################")
        downloader.download(
            keywords,
            limit=int(frog_number),
            filter='photo',
            output_dir=path_to_frogs,
            adult_filter_off=False,
            force_replace=False,  # Setting to true breaks the code due to stupid bug in original code 
            # I don't want to patch on deployment. See frog_cleaner function
            timeout=5,
            verbose=False
        )
        print("################### END BING SEARCH OUTPUT ###################")
    except Exception as e:
        logging.exception("%s - Got exception recovering images from Bing: %s" % (operation_id, e))
    logger.info("%s - Creating a list of frog images files." % operation_id)
    frog_images_list = glob.glob(path_to_frogs + "/" + keywords + "/*", recursive=True)
    return frog_images_list


def frog_namer(frog_names_url, operation_id):
    # Frog Namer compose a random name based on lists
    # Get name list from URL
    logger.info(operation_id + " - Let's retrieve Frog Names from Internet.")
    path_to_frog_names = os.path.join(path_to_frogs, "names")
    path_to_frog_names_file = os.path.join(path_to_frog_names, "names")
    path_to_frog_names_mode = 0o755
    try:
        if os.path.exists(path_to_frogs) and os.path.isdir(path_to_frogs):
            os.mkdir(path_to_frog_names, path_to_frog_names_mode)
        urllib.request.urlretrieve(frog_names_url, path_to_frog_names_file)
    except Exception as e:
        logging.exception("%s - Got exception on main handler: %s" % (operation_id, e))
    # Create a list with it and return it
    logger.info("%s - Generating names list and selecting two random ones." % operation_id)
    frog_names_list = open(path_to_frog_names_file).readlines()
    return frog_names_list


def frog_creator(frog_images_list, frog_names_list, operation_id):
    # Will use the list of photos and the list of names to generate a random, almost unique identity for our frog
    logger.info("%s - Get random photo for our frog" % operation_id)
    # Randomly select one image from downloaded ones
    global frog_photo
    frog_photo = random.choice(frog_images_list).rstrip()
    # Randomly select two names
    logger.info("%s - Get two random names from the list and generate a new name for our frog" % operation_id)
    frog_name = random.choice(frog_names_list).rstrip()
    frog_surname = random.choice(frog_names_list).rstrip()
    # Return a concatenation of both names, separated by a space
    global frog_full_name
    frog_full_name = frog_name + " " + frog_surname
    logger.info(operation_id + " - Photo: " + frog_photo + ", Name: " + frog_full_name)
    # Return photo and name
    return frog_full_name, frog_photo


def frog_poster(operation_id, frog_full_name, frog_photo):
    # Frog Poster is the task that connects to Twitter and posts de tweet
    # using the content generated before.
    try:
        # This seems a little messy due to limitations on API endpoint when using a "Free" project.
        # These limitations force us to use bot V1 and V2 endpoints.

        # Using Twitter API v2
        logger.info("%s - Authenticating to Twitter" % operation_id)
        # Auth for V1, for upload media
        auth = tweepy.OAuth1UserHandler(
            consumer_key=tw_consumer_key,
            consumer_secret=tw_consumer_secret,
            access_token=tw_access_token,
            access_token_secret=tw_access_token_secret
        )
        # Auth for V2, for posting
        client = tweepy.Client(
            consumer_key=tw_consumer_key,
            consumer_secret=tw_consumer_secret,
            access_token=tw_access_token,
            access_token_secret=tw_access_token_secret
        )
        # Upload random selected image
        api = tweepy.API(auth)
        logger.info("%s - Uploading image and posting tweet" % operation_id)
        media = api.media_upload(filename=frog_photo)
        logger.info("%s - Posting tweet" % operation_id)
        tweet = client.create_tweet(text=frog_full_name, media_ids=[media.media_id_string])
        print(tweet)
    except Exception as e:
        logging.exception("%s - Got exception posting to Twitter: %s" % (operation_id, e))


# Auxiliary functions


def frog_cleaner(path_to_frogs, operation_id):
    # Frog Cleaner is an auxiliary function which cleanups the images downloaded by Frog Imager
    # I do this because I'm to lazy to patch others code, specially when it looks abandoned.
    logger.info("%s - Will try cleanup path_to_frogs folder and its contents" % operation_id)
    logger.info("%s - Cleanup %s" % (operation_id, path_to_frogs))
    if os.path.exists(path_to_frogs) and os.path.isdir(path_to_frogs):
        try:
            shutil.rmtree(path_to_frogs)
            logger.info("%s - Directory %s is deleted" % (operation_id, path_to_frogs))
        except OSError as x:
            logger.error("%s - Error occurred: %s : %s" % (operation_id, path_to_frogs, x.strerror))
    else:
        logger.warning("%s - Directory %s doesn't exists or is not a directory" % (operation_id, path_to_frogs))


# Job Scheduler


def frog_scheduler():
    # Frog Scheduler is, as its name says, the job schedule for tasks
    logger.info("SCHEDULER - Initializing Frog Schedulers")
    try:
        # Tell the frog when to appear!
        schedule.every().day.at("08:00").do(frog_generator)
        all_jobs = schedule.get_jobs()
        logger.info("SCHEDULER - The current Frogs Schedulers have been correctly initialized:")
        for i in all_jobs:
            logger.info("+ " + str(i))
    except Exception as e:
        logger.error("SCHEDULER - An error initializing schedules happened. Clearing scheduler and exiting...: %s" % e)
        schedule.clear()
        exit(1)

    while True:
        scheduled_jobs = schedule.idle_seconds()
        logger.info("SCHEDULER - Next job set to run on %s seconds." % str(round(scheduled_jobs)))
        # If --run is set, run all scheduled jobs on start, without waiting of its schedule. Useful for development.
        if run_now:
            schedule.run_all(delay_seconds=5)
        else:
            schedule.run_pending()
        time.sleep(int(frog_scheduler_interval))


def frog_generator():
    operation_id = "uuid: %s" % str(uuid.uuid4())
    logger.info("%s - Standard Frog Generator Job started for keyword: %s" % (operation_id, frogword))
    frog_cleaner(path_to_frogs, operation_id)
    frog_creator(frog_imager(frogword, operation_id), frog_namer(frog_names_url, operation_id), operation_id)
    frog_poster(operation_id, frog_full_name, frog_photo)
    frog_cleaner(path_to_frogs, operation_id)
    logger.info("%s - Standard Frog Generator finished." % operation_id)


if __name__ == '__main__':
    os.environ['TZ'] = str(timezone)
    logger.info("RAPONCHI starting on timezone %s. Please note all dates in logs will appear in this timezone." % (
        str(timezone))
                )
    frog_scheduler()
