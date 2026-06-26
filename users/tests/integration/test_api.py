# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import requests

new_user_id = ""
new_user = {"name": "John Doe"}
# 10-12	Test that unauthenticated user has access to the list of users, expecting HTTP 401 status code as a response
def test_access_to_the_users_without_authentication(global_config):
    response = requests.get(global_config["APIEndpoint"] + '/users')
    assert response.status_code == 401
# 14-19	Test that authenticated non-administrative user has access to the list of users, expecting HTTP 403 status code as a response
def test_get_list_of_users_by_regular_user(global_config):
    response = requests.get(
        global_config["APIEndpoint"] + '/users',
        headers={'Authorization': global_config["regularUserIdToken"]}
    )
    assert response.status_code == 403
# 21-28	Test that authenticated non-administrative user can create a new user, expecting HTTP 403 status code as a response
def test_deny_post_user_by_regular_user(global_config):
    response = requests.post(
        global_config["APIEndpoint"] + '/users',
        data=json.dumps(new_user),
        headers={'Authorization': global_config["regularUserIdToken"],
                 'Content-Type': 'application/json'}
    )
    assert response.status_code == 403
# 30-41	Test that authenticated administrative user can create a new user, expecting response with newly created user data
def test_allow_post_user_by_administrative_user(global_config):
    response = requests.post(
        global_config["APIEndpoint"] + '/users',
        data=json.dumps(new_user),
        headers={'Authorization': global_config["adminUserIdToken"],
                 'Content-Type': 'application/json'}
    )
    assert response.status_code == 200
    data = json.loads(response.text)
    assert data['name'] == new_user['name']
    global new_user_id
    new_user_id = data['userid']
# 43-51	Test that authenticated administrative user can create a new user using invalid request payload (wrong field name case), expecting HTTP 400 status code as a response
def test_deny_post_invalid_user(global_config):
    new_invalid_user = {"Name": "John Doe"}
    response = requests.post(
        global_config["APIEndpoint"] + '/users',
        data=new_invalid_user,
        headers={'Authorization': global_config["adminUserIdToken"],
                 'Content-Type': 'application/json'}
    )
    assert response.status_code == 400

def test_get_user_by_regular_user(global_config):
    response = requests.get(
        global_config["APIEndpoint"] + f'/users/{new_user_id}',
        headers={'Authorization': global_config["regularUserIdToken"]}
    )
    assert response.status_code == 403