"""DSD Approvals _jobs file."""
import os
from datetime import datetime, timedelta
from dateutil.parser import parse
import pandas as pd
from lxml import etree
from bs4 import BeautifulSoup as bs
import requests
import time
from trident.util import general
import logging

conf = general.config

dsd_temp_dir = general.create_path_if_not_exists(conf['temp_data_dir'] + '/')

approval_dict = {
    'completed':
    ['currentweekdsdpermitscompleted.xml', 'permits_completed_ytd_datasd_v1.csv'],
    'issued':
    ['currentweekdsdpermitsissued.xml', 'permits_issued_ytd_datasd_v1.csv'],
    'applied':
    ['currentweekdsdapplicationsreceived.xml', 'apps_received_ytd_datasd_v1.csv']
}


def scrape_dsd(key):
    """Consolidate weekly data by scraping OpenDSD API."""
    src = approval_dict[key][0]
    xml_file = dsd_temp_dir + src
    tree = etree.parse(xml_file)
    root = tree.getroot()
    approvals = root.find('approvals')
    list_app = approvals.findall('approval')
    len_list = len(list_app)
    max_val = len_list - 1

    rows = list()

    count_log = range(0, max_val, 5)

    for i in range(0, max_val):

        app_id = int(list_app[i].attrib['approval_id'])
        app_type_id = int(list_app[i].find('approval_type_id').text)


        if key == 'applied':

            app_xml_dict = {
                'app_date': list_app[i].find('application_date').text,
                'iss_date': 'NaN',
                'insp_date': 'NaN',
                'comp_date': 'NaN',
                'app_type': list_app[i].find('approval_type').text,
                'lat': float(list_app[i].find('latitude').text),
                'lon': float(list_app[i].find('longitude').text),
                'iss_by': 'NaN',
                'pmt_hldr': 'NaN',
                'scope': 'NaN',
                'pj_id': list_app[i].find('project_id').text,
                'jb_id': 'NaN',
                'status': 'NaN',
                'dep': 'NaN',
                'sqft': 'NaN',
                'val': 'NaN'}

        else:
            dsd_api = 'https://opendsd.sandiego.gov/'\
                  + 'api//approval/{0}'.format(app_id)
            page = requests.get(dsd_api, timeout=20)
            content = page.content
            xmlsoup = bs(content, 'lxml-xml')

            if i in count_log:
                logging.info(str(i) + ' / ' + str(max_val) + ' completed.')

            app_xml_dict = {
                'app_date': xmlsoup.Project.ApplicationDate.text.strip(),
                'iss_date': xmlsoup.Approval.IssueDate.text.strip(),
                'insp_date': xmlsoup.Approval.FirstInspectionDate.text.strip(),
                'comp_date': xmlsoup.Approval.CompleteCancelDate.text.strip(),
                'app_type': xmlsoup.Approval.Type.text.strip(),
                'lat': xmlsoup.Job.Latitude.text.strip(),
                'lon': xmlsoup.Job.Longitude.text.strip(),
                'iss_by': xmlsoup.Approval.IssuedBy.text.strip(),
                'pmt_hldr': xmlsoup.Approval.PermitHolder.text.strip(),
                'scope': xmlsoup.Approval.Scope.text.strip(),
                'pj_id': xmlsoup.Project.ProjectId.text.strip(),
                'jb_id': xmlsoup.Approval.JobId.text.strip(),
                'status': xmlsoup.Approval.Status.text.strip(),
                'dep': xmlsoup.Approval.Depiction.text.strip(),
                'sqft': xmlsoup.Approval.SquareFootage.text.strip(),
                'val': xmlsoup.Approval.Valuation.text.strip()
                }

        rows.append([app_id, 
            app_xml_dict['app_type'], 
            app_type_id, 
            app_xml_dict['app_date'], 
            app_xml_dict['iss_date'], 
            app_xml_dict['insp_date'],
            app_xml_dict['comp_date'], 
            app_xml_dict['lat'], 
            app_xml_dict['lon'], 
            app_xml_dict['iss_by'], 
            app_xml_dict['pmt_hldr'], 
            app_xml_dict['scope'], 
            app_xml_dict['pj_id'], 
            app_xml_dict['jb_id'],
            app_xml_dict['status'], 
            app_xml_dict['dep'], 
            app_xml_dict['sqft'], 
            app_xml_dict['val']])

    df = pd.DataFrame(
        rows,
        columns=[
            'approval_id', 'approval_type', 'approval_type_id',
            'date_application', 'date_issued', 'date_first_inspected',
            'date_complete_cancel', 'lat', 'lng', 'issued_by',
            'permit_holder', 'scope', 'project_id', 'job_id', 'status',
            'depiction', 'square_footage', 'valuation'
        ])

    df['date_application'] = pd.to_datetime(
        df['date_application'], errors='coerce')

    df['date_issued'] = pd.to_datetime(df['issue_date'], errors='coerce')

    df['date_first_inspected'] = pd.to_datetime(
        df['date_first_inspected'], errors='coerce')

    df['date_complete_cancel'] = pd.to_datetime(
        df['date_complete_cancel'], errors='coerce')

    if key == 'issued':
        df = df.drop(
            ['date_first_inspected', 'date_complete_cancel'], axis=1)
        df = df.sort_values(by='date_issued')

    elif key == 'applied':
        df = df.drop(
            [
                'date_issued', 'date_first_inspected',
                'date_complete_cancel', 'issued_by', 'permit_holder',
                'scope', 'job_id', 'status', 'depiction',
                'square_footage', 'valuation'
            ],
            axis=1)
        df = df.sort_values(by='date_application')

    elif key == 'completed':
        df = df.sort_values(by='date_complete_cancel')

    general.pos_write_csv(
        df,
        dsd_temp_dir + '{0}_week.csv'.format(key),
        date_format=conf['date_format_ymd_hms'])

    return 'Successfully scraped ' + key + ' permits.'


def update_dsd(key):
    """Add weekly data to current production data."""
    y_src = conf['prod_data_dir'] + '/' + approval_dict[key][1]
    w_src = dsd_temp_dir + key + '_week.csv'
    ytd = pd.read_csv(y_src)
    week = pd.read_csv(w_src)
    prod = ytd.append(week, ignore_index=True)
    prod = prod.drop_duplicates(subset=['approval_id'])

    if key == 'applied':
        prod = prod.sort_values(by='date_application')
    elif key == 'issued':
        prod = prod.sort_values(by='date_issued')
    elif key == 'completed':
        prod = prod.sort_values(by='date_complete_cancel')

    general.pos_write_csv(prod, y_src, date_format=conf['date_format_ymd_hms'])

    return 'Successfully updated ' + key + 'permits.'


def extract_solar(key):
    """Extract solar permits from production files."""
    prod_src = conf['prod_data_dir'] + '/' + approval_dict[key][1]
    solar_pmts = conf['prod_data_dir'] + '/' + 'solar_permits_' + key + '_ytd_datasd_v1.csv'

    ytd = pd.read_csv(prod_src)

    solar = ytd[ytd['approval_type_id'] == 293]

    if key == 'applied':
        solar = solar.sort_values(by='date_application')
    elif key == 'issued':
        solar = solar.sort_values(by='date_issued')
    elif key == 'completed':
        solar = solar.sort_values(by='date_complete_cancel')

    general.pos_write_csv(solar, solar_pmts, date_format=conf['date_format_ymd_hms'])

    return 'Successfully updated ' + key + ' solar permits.'
