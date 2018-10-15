import json
from datetime import datetime
import os

import boto3
import pandas as pandas

def get_path_from_source_and_time(source,t):

	year = t.strftime("%Y")
	month = t.strftime("%m")
	day = t.strftime("%d")
	time = t.strftime("%H-%M-%S")
	path = os.path.join(source,year,month,day,"{}-{}-{}-{}.csv".format(year,month,day,time))

	return path


def store_data_as_csv(data,source):

	filename = "temp.csv"

	now = datetime.now()
	s3_destination = get_path_from_source_and_time(source,now)

	data.to_csv(r"temp-data/"+filename,sep="|")
	print("saved file as "+filename)

	add_csv_to_s3("temp-data/"+filename,"columbo-scanner-data",s3_destination)
	print("added to s3 as "+s3_destination)

	os.remove("temp-data/"+filename)


def add_csv_to_s3(csv,bucket,blob_destination):

	# access credentials folder
	with open('authorizations/aws-credentials.json') as f:
		cred = json.load(f)

	# access s3 using credentials
	s3 = boto3.resource(
		's3',
		aws_access_key_id=cred["aws_access_key_id"],
		aws_secret_access_key=cred["aws_secret_access_key"]
		)

	# save csv to s3
	s3.Object(bucket, blob_destination).put(Body=open(csv,"rb"))

	# update the user
	print(csv+" added to "+bucket+" bucket on s3 as "+blob_destination)