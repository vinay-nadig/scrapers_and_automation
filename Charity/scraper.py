#!/usr/bin/env python

from urllib2 import urlopen
from bs4 import BeautifulSoup
from time import sleep
from random import random
import re, csv, os, sys

BASE_URL = 'http://www.charitynavigator.org/index.cfm?bay=search.alpha&ltr={0}'
INDEX_URL = 'http://www.charitynavigator.org/index.cfm?bay=search.alpha'
CSV_FILE = 'output.csv'
ERROR_FILE = 'errors.txt'
ERROR_MSG = """Area code file not found!
Please copy the area_codes.csv file
to the scraper directory.
Exiting now."""



# Details to get
# 1. Name
# 2. Address
# 3. Telephone
# 4. Fax
# 5. EIN
# 6. Website Link
# 7. Mission


# Construct Area Code dataset
print "Constructing Area Code dataset...\n"
if not os.path.exists("area_codes.csv"):
    print ERROR_MSG
    sys.exit(1)
else:
    area_codes = {}
    fp = open("area_codes.csv", "r")
    reader = csv.reader(fp, delimiter=',', quotechar='"')
    for row in reader:
        area_codes[row[0]] = [row[1], row[2], row[3]]

# Get all the listings to be sent as a parameter to the base url
# and store it in args
html = urlopen(INDEX_URL).read()
soup = BeautifulSoup(html)
maincontent = soup.find("div", {"id" : "maincontent2"})
temp = maincontent.find("p")
temp = temp.findAll("a")
args = [link.text for link in temp]
args_length = len(args)

# Output File
output_fp = open(CSV_FILE, "wb")
# Error File
error_fp = open(ERROR_FILE, "wb")
# CSV Object
csv_writer = csv.writer(output_fp, delimiter=',')
# Write the headings
csv_writer.writerow(['Name', 'Address', 'Telephone No', 'Fax No', 'EIN No', 'Website', 'Mission', 'Size', 'Category', 'City', 'State'])
# Pattern to get telephone number
tel_p = re.compile("tel: \([0-9]{2,4}\) [0-9]{2,4}-[0-9]{2,5}")
# Pattern to get fax number
fax_p = re.compile("fax: \([0-9]{2,4}\) [0-9]{2,4}-[0-9]{2,6}")
# Pattern to get EIN number
ein_p = re.compile("EIN: [0-9]{1,3}-[0-9]{6,8}")
# Pattern for the area code
area_p = re.compile("\([0-9]{3}\)")
# Organization Size list
size_l = ["Lesser than 3.5M", "3.5M to 13.5M", "Greater than 13.5M"]

for letter in args:
    print "In Index {0}".format(letter)
    url = BASE_URL.format(letter)
    html = urlopen(url).read()
    try:
        soup = BeautifulSoup(html)
    except:
        error_fp.write("Could not parse Charities starting with letter {0}".format(letter))
        continue
        
    maincontent = soup.findAll("div", {"id" : "maincontent2"})[0]
    temp = maincontent.findAll("a")
    # Eliminate all index lists
    temp = temp[args_length:]
    for link in temp:
        output_fp.flush()
        os.fsync(output_fp.fileno())
        sleep(round(random(), 2))
        urlz = link.attrs['href']
        htmlz = urlopen(urlz).read()
        try:
            soupz = BeautifulSoup(htmlz)
        except:
            error_fp.write("Could not find details for Charities starting with letter {0}".format(urlz))
            continue
        try:
            name = soupz.find("h1", {"class" : "charityname"}).text
            name = name.encode('ascii', errors='ignore') if name else None
        except:
            error_fp.write("Could not find details for Charities starting with letter {0}".format(urlz))
            continue
        print "Scraping data for {0}".format(name)


        info_obj = soupz.find("div", {"class" : "rating"})
        info_text = info_obj.find("p").text.replace("&nbsp;", "")
        info_text = ' '.join(info_text.split())

        # Category
        category = soupz.findAll("p", {"class" : "crumbs"})
        category = category[0].text if category else None

        # Telephone Number
        tel_no = tel_p.findall(info_text)
        tel_no = tel_no[0] if tel_no else None

        # Std Code
        std_code = area_p.findall(tel_no) if tel_no else None
        std_code = std_code[0] if std_code else None
        std_code = std_code.replace("(", "") if std_code else None
        std_code = std_code.replace(")", "") if std_code else None

        # State and City
        try:
            state = area_codes.get(std_code)[1] if std_code else None
        except TypeError:
            state = None
        try:
            city = area_codes.get(std_code)[0] if std_code else None
        except TypeError:
            state = None

        # Size
        func_exp_text_ele = soupz.findAll("a", {"class" : "glossary", "onmouseover" : "self.status='See Definition of [Total Functional Expenses]';return true;"})
        func_exp_text_ele = func_exp_text_ele[0] if func_exp_text_ele else None
        total_exp = func_exp_text_ele.parent.parent.next_sibling.next_sibling.text if func_exp_text_ele else None
        if total_exp:
            temp = total_exp.replace("$", "")
            total_exp = int(temp.replace(",", ""))
        else:
            total_exp = None

        if total_exp and total_exp <= 3500000:
            size = size_l[0]
        elif total_exp and total_exp > 3500000 and total_exp <= 13500000:
            size = size_l[1]
        else:
            size = size_l[2]

        # Fax Number
        fax_no = fax_p.findall(info_text)
        fax_no = fax_no[0] if fax_no else None

        # EIN Number
        ein_no = ein_p.findall(info_text)
        ein_no = ein_no[0] if ein_no else None

        # Filter out the contact numbers
        info_text = info_text.replace(tel_no, "") if tel_no else info_text
        info_text = info_text.replace(fax_no, "") if fax_no else info_text
        info_text = info_text.replace(ein_no, "") if ein_no else info_text

        # Charity Site
        link_objs = info_obj.findAll("a")
        for link in link_objs:
            charity_website = link.attrs['href'] if link.text == "Visit Web Site" else None

        # Mission Text
        mission_obj = soupz.find("div", {"class" : "mission"})
        mission_text = mission_obj.find("p").text if mission_obj else None

        # Clean up all variables
        name = name.encode('ascii', errors='ignore')
        info_text = info_text.encode('ascii', errors='ignore')
        tel_no = tel_no.encode('ascii', errors='ignore') if tel_no else None
        fax_no = fax_no.encode('ascii', errors='ignore') if fax_no else None
        ein_no = ein_no.encode('ascii', errors='ignore') if ein_no else None
        charity_website = charity_website.encode('ascii', errors='ignore') if charity_website else None
        mission_text = mission_text.encode('ascii', errors='ignore') if mission_text else None

        # name, address, telephone, fax, ein, web link, mission
        csv_writer.writerow([name, info_text, tel_no, fax_no, ein_no, charity_website, mission_text, size, category, city, state])

output_fp.close()
error_fp.close()
