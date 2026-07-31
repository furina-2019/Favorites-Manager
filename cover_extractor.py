import re
import json
from urllib.parse import urlparse, urljoin, unquote
import codecs
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.google.com/'
}

def normalize_url(url):
    if url.startswith('//'):
        url = 'https:' + url
    elif url.startswith('/'):
        url = 'https://www.example.com' + url
    return url

def decode_unicode_url(url):
    try:
        return codecs.decode(url, 'unicode_escape')
    except:
        return url

def extract_cover_bilibili(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return decode_unicode_url(normalize_url(og_image['content']))
    
    script_tags = soup.find_all('script')
    for script in script_tags:
        script_content = script.string
        if script_content:
            match = re.search(r'"pic":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'cover":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"thumbnail":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if 'videoData' in data and 'pic' in data['videoData']:
                        return decode_unicode_url(normalize_url(data['videoData']['pic']))
                    if 'p' in data and isinstance(data['p'], dict):
                        for key in ['pic', 'cover', 'thumbnail']:
                            if key in data['p']:
                                return decode_unicode_url(normalize_url(data['p'][key]))
                except:
                    pass
    
    return None

def extract_cover_douyin(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return decode_unicode_url(normalize_url(og_image['content']))
    
    script_tags = soup.find_all('script')
    for script in script_tags:
        script_content = script.string
        if script_content:
            match = re.search(r'"cover":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"poster":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"image":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if 'awemeDetail' in data:
                        detail = data['awemeDetail']
                        if 'video' in detail and 'cover' in detail['video']:
                            cover_info = detail['video']['cover']
                            if isinstance(cover_info, dict):
                                for key in ['origin_cover', 'dynamic_cover', 'cover_img_url', 'url_list']:
                                    if key in cover_info:
                                        val = cover_info[key]
                                        if isinstance(val, list) and val:
                                            return decode_unicode_url(normalize_url(val[0]))
                                        elif isinstance(val, str):
                                            return decode_unicode_url(normalize_url(val))
                        if 'music' in detail and 'cover_hd' in detail['music']:
                            return decode_unicode_url(normalize_url(detail['music']['cover_hd']))
                except:
                    pass
    
    video_tag = soup.find('video')
    if video_tag and video_tag.get('poster'):
        return decode_unicode_url(normalize_url(video_tag['poster']))
    
    thumbnail_selectors = [
        'img[class*="cover"]', 'img[class*="poster"]', 'img[class*="thumbnail"]',
        'img.cover', 'img.poster', 'img.thumbnail'
    ]
    for selector in thumbnail_selectors:
        img = soup.select_one(selector)
        if img and img.get('src'):
            return decode_unicode_url(normalize_url(img['src']))
    
    return None

def extract_cover_tiktok(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return decode_unicode_url(normalize_url(og_image['content']))
    
    script_tags = soup.find_all('script')
    for script in script_tags:
        script_content = script.string
        if script_content:
            match = re.search(r'"cover":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"poster":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"thumbnail":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
    
    video_tag = soup.find('video')
    if video_tag and video_tag.get('poster'):
        return decode_unicode_url(normalize_url(video_tag['poster']))
    
    return None

def extract_cover_xiaohongshu(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return decode_unicode_url(normalize_url(og_image['content']))
    
    script_tags = soup.find_all('script')
    for script in script_tags:
        script_content = script.string
        if script_content:
            match = re.search(r'"cover_url":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"image_list":\[([^]]+)\]', script_content)
            if match:
                inner_content = match.group(1)
                url_match = re.search(r'"url":"([^"]+)"', inner_content)
                if url_match:
                    return decode_unicode_url(normalize_url(url_match.group(1)))
            match = re.search(r'"images":\[([^]]+)\]', script_content)
            if match:
                inner_content = match.group(1)
                url_match = re.search(r'"url":"([^"]+)"', inner_content)
                if url_match:
                    return decode_unicode_url(normalize_url(url_match.group(1)))
    
    thumbnail_selectors = ['img[class*="share"]', 'img[class*="cover"]']
    for selector in thumbnail_selectors:
        img = soup.select_one(selector)
        if img and img.get('src'):
            return decode_unicode_url(normalize_url(img['src']))
    
    return None

def extract_cover_iqiyi(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return decode_unicode_url(normalize_url(og_image['content']))
    
    script_tags = soup.find_all('script')
    for script in script_tags:
        script_content = script.string
        if script_content:
            match = re.search(r'"imageUrl":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"pic":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"cover":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
    
    video_tag = soup.find('video')
    if video_tag and video_tag.get('poster'):
        return decode_unicode_url(normalize_url(video_tag['poster']))
    
    return None

def extract_cover_tencent(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return decode_unicode_url(normalize_url(og_image['content']))
    
    script_tags = soup.find_all('script')
    for script in script_tags:
        script_content = script.string
        if script_content:
            match = re.search(r'"coverUrl":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"pic":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"image":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
    
    video_tag = soup.find('video')
    if video_tag and video_tag.get('poster'):
        return decode_unicode_url(normalize_url(video_tag['poster']))
    
    return None

def extract_cover_kuaishou(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return decode_unicode_url(normalize_url(og_image['content']))
    
    script_tags = soup.find_all('script')
    for script in script_tags:
        script_content = script.string
        if script_content:
            match = re.search(r'"cover":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"poster":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
    
    video_tag = soup.find('video')
    if video_tag and video_tag.get('poster'):
        return decode_unicode_url(normalize_url(video_tag['poster']))
    
    return None

def extract_cover_cctv(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return decode_unicode_url(normalize_url(og_image['content']))
    
    script_tags = soup.find_all('script')
    for script in script_tags:
        script_content = script.string
        if script_content:
            match = re.search(r'"image":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"cover":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
    
    return None

def extract_cover_youtube(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return decode_unicode_url(normalize_url(og_image['content']))
    
    video_id_match = re.search(r'(?:v=|\/embed\/|\/v\/|youtu\.be\/)([^&\n?]+)', url)
    if video_id_match:
        video_id = video_id_match.group(1)
        return f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
    
    return None

def extract_cover_general(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    og_image = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return decode_unicode_url(normalize_url(og_image['content']))
    
    twitter_image = soup.find('meta', property='twitter:image') or soup.find('meta', attrs={'name': 'twitter:image'})
    if twitter_image and twitter_image.get('content'):
        return decode_unicode_url(normalize_url(twitter_image['content']))
    
    video_tag = soup.find('video')
    if video_tag and video_tag.get('poster'):
        return decode_unicode_url(normalize_url(video_tag['poster']))
    
    thumbnail_selectors = [
        'img.cover', 'img.thumbnail', 'img.video-cover',
        'img[class*="cover"]', 'img[class*="thumbnail"]',
        'meta[itemprop="image"]'
    ]
    for selector in thumbnail_selectors:
        if selector.startswith('meta'):
            meta = soup.find('meta', itemprop='image')
            if meta and meta.get('content'):
                return decode_unicode_url(normalize_url(meta['content']))
        else:
            img = soup.select_one(selector)
            if img and img.get('src'):
                return decode_unicode_url(normalize_url(img['src']))
    
    script_tags = soup.find_all('script')
    for script in script_tags:
        script_content = script.string
        if script_content:
            match = re.search(r'"cover":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
            match = re.search(r'"poster":"([^"]+)"', script_content)
            if match:
                return decode_unicode_url(normalize_url(match.group(1)))
    
    return None

def identify_platform(url):
    url_lower = url.lower()
    if 'bilibili' in url_lower or 'bilibili.com' in url_lower:
        return 'bilibili'
    elif 'douyin' in url_lower or 'douyin.com' in url_lower or 'dytt' in url_lower:
        return 'douyin'
    elif 'tiktok' in url_lower or 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'xiaohongshu' in url_lower or 'xiaohongshu.com' in url_lower or 'xhs' in url_lower:
        return 'xiaohongshu'
    elif 'iqiyi' in url_lower or 'iqiyi.com' in url_lower:
        return 'iqiyi'
    elif 'qq.com' in url_lower and ('video' in url_lower or 'v.qq' in url_lower):
        return 'tencent'
    elif 'kuaishou' in url_lower or 'kuaishou.com' in url_lower or 'ks' in url_lower:
        return 'kuaishou'
    elif 'tv.cctv.com' in url_lower or 'cntv.cn' in url_lower:
        return 'cctv'
    elif 'youtube' in url_lower or 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    else:
        return 'general'

def extract_cover(url):
    platform = identify_platform(url)
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"[DEBUG] Failed to fetch page for {platform}: {str(e)}")
        return None
    
    extractors = {
        'bilibili': extract_cover_bilibili,
        'douyin': extract_cover_douyin,
        'tiktok': extract_cover_tiktok,
        'xiaohongshu': extract_cover_xiaohongshu,
        'iqiyi': extract_cover_iqiyi,
        'tencent': extract_cover_tencent,
        'kuaishou': extract_cover_kuaishou,
        'cctv': extract_cover_cctv,
        'youtube': extract_cover_youtube,
        'general': extract_cover_general
    }
    
    extractor = extractors.get(platform, extract_cover_general)
    cover = extractor(html_content, url)
    
    if cover and not cover.startswith(('http://', 'https://')):
        parsed = urlparse(url)
        if cover.startswith('//'):
            cover = f"{parsed.scheme}:{cover}"
        elif cover.startswith('/'):
            cover = f"{parsed.scheme}://{parsed.netloc}{cover}"
        else:
            cover = urljoin(url, cover)
    
    print(f"[DEBUG] Extracted cover for {platform}: {cover}")
    return cover