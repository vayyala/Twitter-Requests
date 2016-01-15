# Vinay Ayyala Twitter Request Example

import Queue
import json
import sys
import oauth2 as oauth
import urllib2 as urllib
import time
import codecs
# pickle is a cool package to serialize python objects. It's really helpful
# 	because we want to store our data in case we get rate limited from twitter
# 	or in case we have an error with one of our requests 
import pickle
from time import gmtime, strftime
import random
from keys import access_token_key, access_token_secret, consumer_key, consumer_secret

oauth_token    = oauth.Token(key=access_token_key, secret=access_token_secret)
oauth_consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)

# example of using TwitterRequest
# this example takes an set of users, finds all the ids of users they follow ("friends") and returns them

# # # # # # # # # # # # # # # # # #
# Arguments:
# # # # input_set: the set of Twitter usernames we want to find the friends of. Can be a set, list, or anything iterable.
# # # # pickle_file: The name of the file that we want to store our data to
# Results:
# # # # dictonary of <username>:[<friend id strings>] pairs
def get_friends(input_set, pickle_file):

	friends = {}
	q = Queue.Queue()

	# we put our input set of users in a queue
	for x in input_set:
		q.put(str(x))

	# For every user in our queue, we want to send a request to twitter, pull their friends, and store them in our dictionary
	while (q.empty() is False):
		s = q.get()
		parameters = []
		cursor1 = '-1'

		print s 
		friends[s] = set()
		while (cursor1 != '0'):
			try:
				# send the request to twitter
				resp = dict(json.loads(TwitterRequest('friends/ids.json?screen_name='+s+'&stringify_ids=true&count=5000&cursor='+cursor1, "GET", parameters, pickle_file, friends)))

				# check for errors
				if ('errors' in resp):
					if ('message' in 'errors'):
						if (resp['errors']['code'] == 88):
							print 'sleeping for 100 seconds'
							time.sleep(100)
						if (resp['errors']['code'] == 34):
							print 'page does not exist'
							cursor1 = '0'
					cursor1 = '0'

				# if no errors, parse our response
				else:
					ids = resp['ids']
					for id_ in ids:
						friends[s].add(id_)
					cursor1 = str(resp['next_cursor'])

			except LookupError:
				cursor1 = '0'
			except (IOError, ValueError):
				time.sleep(10)
	
	# we open up our pickle file and store our data
	file1 = open(pickle_file,"wb")
	pickle.dump(friends, file1)
	file1.close()

	return friends

# send a generic request to twitter and parse response
# Arguments:
# # # # endpoint: the API request you want to make to twitter, check the Twitter Docs
# # # # method: "GET", "POST"
# # # # parameters: []
# # # # pickle_file: where you want "dict_" to be stored in the event of a rate limite
# # # # dict_: file you want stored in the event of a rate limit
# Result:
# # # # jsonified Twitter Response 
def TwitterRequest(endpoint, method, parameters, pickle_file, dict_):

	url = "https://api.twitter.com/1.1/"+endpoint

	signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()

	http_handler  = urllib.HTTPHandler(debuglevel= 0)
	https_handler = urllib.HTTPSHandler(debuglevel= 0)

	req = oauth.Request.from_consumer_and_token(oauth_consumer,
                                             token=oauth_token,
                                             http_method="GET",
                                             http_url=url, 
                                             parameters=parameters)

 	req.sign_request(signature_method_hmac_sha1, oauth_consumer, oauth_token)

	headers = req.to_header()

	encoded_post_data = None
	url = req.to_url()

	opener = urllib.OpenerDirector()
	opener.add_handler(http_handler)
	opener.add_handler(https_handler)

	response = opener.open(url, encoded_post_data)
	if ('x-rate-limit-remaining' not in response.headers):
		print str(response)
		print str(response.headers)
		print url
		return TwttrRequest(endpoint, method, parameters)
	else:
		if (response.headers['x-rate-limit-remaining'] == '0'):
			print 'waiting'
			reset_time = float(response.headers['x-rate-limit-reset'])
			current_time = float(time.time())
			file1 = open(pickle_file, "wb")
			pickle.dump(dict_, file1)
			file1.close()

			if (current_time < reset_time):
				#reset_time is rounded down, so offset by 1.0 second to prevent any rate limit errors
				time_wait = ((reset_time - current_time) + 5.0)
				print time_wait
				print strftime("%Y-%m-%d %H:%M:%S", gmtime())
				time.sleep(time_wait)
			else:
				time.sleep(10)
		print 'success ' + endpoint + '   ' + str(response.headers['x-rate-limit-remaining'])


		a = ''
		for line in response:
			a = a + line
		return a

if __name__ == "__main__":

	# Example
	seed = ['jack', 'biz', 'ev']
	pickle_output = "results.pickle"

	friends = get_friends(seed, pickle_output)


