import os
import cv2
import shutil
import time as t
import pandas as pd
import urllib.request
from PIL import Image
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC   

ch_path = os.path.join(os.getcwd(), 'chromedriver.exe')
dwn_path = os.path.join(os.getcwd(), 'temp')
images_path = os.path.join(os.getcwd(), 'images')
compressed_path = os.path.join(os.getcwd(), 'compressed')

def get_images(link, type='order'):
  clear_old()
  if type=='order':
    scrap_images(link)
  elif type=='photos':
    scrap_non_o2_images(link)
  save_images()

def crop_and_compress(image, dim):
  base = os.path.basename(image)
  __, ext = os.path.splitext(base)

  if ext != '':
    crop_image(image, dim)
    compress_image(image)

def initiate_driver():
  chromeOptions = webdriver.ChromeOptions()

  prefs = {"download.default_directory" : dwn_path}
  chromeOptions.add_experimental_option("prefs",prefs)

  driver = webdriver.Chrome(executable_path=ch_path, options=chromeOptions)
  wait = WebDriverWait(driver, 60)

  return driver, wait

def scrap_images(link):
  if not (link.endswith('order')):
    link = link + '/order'

  driver, wait = initiate_driver()

  driver.maximize_window()
  driver.get(link)

  div_selector = r"div.sc-1s0saks-4.gkwyfN"
  img_selector = r"img.s1isp7-4.bBALuk"

  divs = driver.find_elements_by_css_selector(div_selector)
  
  imgs = []

  print(f"Found {len(divs)} images")
  print('Getting image src...')
  for div in tqdm(divs):
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
      x2 = x2.replace(":", " ")
      x2 = x2.replace(".", " ")

      f.write(f"{x2},{x}\n")

  driver.quit()

def save_images():
  print('Saving images in folder...')
  file = pd.read_csv('sample.csv', header=None)

  file.columns = ['Name', 'link']

  names = file['Name'].tolist()
  links = file['link'].tolist()

  if 'Gallery Image' in names:
    for index, link in enumerate(tqdm(links)):
      link = link.split('?')[0]
      base = os.path.basename(link)
      __, ext = os.path.splitext(base)
      
      urllib.request.urlretrieve(link, images_path + f"//{index}.{ext}")
  else:
    for index, link in enumerate(tqdm(links)):
      link = link.split('?')[0]
      base = os.path.basename(link)
      __, ext = os.path.splitext(base)

      urllib.request.urlretrieve(link, images_path + f"//{names[index]}.{ext}")

def crop_image(image_path, dim):
  image = Image.open(image_path)
  
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

  return None

def clear_old():
    print("Clearing old...")
    for l in tqdm(os.listdir(os.getcwd())):
      __, ext = os.path.splitext(os.path.join(os.getcwd(), f"{l}"))

      if ext=='':
        if  'images' in __:
          path = os.path.join(os.getcwd(), f"{l}")
          try:
            shutil.rmtree(path)
            os.mkdir(path)
          except Exception as e:
            print(e)
        elif 'compressed' in __:
          path = os.path.join(os.getcwd(), f"{l}")
          try:
            shutil.rmtree(path)
            os.mkdir(path)
          except Exception as e:
            print(e)
      elif 'sample' in __:
        path = os.path.join(os.getcwd(), f"{l}")
        try:
          os.remove(path)
        except:
          pass
      else:
        path = os.path.join(os.getcwd(), "images")
        try:
          os.mkdir(path)
        except:
          pass

def compress_image(image_path, quality=85):
  f_name = os.path.basename(image_path)
  f, _ = os.path.splitext(f_name)

  image = cv2.imread(image_path)
  
  cv2.imwrite(compressed_path + f"//{f}.jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])

def scrap_non_o2_images(link):
  if not (link.endswith('photos')):
    link = link + '/photos'

  driver, wait = initiate_driver()

  driver.maximize_window()
  driver.get(link)

  col1 = r"div.bke1zw-1.fJrjep"
  col2 = r"div.bke1zw-1.fKUTeK"
  col3 = r"div.bke1zw-1.dCXEom"
  col4 = r"div.bke1zw-1.dmqZyt"
  col5 = r"div.bke1zw-1.hJASMb"

  col = [col1, col2, col3, col4, col5]
  img_selector = r"img.s1isp7-4.bBALuk"

  for c in col:
    divs = driver.find_elements_by_css_selector(c)
  
    imgs = []

    print(f"Found {len(divs)} images")
    print('Getting image src...')
    for div in tqdm(divs):
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
        x2 = x2.replace(":", " ")
        x2 = x2.replace(".", " ")

        f.write(f"{x2},{x}\n")

  driver.quit()

'''
def get_menu(link):
  if not (link.endswith('order')):
    link = link + '/order'
  driver, wait = initiate_driver()
  driver.maximize_window()
  driver.get(link)

  section_selector = r"section.sc-eSpQde.fteiyl"
  main_cat_selector = r"h4.sc-1hp8d8a-0.sc-lhLRcH.bLjQUr"
  add_item_selector = r"div.sc-1usozeh-8.kTTqJP"
  price_selector = r"span.sc-17hyc2s-1.fnhnBd"
  menu_item_div_selector = r"div.sc-1s0saks-15.kMdWKd"

  category_names = []

  sections = driver.find_elements_by_css_selector(section_selector)

  for section in sections:
    cat_name = section.find_elements_by_css_selector(main_cat_selector).text

    if 'Recommended' not in cat_name:
      category_names.append(cat_name)
      menu_item_divs = section.find_elements_by_css_selector(menu_item_div_selector)

      for menu_item_div in menu_item_divs:
        item_name = menu_item_div.find_element_by_css_selector(r"h4.sc-1s0saks-13.btodhQ").text
        item_price = menu_item_div.find_element_by_css_selector(r"span.sc-17hyc2s-1.fnhnBd").text
        item_price = item_price.replace("₹", '')
        item_description = ''

        try:
          item_description_more = menu_item_div.find_element_by_css_selector(r"span.sc-1s0saks-5.nsDCA")
          action_chain = ActionChains(driver)
          action_chain.move_to_element(item_description_more).perform()
          item_description_more.click()
          item_description = menu_item_div.find_element_by_css_selector(r"p.sc-1s0saks-10.bQpbVj").text
        except:
          item_description_more = None

        if item_description_more == None:
          item_description = menu_item_div.find_element_by_css_selector(r"p.sc-1s0saks-10.bQpbVj").text

        #CUSTOMIZATIONS
        try:
          customization = menu_item_div.find_element_by_css_selector(r"span.sc-1usozeh-1.frTalr")
        except:
          customization = None

        if customization == None:
          pass
        else:
          btn = menu_item_div.find_element_by_css_selector(r"div.sc-1usozeh-8.kTTqJP")
          btn.click()

          customization_sections = driver.find_elements_by_css_selector(r"div.sc-gCwZxT.AHgAM")

          for customization_section in customization_sections:
            optional_stuff = r"sc-ijnzTp hkXfuN"
            non_optional_choice = r"sc-kWHCRG lnwdhJ"

            non_optional_choice_label = r"djusq7-0 TNqbv"
            optional_label = r"sc-1hez2tp-0 sc-AUpyg aMoHV"



    else:
      pass
'''