import os
import pygsheets
import glob
import pandas as pd
from funcs import clean_link
from tqdm import tqdm
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

form_responses = r"https://docs.google.com/spreadsheets/d/13y-3yw-RLE2sxF9ozwxm7yKZhh3CGUVXq-eJhRl6klM/edit#gid=602833141"

def get_requests():
  gc = pygsheets.authorize(client_secret=os.path.join(os.getcwd(), 'google_credentials.json'))

  sheet = gc.open_by_url(form_responses)
  master = sheet.worksheet_by_title('Form Responses 1')

  df = master.get_as_df()
  
  image_request = df.loc[(df['Request Type']=='Image Request')&(df['Status']!='Done')]
  resize_request = df.loc[(df['Request Type']=='Bulk Resize Request')&(df['Status']!='Done')]

  image_request = image_request[['DO Rest ID','Please provide zomato link']]
  resize_request = resize_request[['DO Rest ID','Upload images provided by client for bulk resize (If you have more than 10 images - please ZIP it and upload here)']]

  return image_request, resize_request

def upload_files_to_drive(file):
  #main folder id: 1cXw3n8w74nrM79xxvKx9zhlGPYs8xQTo
  
  g_login = GoogleAuth()
  g_login.LocalWebserverAuth()
  drive = GoogleDrive(g_login)

  DO_rest_ids = file.iloc[:,0].tolist()
  zomato_links = file.iloc[:,1].tolist()

  folder_names = []
  for link in zomato_links:
    base = os.path.basename(clean_link(link))
    folder_names.append(base)

  #get folder list in drive
  folder_list = drive.ListFile({'q': "'1cXw3n8w74nrM79xxvKx9zhlGPYs8xQTo' in parents and trashed=false"}).GetList()
  folder_list_titles = [f['title'] for f in folder_list]

  for rest_id, folder in zip(DO_rest_ids, folder_names):
    print(f"Checking Rest ID and uploading: {rest_id}-{folder}")
    if str(rest_id) not in folder_list_titles:
      #print(f"New folder: {rest_id} - {folder}.. uploading..")
      images = glob.glob(os.path.join(os.getcwd(), f"images/{folder}") + '//*')
      if len(images)!=0:
        folder_drive = drive.CreateFile({'title': rest_id, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [{'id': '1cXw3n8w74nrM79xxvKx9zhlGPYs8xQTo'}]})
        folder_drive.Upload()
        folder_id = folder_drive.get('id')
        for image in tqdm(images):
          file_drive = drive.CreateFile({'title':os.path.basename(image), 'parents':[{'id':folder_id}]})
          file_drive.SetContentFile(image)
          file_drive.Upload()
      elif len(images)==0:
        print(f"No images found for {rest_id, folder}")
    elif str(rest_id) in folder_list_titles:
      print(f"{rest_id} already exisits, comparing & uploading files...")
      _id = folder_list[folder_list_titles.index(str(rest_id))]['id']
      file_list = drive.ListFile({'q': f"'{_id}' in parents and trashed=false"}).GetList()
      file_list_titles = [f['title'] for f in file_list]

      images = glob.glob(os.path.join(os.getcwd(), f"images/{folder}") + '//*')
      
      if len(images)!=0:
        images_base = [os.path.basename(i) for i in images]
        for image, image_full_path in tqdm(zip(images_base, images), total=len(images_base)):
          if image not in file_list_titles:
            file_drive = drive.CreateFile({'title': image, 'parents':[{'id':_id}]})
            file_drive.SetContentFile(image_full_path)
            file_drive.Upload()
          elif image in file_list_titles:
            print(f"Skipping - {rest_id}-{folder}/{image}")

def get_file_ids():
  g_login = GoogleAuth()
  g_login.LocalWebserverAuth()
  drive = GoogleDrive(g_login)
  
  file_list = drive.ListFile({'q': "'1cXw3n8w74nrM79xxvKx9zhlGPYs8xQTo' in parents and trashed=false"}).GetList()
  files = {}
  for file in file_list:
    files[file['title']] = r'https://drive.google.com/drive/folders/' + file['id']

  df = pd.DataFrame.from_dict(files, orient='index')
  df.to_csv('uploaded.csv')

if __name__ == '__main__':
  get_file_ids()
  #get_requests()