#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""slug 工具：中文名 → ASCII slug（域名/路径派生）。

为什么要有这个文件
------------------
`add_sites.py` 原先直接拿「工具名」做 slug，中文名就产出中文 URL
（`/tools/在线解压工具-fileunzip-云端万能解压-免费支持50-格式-app喵-精选`）。
这类 URL 在英文站上不好读、不好分享，也不好贴到任何地方。

库内本来就有 domain 派生的 ASCII 惯例（`theresanaiforthat-com` / `grok-com` /
`www-qingwafm-com`），这里沿用并扩展到「域名 + 有效路径片段」——
实测同一个站点的多个工具（toolwa.com 的 19 个页面）路径都是英文
（`/maze`、`/dns`、`/password-gen`），带上路径既唯一又可读。

用法：
    from slug_util import ascii_slug, has_cjk
    slug = ascii_slug("https://toolwa.com/maze")   # → "toolwa-com-maze"
"""
import re
from urllib.parse import urlparse

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_HEXY = re.compile(r"^[0-9a-f]{12,}$", re.I)
MAXLEN = 60


def has_cjk(s):
    return bool(CJK_RE.search(s or ""))


def _seg_ok(seg):
    """路径片段是否「有意义」（可读、非哈希、非纯数字 id、不过长）。"""
    if not seg or _HEXY.match(seg):
        return False
    if re.fullmatch(r"\d+", seg):
        return False
    if len(seg) > 24:
        return False
    return bool(re.search(r"[a-z]", seg, re.I))


def ascii_slug(url, fallback_name=""):
    """host[-path]，去掉 www。路径无可读片段时只用 host。

    >>> ascii_slug("https://www.qingwafm.com")        # 'qingwafm-com'
    >>> ascii_slug("https://toolwa.com/maze")         # 'toolwa-com-maze'
    >>> ascii_slug("https://x.com/utms/1f2e3d4c5b6a7f8e9d0c1b2a")
    'x-com-utms'                                       # 哈希段被丢弃，可读段保留
    """
    u = url if "://" in (url or "") else "http://" + (url or "")
    p = urlparse(u)
    host = (p.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return ""
    base = re.sub(r"[^a-z0-9]+", "-", host).strip("-")
    segs = [s for s in (p.path or "").split("/") if s]
    good = [re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") for s in segs if _seg_ok(s)]
    good = [g for g in good if g]
    if good:
        base = f"{base}-{'-'.join(good)}"
    return base[:MAXLEN].strip("-")
