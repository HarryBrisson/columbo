import time
import json
from datetime import datetime, timedelta
from urllib.request import urlopen
import subprocess
import random

import boto3
import numpy as np
import scipy.io.wavfile
import requests
from bs4 import BeautifulSoup
import speech_recognition as sr
import pandas as pd

from s3_uploads import *
from update_reference_data import *


def get_aws_credentials():
	with open("authorizations/aws-credentials.json") as f:
		cred = json.loads(f.read())
	return cred


def capture_livestream(filepath, streamurl, duration):
	print("listening to {}".format(streamurl))
	stream = urlopen(streamurl)
	fd = open(filepath, 'wb')
	begin = datetime.now()
	duration = timedelta(milliseconds=duration*1000)
	while datetime.now() - begin < duration:
		data = stream.read(1000)
		fd.write(data)
	fd.close()


# county id is a 3 digit number -- SF is 220, LA is 201, etc.
def get_all_live_webplayer_urls_for_county_id(ctid):
	
	# initialize dict
	webplayer_urls = {}
	
	url = "https://www.broadcastify.com/listen/ctid/{}".format(ctid)
	r = requests.get(url)
	soup = BeautifulSoup(r.text,'html.parser')

	rows = soup.find("table",{'class','btable'}).find_all('tr')
	
	for row in rows:
		cells = row.find_all('td')

		try:

			feed_name = cells[1].find("a").getText().replace("\n","  ").replace(",","").replace("|"," ")

			dispatch_check = "dispatch" in feed_name.lower()
			pd_check = "pd" in feed_name.lower()
			police_check = "police" in feed_name.lower()
			sheriff_check = "sheriff" in feed_name.lower()
			patrol_check = "patrol" in feed_name.lower()
			law_check = "law" in feed_name.lower()
			keyword_check = dispatch_check or pd_check or police_check or sheriff_check or patrol_check or law_check

			public_safety_check = "Public Safety" in cells[2].getText()

			if keyword_check and public_safety_check:
				feed_number = cells[0].find('a')['href'].split("/feed/")[1].split("/web")[0]
				webplayer_url = "https://www.broadcastify.com/listen/feed/{}/web".format(feed_number)
				webplayer_urls[feed_name]="https://www.broadcastify.com/listen/feed/{}/web".format(feed_number)

		except:
			pass
	
	print("identified {} urls for {}".format(len(webplayer_urls),ctid))
	return webplayer_urls


def get_livestream_mp3_url(webplayer_url):
	r = requests.get(webplayer_url)
	soup = BeautifulSoup(r.text,'html.parser')
	live_url = soup.find("audio")['src']
	print("live url identified for {}".format(webplayer_url))
	return live_url
	

def get_live_urls_from_ctid(ctid):
	webplayer_urls = get_all_live_webplayer_urls_for_county_id(ctid)
	livestream_mp3_urls = {}
	for feed in webplayer_urls.keys():
		livestream_mp3_urls[feed] = get_livestream_mp3_url(webplayer_urls[feed])
	return livestream_mp3_urls


def collect_and_process_scanner_audio(live_url):
	

	capture_livestream("temp-audio/raw.mp3",live_url,30)
	subprocess.call("ffmpeg -i temp-audio/raw.mp3 temp-audio/raw.wav -y", shell=True)
	
	wav_data = scipy.io.wavfile.read("temp-audio/raw.wav")

	new_wav_data = np.array([])

	total_chunk_count = len(wav_data[1])//11250

	# initialize ucc
	utilized_chunk_count = 0

	for chunk_number in range(total_chunk_count):
		start = chunk_number*11250
		end = (chunk_number+1)*11250
		chunk = wav_data[1][start:end]
		if np.max(chunk) > 1000:
			new_wav_data = np.append(new_wav_data,chunk)
			utilized_chunk_count += 1

	# quiet down the volume        
	new_wav_data = new_wav_data/10000

	scipy.io.wavfile.write("temp-audio/clean.wav",22500,new_wav_data)

	subprocess.call("ffmpeg -i temp-audio/clean.wav temp-audio/clean.flac -y", shell=True)

	r = sr.Recognizer()

	scanner_audio = sr.AudioFile('temp-audio/clean.flac')

	try:
		with scanner_audio as source:
			audio = r.record(source)

		print("processing audio")
		text = r.recognize_google(audio)
		print("google heard: {}".format(text))
	except:
		print("google couldn't understand")
		text = ""
		
	utilization_pct = float(utilized_chunk_count)/float(total_chunk_count)
	print("Utilization Percent: {}".format(utilization_pct))

	data = {
		"text":text,
		"utilization":utilization_pct,
		"length":len(wav_data[1])/22500
	}

	return data


def create_df_of_scanner_data(ctid):
	
	urls = get_live_urls_from_ctid(ctid)
	
	d = pd.DataFrame()
	
	for feed in urls.keys():
		print("trying to add info for {}".format(feed))
		collection_time = datetime.utcnow()

		try:
			data = collect_and_process_scanner_audio(urls[feed])
			print("successfully collected")
			
		except Exception as e:
			data = {}
			print("unable to collect")
			print(e)
			
			
		data['name'] = feed.replace("\n"," ").replace("|"," ").replace(","," ")
		data['url'] = urls[feed]
		data['collection_time'] = collection_time

		print()

		try:
			d = d.append(data,ignore_index=True)
			
		except:
			print("could not append")

		
	return d

def get_ctid_ref():
	with open("reference-data/ctids_by_name.json") as f:
		ctid_ref = json.loads(f.read())
	return ctid_ref


def surf_scanners(state=None,county=None):

	ctid_ref = get_ctid_ref()

	if state and county:
		ctid = ctid_ref[state][county]
		while True:
			data = create_df_of_scanner_data(str(ctid))
			store_data_as_csv(data,state+"--"+county)
			print()
			print()
	else:
		while True:
			for state in ctid_ref.keys():
				for county in ctid_ref[state].keys():
					ctid = ctid_ref[state][county]
					data = create_df_of_scanner_data(str(ctid))
					store_data_as_csv(data,state+"--"+county)   
					

if __name__ == "__main__":
	update_ctid_json_file()
	surf_scanners()  		
