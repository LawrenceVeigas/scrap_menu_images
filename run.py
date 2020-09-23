from tqdm import tqdm
import os, sys, getopt, shutil, glob
import time as t
import pandas as pd
#import custom functions
from funcs import get_images, crop_and_compress, images_path, clean_link, clear_old
from sheets import upload_files_to_drive, get_file_ids, get_requests

def main(argv):
  start_time = t.time()

  opts, args = getopt.getopt(argv, "gc", longopts=["link=", "input_file="])

  for opt, arg in opts:
    if opt=="--link":
      link = arg
      clear_old()
      get_images(link)

    elif opt=="-c":
      image_files = glob.glob(images_path+'//*')
      #crop and compress images
      for image in tqdm(image_files):
        crop_and_compress(image)
    elif opt=="--input_file":
      #file_name = os.path.join(os.getcwd(), arg)
      file_name = arg
      
      file = pd.read_csv(file_name, header=None)
      rest_ids = file.iloc[:,0].tolist()
      links = file.iloc[:,1].tolist()
      
      clear_old()
      for rest_id, link in zip(rest_ids, links):
        get_images(link, rest_id)

      print("Uploading files to drive...")
      upload_files_to_drive(file)

    elif opt=='-g':
      image_request, resize_request = get_requests()

      #handle image_request
      clear_old()
      rest_ids = image_request.iloc[:,0].tolist()
      links = image_request.iloc[:,1].tolist()

      print(rest_ids, links)

  print(f"Script executed in: {start_time - t.time()}")

if __name__ == "__main__":
  main(sys.argv[1:])
