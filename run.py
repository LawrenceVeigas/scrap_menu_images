import os
import sys, getopt
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC   
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import time as t
from funcs import scrap_images, save_images, crop_image, images_path, clear_old
import shutil
import glob
from PIL import Image

def main(argv):
  start_time = t.time()
  
  link = ''
  dim = (1000,750)
  
  opts, args = getopt.getopt(argv, "i", longopts=["link=", "dimensions="])

  for opt, arg in opts:
    if opt=="--link":
      link = arg
    elif opt=="--dimensions":
      x = int(arg.split(',')[0])
      y = int(arg.split(',')[1])

      dim=(x,y)

  print(f"Link: {link}\nDimensions: {dim}")

  clear_old()
  scrap_images(link)
  save_images()

  image_files = glob.glob(images_path+'//*')

  print('Cropping images....')
  for image in tqdm(image_files):
    crop_image(image, dim)

  print(f"Script executed in: {start_time - t.time()}")

if __name__ == "__main__":
  main(sys.argv[1:])
