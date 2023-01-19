import hashlib
import io
import os
import random
import requests
import string
import sys
import time
import logging

from p2d._version import __version__

POLYGON_ADDRESS = 'https://polygon.codeforces.com/api/'

# Call to a Polygon API.
# It returns the response, checking that the return status is ok.
def call_polygon_api(key, secret, method_name, params):
    params['apiKey'] = key
    params['time'] = int(time.time())
    
    rand = ''.join(random.choices(string.ascii_uppercase, k=6))
    pref = rand + '/' + method_name + '?'
    params_arr = []
    for p in params:
        params_arr.append((p, params[p]))
    params_arr.sort()
    middle = ""
    for pp in params_arr:
        if middle:
            middle += '&'
        middle += str(pp[0]) + '=' + str(pp[1])
    suff = '#' + secret

    to_hash = pref + middle + suff
    params['apiSig'] = rand + hashlib.sha512(to_hash.encode()).hexdigest()

    logging.debug('Sending API request:\n'
                  + ('\t method = %s\n' % method_name)
                  + '\t params = %s' % params)

    res = requests.post(POLYGON_ADDRESS + method_name, data = params)
    if not res.ok:
        logging.error('API call to Polygon returned status %s. The content of the response is %s.' % (res.status_code, res.text))
        exit(1)
    assert(res.ok)
    return res

# Returns the pair (revision, package_id) corresponding to the latest
# revision of the problem which has a package of type linux ready.
# It returns (-1, -1) if no valid package is found.
def get_latest_package_id(key, secret, problem_id):
    packages_list = call_polygon_api(key, secret, 'problem.packages',
                                     {'problemId': problem_id}).json()

    if packages_list['status'] != 'OK':
        logging.error('API problem.packages request to Polygon failed with error: %s'              % packages_list['comment'])
        exit(1)

    revision = -1
    package_id = -1
    for p in packages_list['result']:
        if p['revision'] > revision and p['state'] == 'READY' \
           and p['type'] == 'linux':
            revision = p['revision']
            package_id = p['id']
    return (revision, package_id)

# Downloads the Polygon package into polygon_zip (as a .zip archive).
def download_package(key, secret, problem_id, package_id, polygon_zip):
    package = call_polygon_api(key, secret, 'problem.package',
                               {'problemId': problem_id,
                                'packageId': package_id,
                                'type': 'linux'})
    with open(polygon_zip, "wb") as f:
        f.write(io.BytesIO(package.content).getbuffer())

# Fetches the list of problems of the specified contest
# as a dictionary {problem_label: problem_info}.
def get_contest_problems(key , secret, contest_id):
    return call_polygon_api(key, secret, 'contest.problems', {'contestId': contest_id}).json()['result']
