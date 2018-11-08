import boto3
import pandas as pd
import json

def get_credentialed_s3_resource():

	# access credentials folder
	with open('authorizations/aws-credentials.json') as f:
		cred = json.load(f)

	# access s3 using credentials
	s3 = boto3.resource(
		's3',
		aws_access_key_id=cred["aws_access_key_id"],
		aws_secret_access_key=cred["aws_secret_access_key"]
		)

	return s3

def get_list_of_s3_object_keys():

	# access credentials folder
	with open('authorizations/aws-credentials.json') as f:
		cred = json.load(f)

	# access s3 using credentials
	s3 = boto3.resource(
		's3',
		aws_access_key_id=cred["aws_access_key_id"],
		aws_secret_access_key=cred["aws_secret_access_key"]
		)

	keys = [blob.key for blob in s3.Bucket('columbo-scanner-data').objects.all()]

	return keys


def get_scanner_data_as_dataframe(state=None,county=None):

	# access credentials folder
	with open('authorizations/aws-credentials.json') as f:
		cred = json.load(f)

	# access s3 using credentials
	s3 = boto3.resource(
		's3',
		aws_access_key_id=cred["aws_access_key_id"],
		aws_secret_access_key=cred["aws_secret_access_key"]
		)

	keys = get_list_of_s3_object_keys()

	if state and county:
		keys = [k for k in keys if k.split('/')[:2] == [state.title(),county.title()]]
		print("looking for {} data in {}".format(state,county))

	elif state:
		keys = [k for k in keys if k.split('/')[0] == state.title()]
		print("looking for {} dataframes".format(state))

	d = pd.DataFrame()

	for k in keys:
		try:
			temp = pd.read_csv(s3.Object('columbo-scanner-data',k).get()['Body'],sep="|",encoding="latin1")
			if len(k.split('/'))==6:
				temp['state'] = k.split('/')[0]
				temp['county'] = k.split('/')[1]
			print("successfully downloaded {}".format(k))
			d = d.append(temp, ignore_index=True)
		except Exception as e:
			print("could not load {}".format(k))
			print(e)

	return d


