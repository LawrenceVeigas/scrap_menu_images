import re
import os
import cv2
import glob
import shutil
from random import randrange
import time as t
import pandas as pd
import urllib.request
from PIL import Image
from tqdm import tqdm
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ch_path = os.path.join(os.getcwd(), 'chromedriver.exe')
dwn_path = os.path.join(os.getcwd(), 'temp')
images_path = os.path.join(os.getcwd(), 'images')

def clean_link(link):
  if link.endswith('/'):
    link = link[:-1]
  
  link = link.replace('/order', '')
  link = link.replace('/photos', '')

  return link

def log_status(link, status, rest_id=None):
  with open('status.csv', 'a+') as f:
    link = clean_link(link)
    f.write(f"{rest_id},{link},{status}\n")

def get_images(link, rest_id=None):
  link = clean_link(link)
  error = scrap_images(link, rest_id)
  if 'error' in error:
    pass
  else:
    save_images(link)
  try:
    os.remove(os.path.join(os.getcwd(), 'sample.csv'))
  except:
    pass

def crop_and_compress(image, dim=(560,420)):
  base = os.path.basename(image)
  __, ext = os.path.splitext(base)

  if ext != '':
    crop_image(image, dim)
    compress_image(image)
  elif ext == '':
    folder = glob.glob(image + '//*')
    
    for file in folder:
      base = os.path.basename(file)
      __, ext = os.path.splitext(base)

      if ext!='':
        crop_image(file, dim)
        compress_image(file)

def initiate_driver():
  chromeOptions = webdriver.ChromeOptions()

  prefs = {"download.default_directory" : dwn_path}
  chromeOptions.add_experimental_option("prefs",prefs)
  driver = webdriver.Chrome(executable_path=ch_path, options=chromeOptions)
  wait = WebDriverWait(driver, 60)

  return driver, wait

def scrap_images(link, rest_id=None):
  base = os.path.basename(link)
  check_path = os.path.join(os.getcwd(), f"images//{base}")

  if os.path.exists(check_path):
    return 'error'

  if not (link.endswith('order')):
    link = link + '/order'
  
  driver, wait = initiate_driver()

  driver.maximize_window()
  driver.get(link)

  check_404 = driver.title
  if '404' in check_404:
    log_status(link, '404', rest_id)

    driver.quit()
    return 'error'

  div_selector = r"div.sc-1s0saks-4.gkwyfN"
  img_selector = r"img.s1isp7-4.bBALuk"

  divs = driver.find_elements_by_css_selector(div_selector)
  
  if len(divs)==0:
    link = link.replace('/order', '')
    log_status(link, 'No images on O2', rest_id)
    driver.quit()
    #status = scrap_non_o2_images(driver, wait, link)
    return 'error'

  imgs = []

  print(f"Found {len(divs)} images")
  print('Getting image src...')
  for div in tqdm(divs):
    action = ActionChains(driver)
    action.move_to_element(div).perform()
    t.sleep(0.01)
    
    element = div.find_elements_by_css_selector(img_selector)
    max = 0
    while (element == None) | (element == []) | (len(element)==0):
      max = max + 1
      t.sleep(1)
      element = div.find_elements_by_css_selector(img_selector)
      if max==10:
        break

    imgs.extend(element)

  with open('sample.csv', 'a+') as f:
    for img in imgs:
      x = img.get_attribute('src')
      x2 = img.get_attribute('alt')
      x2 = re.sub(r'[^a-zA-Z0-9\s]',r'',x2)

      f.write(f"{x2},{x}\n")

  log_status(link, 'Success', rest_id)
  driver.quit()
  return 'Success'

def save_images(link):
  base = os.path.basename(link)
  images_path = os.path.join(os.getcwd(), f"images//{base}")

  try:
    os.mkdir(images_path)
  except Exception as e:
    print(e)
    return None
  
  try:
    file = pd.read_csv('sample.csv', header=None, encoding='utf-8')
  except:
    file = pd.read_csv('sample.csv', header=None, encoding='cp1252')

  file.columns = ['Name', 'link']

  names = file['Name'].tolist()
  links = file['link'].tolist()

  if 'Gallery Image' in names:
    for index, link in enumerate(tqdm(links)):
      link = link.split('?')[0]
      base = os.path.basename(link)
      __, ext = os.path.splitext(base)
      
      try:
        urllib.request.urlretrieve(link, images_path + f"//{index}{ext}")
      except Exception as e:
        print(e)
  else:
    for index, link in enumerate(tqdm(links)):
      link = link.split('?')[0]
      base = os.path.basename(link)
      __, ext = os.path.splitext(base)

      try:
        new_name = re.sub(r'[^a-zA-Z0-9\s]',r'',names[index])
        urllib.request.urlretrieve(link, images_path + f"//{new_name}{ext}")
      except Exception as e:
        print(e)


  files = glob.glob(images_path + '//*')
  print('Cropping and compressing...')
  for file in tqdm(files):
    crop_and_compress(file)

def crop_image(image_path, dim):
  image = Image.open(image_path)
  width, height = image.size

  if (width==dim[0] and height==dim[1]):
      pass
  else:
    aspect_ratio = dim[0]/dim[1]
    width, height = image.size
    image_aspect_ratio = width/height
    new_width = width
    new_height = height

    if (image_aspect_ratio > aspect_ratio):
      new_width = height * aspect_ratio
    elif (image_aspect_ratio < aspect_ratio):
      new_height = width / aspect_ratio
    else:
      if (width==dim[0] and height==dim[1]):
        return None
      else:
        new_image = image.resize(dim, Image.ANTIALIAS)
        new_image.save(image_path)
      return None

    left = (width - new_width)/2
    top = (height - new_height)/2
    right = (width + new_width)/2
    bottom = (height + new_height)/2

    new_image = image.crop((left, top, right, bottom))
    width, height = new_image.size

    if (width==dim[0] and height==dim[1]):
      return None
    else:
      new_image = new_image.resize(dim, Image.ANTIALIAS)
      new_image.save(image_path)

def clear_old():  
  sample = os.path.join(os.getcwd(), 'sample.csv')
  status = os.path.join(os.getcwd(), 'status.csv')
  
  li = [sample, status]

  for l in li:
    try:
      os.remove(l)
    except Exception as e:
      print(e)


def compress_image(image_path, quality=85):
  if (os.path.getsize(image_path)/1000)>99:
    f_name = os.path.basename(image_path)
    f, _ = os.path.splitext(f_name)
    path = image_path.replace(f_name, '')
    image = cv2.imread(image_path)
    os.remove(image_path)
    cv2.imwrite(path + f"//{f}.jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])

def scrap_non_o2_images(driver, wait, link):
  if not (link.endswith('photos')):
    link = link + '/photos'

  driver.get(link)
  try:
    food = driver.find_element_by_xpath(r"//span[contains(text(), 'Food (')]")
    food.click()
  except NoSuchElementException as e:
    log_status(link, 'Error')
    driver.quit()
    return 'error'
  except:
    cookies = driver.find_element_by_css_selector(r"i.rbbb40-1.fRCvfo")
    cookies.click()
    food = driver.find_element_by_xpath(r"//span[contains(text(), 'Food (')]")
    food.click()
    t.sleep(3)

  col1 = r"div.bke1zw-1.fJrjep"
  col2 = r"div.bke1zw-1.fKUTeK"
  col3 = r"div.bke1zw-1.dCXEom"
  col4 = r"div.bke1zw-1.dmqZyt"
  col5 = r"div.bke1zw-1.hJASMb"

  col = [col1, col2, col3, col4, col5]
  img_selector = r"img.s1isp7-4.bBALuk"

  print('Getting image src...')
  for c in tqdm(col):
    divs = driver.find_elements_by_css_selector(c)
    imgs = []
    for div in (divs):
      action = ActionChains(driver)
      action.move_to_element(div).perform()
      t.sleep(0.01)
      
      element = div.find_elements_by_css_selector(img_selector)

      while (element == None) | (element == []) | (len(element)==0):
        t.sleep(1)
        element = div.find_elements_by_css_selector(img_selector)

      imgs.extend(element)

    with open('sample.csv', 'a+') as f:
      for img in imgs:
        x = img.get_attribute('src')
        x2 = img.get_attribute('alt')
        x2 = re.sub(r'[^a-zA-Z0-9\s]',r'',x2)

        f.write(f"{x2},{x}\n")

  driver.quit()
  log_status(link, 'Success')
  return 'Success'