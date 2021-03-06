if __name__ == '__main__':
	from settings import *
else:
	from . settings import *
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from bs4 import BeautifulSoup
import pandas as pd
import xlsxwriter
import os
import io
import re
import csv
import io
import json
import requests

### Office365 related features ###

class Office365(object):

	def __init__(self, api_version='v1.0'):
		
		if api_version == 'v1.0':
			self.uri = OFFICE_365_GRAPH_API_BASE_URL
		elif api_version == 'beta':
			self.uri = OFFICE_365_GRAPH_API_BETA_BASE_URL
		else:
			print('Version not supported')
			sys.exit(1)
		
		self.scope = 'https://graph.microsoft.com/.default'
		self.headers = ''
		self.access_token = ''
		self.expires_at = ''
		#self.refresh_token = ''
		self.__connect__()
		self.sharepoint_root_id = self.__get_sharepoint_root_id__()
		self.reporting_site_id = self.__get_reporting_id__()

	
	def __send_request__(self, endpoint, params=None, method=None, data=None, headers=None):

		if method == 'GET':
			r = requests.get('{uri}{endpoint}'.format(uri=self.uri, endpoint=endpoint), headers=self.headers, params=params)			
		elif method == 'POST':
			r = requests.post('{uri}{endpoint}'.format(uri=self.uri, endpoint=endpoint), headers=self.write_headers, json=data)			
		elif method == 'PUT':
			r = requests.put('{uri}{endpoint}'.format(uri=self.uri, endpoint=endpoint), headers=self.upload_headers, data=data)			
		elif method == 'PUT_JSON':
			r = requests.put('{uri}{endpoint}'.format(uri=self.uri, endpoint=endpoint), headers=self.write_headers, json=data)			
		elif method == 'PATCH':
			r = requests.patch('{uri}{endpoint}'.format(uri=self.uri, endpoint=endpoint), headers=self.write_headers, json=data)			
		elif method == 'DELETE':
			r = requests.delete('{uri}{endpoint}'.format(uri=self.uri, endpoint=endpoint), headers=self.headers)			
		else:
			return "Unsupported Operation"

		print(r.url)
		#print(r.request.__dict__)
		
		try:
			return r.json()
		except:
			return r

	def get_consent(self):

		"""This is a step used when adding permissions via the Microsoft dashboard - admin consent granted through pasting returned URL in browser"""		
		
		params = {'client_id':OFFICE_365_CLIENT_ID,
			'redirect_uri':OFFICE_365_REDIRECT_URI,
			'state':'12345'}
		
		return self.__send_request__(endpoint=OFFICE_365_GRAPH_API_ADMIN_URI, method='GET', params=params) 
	
	def __connect__(self):
		
		auth = requests.auth.HTTPBasicAuth(OFFICE_365_CLIENT_ID, OFFICE_365_CLIENT_SECRET)
		client = BackendApplicationClient(OFFICE_365_CLIENT_ID)
		oauth = OAuth2Session(client=client)
		token_info = oauth.fetch_token(scope=self.scope, auth=auth, token_url=OFFICE_365_ACCESS_TOKEN_URL, client_id=OFFICE_365_CLIENT_ID, client_secret=OFFICE_365_CLIENT_SECRET)
		self.access_token = token_info['access_token']
		self.expires_at = token_info['expires_at']
		self.headers = {"Authorization": "Bearer {token}".format(token=self.access_token)}
		self.write_headers = {"Content-Type":"application/json", "Authorization": "Bearer {token}".format(token=self.access_token)}
		self.upload_headers = {"Content-Type":"text/plain", "Authorization": "Bearer {token}".format(token=self.access_token)}

	def __get_sharepoint_root_id__(self, params=None):

		endpoint = 'sites/root'
		return self.__send_request__(endpoint=endpoint, method='GET', params=params)['id'] 

	def __get_reporting_id__(self, params=None):

		sites = self.search_sharepoint_sites(params={"search":"reporting"})
		return str([s['id'] for s in sites['value'] if s['name'] == 'reporting_and_analytics'][0])

	def get_drive_for_user(self, user_name='company@office.org', params=None):

		return self.__send_request__(endpoint='users/{user_name}'.format(user_name=user_name), method='GET', params=params) 	

	def get_drives_for_group(self, group_id=None, params=None):

		return self.__send_request__(endpoint='groups/{group_id}/drive/root/children'.format(group_id=group_id), method='GET', params=params) 	
	
	def get_drives_for_site(self, site_id=None, params=None):
		
		return self.__send_request__(endpoint='sites/{site_id}/drives'.format(site_id=site_id), method='GET', params=params) 	

	def get_drive_items(self, drive_id=None, params=None):
		
		return self.__send_request__(endpoint='drives/{drive_id}/root/children'.format(drive_id=drive_id), method='GET', params=params) 	

	def get_drive_items_(self, drive_id=None, sub_folder_path=None, item_id=None, params=None):

		if sub_folder_path:
			endpoint='drives/{drive_id}/root:/{sub_folder_path}:/children'.format(drive_id=drive_id, sub_folder_path=sub_folder_path)
		elif item_id:
			endpoint='drives/{drive_id}/items/{item_id}/children'.format(drive_id=drive_id, item_id=item_id)
		else:
			endpoint='drives/{drive_id}/root/children'.format(drive_id=drive_id) 	
				
		return self.__send_request__(endpoint=endpoint, method='GET', params=params) 	
	def get_drive_items_by_item(self, drive_id=None, item_id=None, params=None):
		
		return self.__send_request__(endpoint='drives/{drive_id}/items/{item_id}/children'.format(drive_id=drive_id, item_id=item_id), method='GET', params=params) 	

	def download_file_from_drive(self, user_id='company@office.org', item_id=None, params=None):

		return self.__send_request__(endpoint='users/{user_id}/drive/items/{item_id}/content'.format(user_id=user_id, item_id=item_id), method='GET', params=params).content 

	def move_file(self, drive_id=None, item_id=None, new_file_name=None, new_parent_folder_id=None):

		item_info = {'parentReference':{'id':new_parent_folder_id}, 'name':new_file_name}
		endpoint = 'drives/{drive_id}/items/{item_id}'.format(drive_id=drive_id, item_id=item_id)
		return self.__send_request__(endpoint=endpoint, method='PATCH', data=item_info) 
		def download_file(self, drive_id=None, user_id=None, item_id=None, sub_folder_path=None, download_location='Sharepoint', params=None):

		if download_location == 'Sharepoint':

			if sub_folder_path:
				endpoint='drives/{drive_id}/root:/{sub_folder_path}:/{item_id}/content'.format(drive_id=drive_id, sub_folder_path=sub_folder_path, item_id=item_id)
			else:
				endpoint='drives/{drive_id}/items/{item_id}/content'.format(drive_id=drive_id, item_id=item_id)
	
		elif download_location == 'OneDrive':
			
			if sub_folder_path:
				endpoint='users/{user_id}/root:/{sub_folder_path}:/{item_id}/content'.format(drive_id=drive_id, file_name=file_name, sub_folder_path=sub_folder_path)		
			else:
				endpoint='users/{user_id}/drive/items/{item_id}/content'.format(user_id=user_id, item_id=item_id, file_name=file_name)
					
		else:
			raise Exception('Not a valid input')
		
		return self.__send_request__(endpoint=endpoint, method='GET', params=params).content 

	def upload_file(self, drive_id=None, file_name=None, file_path=None, user_id=None, item_id=None, sub_folder_path=None, upload_location='Sharepoint', params=None):

		if upload_location == 'Sharepoint':

			if sub_folder_path:
				endpoint='drives/{drive_id}/root:/{sub_folder_path}/{file_name}:/content'.format(drive_id=drive_id, file_name=file_name, sub_folder_path=sub_folder_path)
			elif item_id:
				endpoint='drives/{drive_id}/drive/items/{item_id}:/{file_name}:/content'.format(drive_id=drive_id, file_name=file_name, item_id=item_id)
			else:
				endpoint = 'drives/{drive_id}/root/children/{file_name}/content'.format(drive_id=drive_id, file_name=file_name)
	
		elif upload_location == 'OneDrive':
			
			if sub_folder_path:
				endpoint='users/{user_id}/root:/{sub_folder_path}/{file_name}:/content'.format(drive_id=drive_id, file_name=file_name, sub_folder_path=sub_folder_path)		
			elif item_id:
				endpoint='users/{user_id}/drive/items/{item_id}:/{file_name}:/content'.format(user_id=user_id, item_id=item_id, file_name=file_name)
			else:
				endpoint='users/{user_id}/root/children/{file_name}/content'.format(user_id=user_id, file_name=file_name)
					
		else:
			raise Exception('Not a valid input')

		with open(file_path, 'rb') as file_handle:
			
			file_data = file_handle.read()
			return self.__send_request__(endpoint=endpoint, method='PUT', params=params, data=file_data) 	
	
	def upload_file_to_drive(self, drive_id=None, file_name=None, params=None, file_path=None, sub_folder=None):
		
		with open(file_path, 'rb') as file_handle:
			
			file_data = file_handle.read()
			
			if sub_folder:
				return self.__send_request__(endpoint='drives/{drive_id}/root:/{sub_folder}/{file_name}:/content'.format(drive_id=drive_id, file_name=file_name, sub_folder=sub_folder), 
						method='PUT', params=params, data=file_data) 	
			else:
				return self.__send_request__(endpoint='drives/{drive_id}/root/children/{file_name}/content'.format(drive_id=drive_id, file_name=file_name), method='PUT', params=params, data=file_data) 	
	
	def upload_file_to_onedrive(self, user_id='user@office.com', file_name=None, item_id=None, file_path=None, params=None):
		
		with open(file_path, 'rb') as file_handle:
			
			file_data = file_handle.read()
			return self.__send_request__(endpoint='users/{user_id}/drive/items/{item_id}:/{file_name}:/content'.format(user_id=user_id, item_id=item_id, file_name=file_name), method='PUT', params=params, data=file_data)
