# Raponchi
Just stupid, fake and absolutely futile information about frogs

To run just setup the following environment variables:

- LOGLEVEL: Log level defaults to INFO
- PATH_TO_FROGS', default="dataset") # Temporary path where frog images will be stored 
- FROG_NUMBER', default=5) # Number of frog images downloaded in each batch
- FROG_SCHEDULER_INTERVAL', default=30) # How frequently the scheduler will look for pending jobs.
- FROG_NAMES_URL', default="https://raw.githubusercontent.com/olea/lemarios/master/nombres-propios-es.txt") # Online source for frogs
- TW_CONSUMER_KEY') # Twitter Consumer Key
- TW_CONSUMER_SECRET') # Twitter Consumer Secret
- TW_ACCESS_TOKEN') # Twitter Access Token
- TW_ACCESS_TOKEN_SECRET') # Twitter Access Token Secret

Install dependencies:

pip install -r requirements

An run:

python raponchi.py

See [tweepy](https://docs.tweepy.org/en/stable/index.html) documentation for further information, you lazy
