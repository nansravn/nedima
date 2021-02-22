"""
Groundswell is an util module for continuous inspection of a hashtag
"""

import numpy as np 
import pickle
import datetime as dt
import os
import random
from instagramy import InstagramHashTag

from nedima.utils import env_setup


##############################################
##### KNOWN POST IDENTIFICATION SECTION  #####
##############################################

# Tries to locate a single post in a post_list
# It returns None if it can't indentify the post
def find_post(input_post, post_list):
    post_ids = [p.shortcode for p in post_list]
    if input_post.shortcode in post_ids:
        return post_ids.index(input_post.shortcode)
    else:
        return None

# Tries to locate any post from a list of targeted_posts in a post_list
# It returns the index of the most recent identified posts
# It returns None if it can't indentify any known post
def find_any_post(targeted_posts, post_list):
    for p in targeted_posts:
        idx = find_post(p, post_list)
        if idx != None:
            return idx
    return None


#########################################
##### POST INFO EXTRACTION SECTION  #####
#########################################

def convert_post2json(input_post):
    return {
        "caption":input_post.caption,
        "display_url" : input_post.display_url,
        "is_video" : 1*input_post.is_video,
        "post_url" : input_post.post_url,
        "shortcode" : input_post.shortcode,
        "upload_time" : input_post.upload_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "json_version" : "0.1"
    }


def convert_post2json_recursive(input_post_list):
    return [convert_post2json(p) for p in input_post_list]


################################################
##### INCREMENTAL POSTS WRANGLING SECTION  #####
################################################

# 1. Looks for the list of latest posts
# 2. Remove every post that is older than than the last post from the list of dated post
# 3. Return this trimmed post list
def trim_posts_overlap(tag_latest, tag_dated):
    post_dated = tag_dated.top_posts[0]
    diff_posts = [p for p in tag_latest.top_posts if p.upload_time > post_dated.upload_time]
    return diff_posts


def trim_posts_delta_seconds(tag_latest, tag_dated, delta_seconds = 30):
    diff_posts = trim_posts_overlap(tag_latest, tag_dated)
    for p in range(-20,-1):
        post_aux = diff_posts[p]
        if (post_aux.upload_time - diff_posts[p+1].upload_time).seconds > delta_seconds:
            return diff_posts[:p+1]
    return diff_posts


def get_diff_top_posts(tag_latest, tag_dated, flag_print = False, logging_dict = {}):
    post_latest = tag_latest.top_posts[0]
    post_dated = tag_dated.top_posts[0]
    #delete idx = find_post(post_dated, tag_latest.top_posts)
    idx = find_any_post(tag_dated.top_posts[:5], tag_latest.top_posts)
    delta_seconds = (post_latest.upload_time - post_dated.upload_time).seconds

    # If it didn't find a known post in the latest tag inspection
    if idx == None:
        diff_posts = trim_posts_overlap(tag_latest, tag_dated)
        uninspected_time = (diff_posts[-1].upload_time - post_dated.upload_time).seconds
        if flag_print:
            print("[TRIM] {} dated posts were removed by the trimming function".format(len(tag_latest.top_posts) - len(diff_posts)))
            print("[DIFF] {} new posts in the last {} seconds (idx was not found)".format(len(diff_posts), delta_seconds))
            print("[DIFF] Posts may have gotten lost for a period of {} seconds".format(uninspected_time))
         
    # If it did find a known post in the latest tag inspection 
    else:
        diff_posts = tag_latest.top_posts[:idx]
        uninspected_time = 0
        if flag_print:
            print("[DIFF] {} new posts in the last {} seconds".format(idx, delta_seconds))

    logging_dict['time_posts_total'] = int(delta_seconds)
    logging_dict['time_posts_lost'] = int(uninspected_time)
    logging_dict['time_posts_diff'] = logging_dict['time_posts_total'] - logging_dict['time_posts_lost']
    logging_dict['n_posts_total'] = int(len(tag_latest.top_posts))
    logging_dict['n_posts_diff'] = int(len(diff_posts))
    logging_dict['n_posts_trim'] = logging_dict['n_posts_total'] - logging_dict['n_posts_diff']
    return convert_post2json_recursive(diff_posts)


def get_diff_json(tag_latest, tag_dated, flag_print = False, logging_dict = {}):
    post_latest = tag_latest.top_posts[0]
    post_dated = tag_dated.top_posts[0]
    idx = find_any_post(tag_dated.top_posts[:5], tag_latest.top_posts)
    delta_seconds = (post_latest.upload_time - post_dated.upload_time).seconds
    json_latest = tag_latest.get_json()['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['edges']

    # If it didn't find a known post in the latest tag inspection
    if idx == None:
        diff_posts = trim_posts_overlap(tag_latest, tag_dated)
        diff_json = json_latest[:len(diff_posts)]
        uninspected_time = (diff_posts[-1].upload_time - post_dated.upload_time).seconds
        if flag_print:
            print("[TRIM] {} dated posts were removed by the trimming function".format(len(tag_latest.top_posts) - len(diff_posts)))
            print("[DIFF] {} new posts in the last {} seconds (idx was not found)".format(len(diff_json), delta_seconds))
            print("[DIFF] Posts may have gotten lost for a period of {} seconds".format(uninspected_time))
    # If it did find a known post in the latest tag inspection 
    else:
        diff_json = json_latest[:idx]
        uninspected_time = 0
        if flag_print:
            print("[DIFF] {} new posts in the last {} seconds".format(idx, delta_seconds))

    logging_dict['time_posts_total'] = int(delta_seconds)
    logging_dict['time_posts_lost'] = int(uninspected_time)
    logging_dict['time_posts_diff'] = logging_dict['time_posts_total'] - logging_dict['time_posts_lost']
    logging_dict['n_posts_total'] = int(len(tag_latest.top_posts))
    logging_dict['n_posts_diff'] = int(len(diff_json))
    logging_dict['n_posts_trim'] = logging_dict['n_posts_total'] - logging_dict['n_posts_diff']
    return diff_json


def structure_inspection_json(tag_latest, tag_dated, flag_print = False, logging_dict = {}):
    inspection_json = {
        "posts_short" : get_diff_top_posts(tag_latest, tag_dated, flag_print, logging_dict),
        "posts_full" : get_diff_json(tag_latest, tag_dated, False, logging_dict)
    }
    return inspection_json

###################################################
#####  SNAPSHOTING & TIME MANAGEMENT SECTION  #####
###################################################

def calculate_waiting_time(tag_latest, tag_dated, min_waiting_period=330, max_waiting_period=720, posts_to_wait=48, logging_dict = {}):
    post_latest = tag_latest.top_posts[0]
    post_dated = tag_dated.top_posts[0]
    idx = find_any_post(tag_dated.top_posts[:5], tag_latest.top_posts)

    # If post_latest == post_dated
    if idx == 0:
        return min_waiting_period
    # If it didn't find a known post in the latest tag inspection, replace post_dated and idx for new values
    elif idx == None:
        post_dated = trim_posts_delta_seconds(tag_latest, tag_dated)[-1]
        idx = len(trim_posts_delta_seconds(tag_latest, tag_dated))
    # If it did find a known post in the latest tag inspection, then do nothing
    
    average_post_period = (post_latest.upload_time - post_dated.upload_time)/idx
    suggested_waiting_period = (posts_to_wait*average_post_period).seconds
    clipped_waiting_period = np.clip(suggested_waiting_period, min_waiting_period, max_waiting_period)
    logging_dict['time_next_inspection'] = int(clipped_waiting_period)
    return clipped_waiting_period


def dump_inspection_snapshot(tag_latest, tag_dated, inspection_hastag = "surf", logging_dict = {}):
    dt_latest_inspection = tag_latest.top_posts[0].upload_time
    dt_next_inspection = tag_latest.top_posts[0].upload_time + dt.timedelta(seconds=int(calculate_waiting_time(tag_latest, tag_dated, logging_dict = logging_dict)))
    
    snapshot_dict = {}
    snapshot_dict['inspection_hashtag'] =  inspection_hastag
    snapshot_dict['dt_next_ispection'] = dt_next_inspection
    snapshot_dict['tag_dated'] = tag_latest

    with open(os.path.join('temp','inspection_snapshot_'+inspection_hastag+'.pickle'), "wb") as fp:
        pickle.dump(snapshot_dict, fp)

    return snapshot_dict


def calculate_remaining_sleep_time(dt_next_inspection):
    dt_now = dt.datetime.now()

    if dt_next_inspection > dt_now:
        return (dt_next_inspection - dt_now).seconds
    else:
        return 0


def load_inspection_snapshot(inspection_hastag = "surf", flag_print = True):
    with open(os.path.join('temp','inspection_snapshot_'+inspection_hastag+'.pickle'), "rb") as fp:
        snapshot_dict = pickle.load(fp)
    tag_dated = snapshot_dict['tag_dated']
    sleep_time = calculate_remaining_sleep_time(snapshot_dict['dt_next_ispection'])
    if flag_print:
        print("[SNAPSHOT] Next inspection scheduled for {}. {} seconds remaining.".format(snapshot_dict['dt_next_ispection'], sleep_time))
    return (tag_dated, sleep_time)


################################
#####  INSPECTION SECTION  #####
################################

def inspect_posts(inspection_hashtag = 'surf', secrets_dict = env_setup.load_secrets(), flag_print = False, logging_dict = {}):
    random_id = random.choice(secrets_dict['instagram']['session_id'])
    if flag_print:
        print("[SESSION] Randomly selected the sessionid {} for the next inspection".format(random_id))
    tag_latest = InstagramHashTag(inspection_hashtag, sessionid=random_id)
    logging_dict['id_hashtag'] = str(inspection_hashtag)
    logging_dict['id_instagram_session'] = str(random_id)
    return tag_latest


def start_inspection_iteration(inspection_hashtag = 'surf', secrets_dict = env_setup.load_secrets(), flag_print = True, logging_dict = {}):
    try:
        tag_dated, sleep_time = load_inspection_snapshot(inspection_hashtag, flag_print)
    except:
        tag_dated = inspect_posts(inspection_hashtag, secrets_dict, logging_dict = logging_dict)
        sleep_time = calculate_waiting_time(tag_dated, tag_dated, logging_dict = logging_dict)
        if flag_print:
            print("[SNAPSHOT] The snapshot couldn't be loaded. A new snapshot will be generated. Some posts may have gotten lost")
            print("[SNAPSHOT] {} seconds remaining until next inspection".format(sleep_time))
    return tag_dated, sleep_time