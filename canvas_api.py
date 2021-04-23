import requests
import json
from gvars import CANVAS_DOMAIN, CANVAS_TOKEN


def send_request(request_url, params=[], method='GET', payload=None):
    '''Send request to request_url with given params and payload and return data from all paginated pages'''
    base_url = '/api/v1/'
    url = CANVAS_DOMAIN + base_url + request_url
    for param in params:
        url += '?' + param
    url += '/?per_page=1000'
    headers = {'Authorization': f'Bearer {CANVAS_TOKEN}'}
    page = 1
    # Send request and get data by looping trought all pages 
    while True:
        response = requests.request(method, url, headers=headers, data=payload)
        if page == 1:
            all_pages_response = json.loads(response.text)     
        else:
            all_pages_response += json.loads(response.text)
        page += 1
        if len(response.links) > 1:
            current_url = response.links['current']['url']
            last_url = response.links['last']['url']
            if current_url != last_url:
                url = response.links['next']['url']
            else:
                break
        else:
            break
    # seperate original response from last page and final text result of all pages
    new_response = {}        
    new_response['origin'] = response
    new_response['text'] = all_pages_response
    return new_response

def active_courses_in_account(account_id):
    '''Get an account_id and return all active courses in that account'''
    url = 'accounts/{id}/courses'.format(id=account_id)
    res = send_request(url)
    return res

def get_course_enrollments(course_id):
    '''Get a course_id and returns all user enrollments in that course'''
    url = 'courses/{id}/enrollments'.format(id=course_id)
    res = send_request(url)
    return res

def delete_user_enrollment(course_id, enrollment_id):
    '''Given a course_id and enrollment_id, delete user enrollment from course'''
    url = 'courses/{cid}/enrollments/{eid}'.format(cid=course_id, eid=enrollment_id)
    res = send_request(url, method='DELETE')
    return res

def delete_all_course_enrollments(course_id):
    '''Get a course_id and delete all user enrollments from that course. Return True if success'''
    res = get_course_enrollments(course_id)
    res_status = res['origin'].status_code
    if res_status == 200:
        enrolls = [e for e in res['text']]
        tot = len(enrolls)
        don = 0
        err = 0
        for enroll in enrolls:
            res = delete_user_enrollment(course_id, enroll['id'])
            if res['origin'].status_code != 200:
                print('Error removing user from course {c}'.format(c=course_id))
                err += 1
            don += 1
            if don % 100 == 0:
                print('{d}/{t} done with {e} errors!'.format(d=don, t=tot, e=err))
        print('Done.')
        return True
    return False

def delete_all_acount_enrollments(account_id):
    '''Get a account_id and delete all user enrollments from that account. Return True if success'''
    res = active_courses_in_account(account_id)
    res_status = res['origin'].status_code
    if res_status == 200:
        courses = res['text']
        tot = len(courses)
        print('Total of {t} course to delete enrollments'.format(t=tot))
        don = 0
        err = 0
        for course in courses:
            print('Removing Enrollments of course {c}...'.format(c=course['id']), end=' ')
            res = delete_all_course_enrollments(course['id'])
            if not res:
                err += 1
                print('Error deleting enrollments from course {c}'.format(c=course['id']))
            don += 1
            if don % 50 == 0:
                print('{d}/{t} done with {e} errors!'.format(d=don, t=tot, e=err))
        return True
    return False
