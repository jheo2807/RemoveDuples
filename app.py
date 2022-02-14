"""
Streamlit Cheat Sheet
App to summarise streamlit docs v0.71.0 for quick reference
There is also an accompanying png version
https://github.com/daniellewisDL/streamlit-cheat-sheet
v0.71.0 November 2020 Daniel Lewis and Austin Chen
"""
import io
import json
import os

import imagehash
import numpy as np
import requests
import streamlit as st
import random
import timeit
from PIL import ImageFile, Image
from itertools import combinations, permutations
import pandas as pd
from collections import defaultdict

ImageFile.LOAD_TRUNCATED_IMAGES = True

st.set_page_config(
     page_title='이미지 중복 제거',
     layout="wide",
     initial_sidebar_state="expanded",
)

in_num = 10
HASH_SIZE = 32

MATCH_RATIO = 80 # 80% 동일
THRESHOLD = int((HASH_SIZE**2) * (1 - (MATCH_RATIO / 100)))
random.seed()
average_time = defaultdict(list)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36"}
COLUMNS = ["DESC_IMG1", "DESC_IMG2", "DESC_IMG3", "DESC_IMG4", "DESC_IMG5"]


with open('img_info.json', encoding="UTF-8") as f:
    _rtb_data = json.load(f)


def timer(func):
    def wrapper(*args, **kwargs):
        start = timeit.default_timer()
        val = func(*args, **kwargs)
        end = timeit.default_timer()
        if isinstance(args[0], list):
            average_time[func.__name__].extend([end-start] * len(args[0]))
        else:
            average_time[func.__name__].append(end - start)
        return val
    return wrapper


def make_clickable_pic(url, score=1.0):
    style = 'height:200px;'
    return f"""<a href="{url}" target="_blank"><img src="{url}" title="{score}" style="{style}"/></a> """


@timer
def download_image(_url):
    try:
        response = requests.get(_url, headers=HEADERS, stream=True)
        image_bytes = io.BytesIO(response.content)
        img = Image.open(image_bytes)
    except Exception as e:
        print(e, _url)
        img = None
    return img

#http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html
@timer
def convert_img2hash(_url, img):
    if img is None:
        return None
    _hash = imagehash.phash(img, HASH_SIZE)
    return _hash


@timer
def remove_duplicated(urls, hashs):
    hash_map = {}
    for i, _hash in enumerate(hashs):
        if _hash is None:
            continue
        if _hash in hash_map:
            continue
        else:
            hash_map[_hash] = urls[i]
    unique_urls = remove_similar_image(hash_map)
    return list(unique_urls.values())


# @timer
def remove_similar_image(hash_map):
    compare_list = permutations(hash_map, 2)
    for a, b in compare_list:
        if a not in hash_map or b not in hash_map:
            continue
        score = np.count_nonzero(a.hash != b.hash)
        if score <= THRESHOLD:
            hash_map.pop(b)
    return hash_map


def display_origin_data(urls):
    targets = [
        make_clickable_pic(url)
        for url in urls
    ]
    return '\n'.join(targets)


def display_unique(urls):
    hashs = []
    for i, _url in enumerate(urls):
        img = download_image(_url)
        _hash = convert_img2hash(_url, img)
        hashs.append(_hash)
    unique_url = remove_duplicated(urls, hashs)

    outputs = '\n'.join([make_clickable_pic(u) for u in unique_url])
    similars = f"""<div style="position:relative; overflow-x:scroll; width:100%; white-space: nowrap">{outputs}</div>"""
    return similars


def build_div(samples):
    divs = []
    for sample in samples:
        urls = [sample[c] for c in COLUMNS if sample[c] != 'NULL']
        html = f"""<hr>
        <div style="position:relative; overflow-x:scroll; width:100%; white-space: nowrap">
        {display_origin_data(urls)}
        </div>
        {display_unique(urls)}
        """
        divs.append(html)
    return divs


def demo_body(data, limit=in_num):
    samples = random.sample(data, limit)
    divs = build_div(samples)
    with st.beta_container():
        print(len(average_time.get('download_image')))
        print(len(average_time.get('convert_img2hash')))
        print(len(average_time.get('remove_duplicated')))
        data = pd.DataFrame([average_time.get('download_image'),
                             average_time.get('convert_img2hash'),
                             average_time.get('remove_duplicated')],
                            index=['이미지 다운로드', '이미지 변환', '중복 제거']).T
        st.bar_chart(data)
        for div in divs:
            st.write(div, unsafe_allow_html=True)
        average_time.clear()
    return None


if __name__ == '__main__':
    demo_body(_rtb_data)
