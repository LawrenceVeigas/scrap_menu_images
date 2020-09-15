from tqdm import tqdm
import os, sys, getopt, shutil, glob
import time as t
#import custom functions
from funcs import get_images, crop_and_compress, images_path

def main(argv):
  start_time = t.time()
  
  link_type = 'order'
  link = ''
  dim = (560,420)
  func = 0

  opts, args = getopt.getopt(argv, "i", longopts=["link=", "dimensions=", "func=", "type="])

  for opt, arg in opts:
    if opt=="--link":
      link = arg
    elif opt=="--dimensions":
      x = int(arg.split('x')[0])
      y = int(arg.split('x')[1])
      dim=(x,y)
    elif opt=="--func":
      #1 is to scrap and save_images
      #2 is to crop, compress and resize
      # default is for both
      func = int(arg)
    elif opt=="--type":
      link_type = arg

  print(f"Link: {link}\nDimensions: {dim}")

  if func==1:  
    get_images(link, link_type)
  elif func==2:
    image_files = glob.glob(images_path+'//*')
    #crop and compress images
    for image in tqdm(image_files):
      crop_and_compress(image, dim)
  else:
    get_images(link, link_type)
    image_files = glob.glob(images_path+'//*')
    #crop and compress images
    for image in tqdm(image_files):
      crop_and_compress(image, dim)

  print(f"Script executed in: {start_time - t.time()}")

if __name__ == "__main__":
  main(sys.argv[1:])
