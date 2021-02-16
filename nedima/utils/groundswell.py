"""
Groundswell is an util module for continuous inspection of a hashtag
"""

import numpy as np 

def trim_top_posts(top_posts, delta_seconds = 40):
    for p in range(-25,-1):
        post_aux = top_posts[p]
        if (post_aux.upload_time - top_posts[p+1].upload_time).seconds > delta_seconds:
            return top_posts[:p+1]
    return top_posts[:-12]

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


def get_latest_datetime(tag_latest, date_format="%Y/%m/%d"):
    latest_datetime = tag_latest.top_posts[0].upload_time
    if date_format == None:
        return latest_datetime
    elif date_format == 'date':
        return latest_datetime.strftime("%Y%m%d")
    elif date_format == 'time':
        return latest_datetime.strftime("%H%M%S")
    else:
        return latest_datetime.strftime(date_format)



def get_diff_top_posts(tag_latest, tag_dated, flag_print = True):
    post_latest = tag_latest.top_posts[0]
    post_dated = tag_dated.top_posts[0]
    #delete idx = find_post(post_dated, tag_latest.top_posts)
    idx = find_any_post(tag_dated.top_posts[:5], tag_latest.top_posts)
    delta_seconds = (post_latest.upload_time - post_dated.upload_time).seconds

    # If it didn't find a known post in the latest tag inspection
    if idx == None:
        diff_posts = trim_top_posts(tag_latest.top_posts)
        if flag_print:
            print("[TRIM] {} dated posts were removed by the trimming function".format(len(tag_latest.top_posts) - len(diff_posts)))
            print("[DIFF] {} new posts in the last {} seconds (idx was not found)".format(len(diff_posts), delta_seconds))
            uninspected_time = (diff_posts[-1].upload_time - post_dated.upload_time).seconds
            print("[DIFF] Posts may have gotten lost for a period of {} seconds".format(uninspected_time))
         
    # If it did find a known post in the latest tag inspection 
    else:
        diff_posts = tag_latest.top_posts[:idx]
        if flag_print:
            print("[DIFF] {} new posts in the last {} seconds".format(idx, delta_seconds))

    return convert_post2json_recursive(diff_posts)


def get_diff_json(tag_latest, tag_dated, flag_print = True):
    post_latest = tag_latest.top_posts[0]
    post_dated = tag_dated.top_posts[0]
    idx = find_any_post(tag_dated.top_posts[:5], tag_latest.top_posts)
    delta_seconds = (post_latest.upload_time - post_dated.upload_time).seconds
    json_latest = tag_latest.get_json()['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['edges']

    # If it didn't find a known post in the latest tag inspection
    if idx == None:
        diff_posts = trim_top_posts(tag_latest.top_posts)
        diff_json = json_latest[:len(diff_posts)]
        if flag_print:
            print("[TRIM] {} dated posts were removed by the trimming function".format(len(tag_latest.top_posts) - len(diff_posts)))
            print("[DIFF] {} new posts in the last {} seconds (idx was not found)".format(len(diff_json), delta_seconds))
            uninspected_time = (diff_posts[-1].upload_time - post_dated.upload_time).seconds
            print("[DIFF] Posts may have gotten lost for a period of {} seconds".format(uninspected_time))
    # If it did find a known post in the latest tag inspection 
    else:
        diff_json = json_latest[:idx]
        if flag_print:
            print("[DIFF] {} new posts in the last {} seconds".format(idx, delta_seconds))

    return diff_json


def calculate_waiting_time(tag_latest, tag_dated, min_waiting_period=360, max_waiting_period=600, posts_to_wait=48):
    post_latest = tag_latest.top_posts[0]
    post_dated = tag_dated.top_posts[0]
    idx = find_any_post(tag_dated.top_posts[:5], tag_latest.top_posts)

    # If post_latest == post_dated
    if idx == 0:
        return min_waiting_period
    # If it didn't find a known post in the latest tag inspection, replace post_dated and idx for new values
    elif idx == None:
        post_dated = trim_top_posts(tag_latest.top_posts)[-1]
        idx = len(trim_top_posts(tag_latest.top_posts))
    # If it did find a known post in the latest tag inspection, then do nothing
    
    average_post_period = (post_latest.upload_time - post_dated.upload_time)/idx
    suggested_waiting_period = (posts_to_wait*average_post_period).seconds
    return np.clip(suggested_waiting_period, min_waiting_period, max_waiting_period)


