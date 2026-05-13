#!/usr/bin/env python3
"""Convert Rolex.org JSON files to markdown, preserving folder structure."""

import json
import re
import sys
from pathlib import Path
from html.parser import HTMLParser

SOURCE_DIR = Path("/Users/olivier/Developer/Scripting/dot-org/data/www.rolex.org.en")
TARGET_DIR = Path("/Users/olivier/Developer/Scripting/dot-org/data/rolex_dot_org")
IMAGE_PREFIX = "https://images.rolex.org"


# ---------------------------------------------------------------------------
# HTML → Markdown helpers
# ---------------------------------------------------------------------------

class _HtmlToMd(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True
        elif tag == "br":
            self.parts.append("\n")
        elif tag in ("b", "strong"):
            self.parts.append("**")
        elif tag in ("i", "em"):
            self.parts.append("_")
        elif tag == "p":
            if self.parts and self.parts[-1] not in ("\n\n", "\n"):
                self.parts.append("\n\n")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.parts.append("\n" + "#" * level + " ")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag == "a":
            d = dict(attrs)
            href = d.get("href", "")
            self.parts.append(f"[")
            self._pending_href = href
        else:
            self._pending_href = None

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False
        elif tag in ("b", "strong"):
            self.parts.append("**")
        elif tag in ("i", "em"):
            self.parts.append("_")
        elif tag == "p":
            self.parts.append("\n\n")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.parts.append("\n")
        elif tag == "a":
            href = getattr(self, "_pending_href", "") or ""
            self.parts.append(f"]({href})")
            self._pending_href = None

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)

    def result(self):
        text = "".join(self.parts)
        # collapse excess blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # fix bold/italic markers that wrap only whitespace
        text = re.sub(r"\*\*\s*\*\*", "", text)
        text = re.sub(r"_\s*_", "", text)
        # decode HTML entities
        text = text.replace("&ndash;", "–").replace("&mdash;", "—")
        text = text.replace("&nbsp;", " ").replace("&amp;", "&")
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&laquo;", "«").replace("&raquo;", "»")
        text = text.replace("&rsquo;", "'").replace("&lsquo;", "'")
        text = text.replace("&ldquo;", """).replace("&rdquo;", """)
        text = text.replace("&hellip;", "…").replace("&copy;", "©")
        return text.strip()


def html_to_md(html: str) -> str:
    if not html:
        return ""
    parser = _HtmlToMd()
    parser.feed(html)
    return parser.result()


# ---------------------------------------------------------------------------
# Field extraction helpers
# ---------------------------------------------------------------------------

def fv(obj, *keys):
    """Extract .value from a nested dict path, returning str or None."""
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    if isinstance(cur, dict):
        return cur.get("value")
    return cur


def img(path: str) -> str:
    """Prepend IMAGE_PREFIX to relative paths."""
    if not path:
        return ""
    if path.startswith("http"):
        return path
    return IMAGE_PREFIX + path


def image_line(src: str, alt: str = "", legend: str = "") -> list[str]:
    lines = []
    url = img(src)
    if url:
        lines.append(f"![{alt or ''}]({url})")
        if legend:
            leg = html_to_md(legend)
            if leg:
                lines.append(f"*{leg}*")
        lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Component renderers  (return list[str])
# ---------------------------------------------------------------------------

def render_cover(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    subtitle = fv(f, "subtitle", "value") or fv(f, "subtitle") or ""
    description = fv(f, "description", "value") or fv(f, "description") or ""
    src = fv(f, "backgroundLandscape_src", "value") or fv(f, "backgroundLandscape_src") or ""
    alt = fv(f, "backgroundLandscape_alt", "value") or fv(f, "backgroundLandscape_alt") or ""
    if src:
        lines += image_line(src, alt or title)
    if title:
        lines += [f"# {html_to_md(title)}", ""]
    if subtitle:
        lines += [f"## {html_to_md(subtitle)}", ""]
    if description:
        lines += [html_to_md(description), ""]
    return lines


def render_cover_image(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    subtitle = fv(f, "subtitle", "value") or fv(f, "subtitle") or ""
    src = fv(f, "landscapeImage_src", "value") or fv(f, "landscapeImage_src") or fv(f, "poster_src", "value") or fv(f, "poster_src") or ""
    alt = fv(f, "landscapeImage_alt", "value") or fv(f, "landscapeImage_alt") or ""
    if src:
        lines += image_line(src, alt or title)
    if title:
        lines += [f"# {html_to_md(title)}", ""]
    if subtitle:
        lines += [f"### {html_to_md(subtitle)}", ""]
    return lines


def render_image_text_background(f):
    lines = []
    author = fv(f, "author", "value") or fv(f, "author") or ""
    bg_src = fv(f, "background_src", "value") or fv(f, "background_src") or ""
    img_src = fv(f, "image_src", "value") or fv(f, "image_src") or ""
    legend = fv(f, "legend", "value") or fv(f, "legend") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    if author:
        lines += [f"*by {html_to_md(author)}*", ""]
    if bg_src:
        lines += image_line(bg_src)
    if img_src:
        lines += image_line(img_src, legend=legend)
    elif legend:
        lines += [f"*{html_to_md(legend)}*", ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_paragraph(f):
    text = fv(f, "text", "value") or fv(f, "text") or ""
    if text:
        return [html_to_md(text), ""]
    return []


def render_simple_text(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    if title:
        lines += [f"### {html_to_md(title)}", ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_simple_image(f):
    src = fv(f, "imageSrc_src", "value") or fv(f, "imageSrc_src") or ""
    mob = fv(f, "imageMobile_src", "value") or fv(f, "imageMobile_src") or ""
    alt = fv(f, "imageSrc_alt", "value") or fv(f, "imageSrc_alt") or ""
    legend = fv(f, "legend", "value") or fv(f, "legend") or ""
    use = src or mob
    return image_line(use, alt, legend)


def render_push_thematique(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    suptitle = fv(f, "contentSuptitle", "value") or fv(f, "contentSuptitle") or ""
    ctitle = fv(f, "contentTitle", "value") or fv(f, "contentTitle") or ""
    text = fv(f, "contentText", "value") or fv(f, "contentText") or ""
    src = fv(f, "backgroundImage_src", "value") or fv(f, "backgroundImage_src") or ""
    if title:
        lines += [f"# {html_to_md(title)}", ""]
    if src:
        lines += image_line(src, title)
    if suptitle:
        lines += [f"*{html_to_md(suptitle)}*", ""]
    if ctitle:
        lines += [f"## {html_to_md(ctitle)}", ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_push_hub(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    subtitle = fv(f, "subtitle", "value") or fv(f, "subtitle") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    src = fv(f, "backgroundLandscape_src", "value") or fv(f, "backgroundLandscape_src") or ""
    if src:
        lines += image_line(src, title)
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if subtitle:
        lines += [f"*{html_to_md(subtitle)}*", ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_article_hub(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    subtitle = fv(f, "subtitle", "value") or fv(f, "subtitle") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    src = fv(f, "backgroundLandscape_src", "value") or fv(f, "backgroundLandscape_src") or ""
    link = fv(f, "link", "value") or fv(f, "link") or ""
    anchor = fv(f, "anchorText", "value") or fv(f, "anchorText") or ""
    if src:
        lines += image_line(src, title)
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if subtitle:
        lines += [f"*{html_to_md(subtitle)}*", ""]
    if text:
        lines += [html_to_md(text), ""]
    if link and anchor:
        lines += [f"[{html_to_md(anchor)}]({link})", ""]
    return lines


def render_quote(f):
    text = fv(f, "text", "value") or fv(f, "text") or ""
    author = fv(f, "author", "value") or fv(f, "author") or ""
    lines = []
    if text:
        lines += [f"> {html_to_md(text)}", ""]
    if author:
        lines += [f"> — *{html_to_md(author)}*", ""]
    if lines:
        lines.append("")
    return lines


def render_text_background(f):
    lines = []
    suptitle = fv(f, "suptitle", "value") or fv(f, "suptitle") or ""
    title = fv(f, "title", "value") or fv(f, "title") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    bg = fv(f, "background_src", "value") or fv(f, "background_src") or ""
    img_src = fv(f, "image_src", "value") or fv(f, "image_src") or ""
    if bg:
        lines += image_line(bg)
    if img_src:
        lines += image_line(img_src)
    if suptitle:
        lines += [f"*{html_to_md(suptitle)}*", ""]
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_text_image(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    src = fv(f, "image_src", "value") or fv(f, "image_src") or ""
    if src:
        lines += image_line(src, title)
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_title_text_image(f):
    lines = []
    suptitle = fv(f, "suptitle", "value") or fv(f, "suptitle") or ""
    title = fv(f, "title", "value") or fv(f, "title") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    src = fv(f, "image_src", "value") or fv(f, "image_src") or ""
    link = fv(f, "link", "value") or fv(f, "link") or ""
    label = fv(f, "linkLabel", "value") or fv(f, "linkLabel") or ""
    if src:
        lines += image_line(src, title)
    if suptitle:
        lines += [f"*{html_to_md(suptitle)}*", ""]
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if text:
        lines += [html_to_md(text), ""]
    if link and label:
        lines += [f"[{html_to_md(label)}]({link})", ""]
    return lines


def render_simple_video(f):
    poster = fv(f, "poster_src", "value") or fv(f, "poster_src") or ""
    src = fv(f, "source_src", "value") or fv(f, "source_src") or ""
    lines = []
    if poster:
        lines += image_line(poster, "Video poster")
    if src:
        lines += [f"Video: {img(src)}", ""]
    return lines


def render_direct_link(f):
    label = fv(f, "linkLabel", "value") or fv(f, "linkLabel") or ""
    lines = []
    for key in ("link1", "link2", "link3"):
        link = fv(f, key, "value") or fv(f, key) or ""
        if link and label:
            lines += [f"[{html_to_md(label)}]({link})", ""]
            break
        elif link:
            lines += [f"[{link}]({link})", ""]
    return lines


def render_ext_link(f):
    label = fv(f, "linkLabel", "value") or fv(f, "linkLabel") or ""
    link = fv(f, "link", "value") or fv(f, "link") or ""
    if link:
        return [f"[{html_to_md(label) or link}]({link})", ""]
    return []


def render_grid_contribution(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    highlights = f.get("highlights", {})
    if isinstance(highlights, dict):
        highlights = highlights.get("value", [])
    for item in (highlights or []):
        ifields = item.get("fields", {})
        ititle = fv(ifields, "pageTitle", "value") or fv(ifields, "pageTitle") or ""
        icaption = fv(ifields, "pageCaption", "value") or fv(ifields, "pageCaption") or ""
        ithumb = fv(ifields, "pageThumbnail_src", "value") or fv(ifields, "pageThumbnail_src") or ""
        ilink = fv(ifields, "customLink", "value") or fv(ifields, "customLink") or fv(ifields, "pageSiteSubSection", "value") or ""
        if ithumb:
            lines += image_line(ithumb, ititle)
        if ititle:
            if ilink:
                lines += [f"**[{html_to_md(ititle)}]({ilink})**", ""]
            else:
                lines += [f"**{html_to_md(ititle)}**", ""]
        if icaption:
            lines += [html_to_md(icaption), ""]
    return lines


def render_related_items(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    if title:
        lines += [f"---", "", f"## {html_to_md(title)}", ""]
    items = f.get("relatedItems", {})
    if isinstance(items, dict):
        items = items.get("value", [])
    for item in (items or []):
        ifields = item.get("fields", {})
        ititle = fv(ifields, "pageTitle", "value") or fv(ifields, "pageTitle") or ""
        icaption = fv(ifields, "pageCaption", "value") or fv(ifields, "pageCaption") or ""
        ithumb = fv(ifields, "pageThumbnail_src", "value") or fv(ifields, "pageThumbnail_src") or ""
        subsection = fv(ifields, "pageSiteSubSection", "value") or fv(ifields, "pageSiteSubSection") or ""
        if ithumb:
            lines += image_line(ithumb, ititle)
        if ititle:
            link = f"/{subsection}" if subsection else ""
            if link:
                lines += [f"**[{html_to_md(ititle)}]({link})**", ""]
            else:
                lines += [f"**{html_to_md(ititle)}**", ""]
        if icaption:
            lines += [html_to_md(icaption), ""]
    return lines


def render_intro(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    subtitle = fv(f, "subtitle", "value") or fv(f, "subtitle") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    src = fv(f, "image_src", "value") or fv(f, "image_src") or ""
    if src:
        lines += image_line(src, title)
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if subtitle:
        lines += [html_to_md(subtitle), ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_cover_globe(f):
    lines = []
    title = fv(f, "introTitle", "value") or fv(f, "introTitle") or ""
    suptitle = fv(f, "introSuptitle", "value") or fv(f, "introSuptitle") or ""
    b2title = fv(f, "bloc2Title", "value") or fv(f, "bloc2Title") or ""
    b2text = fv(f, "bloc2Text", "value") or fv(f, "bloc2Text") or ""
    if suptitle:
        lines += [f"*{html_to_md(suptitle)}*", ""]
    if title:
        lines += [f"# {html_to_md(title)}", ""]
    if b2title:
        lines += [f"## {html_to_md(b2title)}", ""]
    if b2text:
        lines += [html_to_md(b2text), ""]
    return lines


def render_push_program(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    src = fv(f, "backgroundLandscape_src", "value") or fv(f, "backgroundLandscape_src") or ""
    link = fv(f, "link", "value") or fv(f, "link") or ""
    label = fv(f, "anchorText", "value") or fv(f, "anchorText") or ""
    if src:
        lines += image_line(src, title)
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if text:
        lines += [html_to_md(text), ""]
    if link and label:
        lines += [f"[{html_to_md(label)}]({link})", ""]
    return lines


def render_infographic(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    src = fv(f, "imageSrc_src", "value") or fv(f, "imageSrc_src") or ""
    alt = fv(f, "imageSrc_alt", "value") or fv(f, "imageSrc_alt") or ""
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if src:
        lines += image_line(src, alt or title)
    return lines


def render_stamp(f):
    lines = []
    text = fv(f, "text", "value") or fv(f, "text") or ""
    if text:
        lines += [f"> {html_to_md(text)}", ""]
    return lines


def render_location(f):
    lines = []
    country = fv(f, "country", "value") or fv(f, "country") or ""
    city = fv(f, "city", "value") or fv(f, "city") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    if country or city:
        loc = ", ".join(x for x in [city, country] if x)
        lines += [f"**Location:** {loc}", ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_facts(f):
    lines = []
    src = fv(f, "backgroundLandscape_src", "value") or fv(f, "backgroundLandscape_src") or ""
    if src:
        lines += image_line(src)
    return lines


def render_text_section(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_parallaxed_section(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    src = fv(f, "backgroundLandscape_src", "value") or fv(f, "backgroundLandscape_src") or ""
    if src:
        lines += image_line(src, title)
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_video_autoplay(f):
    poster = fv(f, "poster_src", "value") or fv(f, "poster_src") or ""
    title = fv(f, "title", "value") or fv(f, "title") or ""
    if poster:
        return image_line(poster, title or "Video")
    return []


def render_hub_background_quote(f):
    text = fv(f, "text", "value") or fv(f, "text") or ""
    src = fv(f, "backgroundLandscape_src", "value") or fv(f, "backgroundLandscape_src") or ""
    lines = []
    if src:
        lines += image_line(src)
    if text:
        lines += [f"> {html_to_md(text)}", ""]
    return lines


def render_image_reveal(f):
    lines = []
    src1 = fv(f, "image1_src", "value") or fv(f, "image1_src") or ""
    src2 = fv(f, "image2_src", "value") or fv(f, "image2_src") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    if src1:
        lines += image_line(src1)
    if src2:
        lines += image_line(src2)
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_text_video_gradient(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    text = fv(f, "text", "value") or fv(f, "text") or ""
    poster = fv(f, "poster_src", "value") or fv(f, "poster_src") or ""
    if poster:
        lines += image_line(poster, title)
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    if text:
        lines += [html_to_md(text), ""]
    return lines


def render_rmp_grid(f):
    lines = []
    title = fv(f, "title", "value") or fv(f, "title") or ""
    if title:
        lines += [f"## {html_to_md(title)}", ""]
    items = f.get("items", {})
    if isinstance(items, dict):
        items = items.get("value", [])
    for item in (items or []):
        ifields = item.get("fields", {})
        ititle = fv(ifields, "title", "value") or fv(ifields, "title") or ""
        itext = fv(ifields, "text", "value") or fv(ifields, "text") or ""
        isrc = fv(ifields, "image_src", "value") or fv(ifields, "image_src") or ""
        if isrc:
            lines += image_line(isrc, ititle)
        if ititle:
            lines += [f"**{html_to_md(ititle)}**", ""]
        if itext:
            lines += [html_to_md(itext), ""]
    return lines


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

RENDERERS = {
    "Cover": render_cover,
    "CoverImage": render_cover_image,
    "CoverParallax": render_cover,
    "CoverVideo": render_cover,
    "CoverVideoButton": render_cover,
    "CoverVideoGrid": render_cover,
    "CoverVideoMasked": render_cover,
    "CoverVideoScroll": render_cover,
    "ImageTextBackground": render_image_text_background,
    "Paragraph": render_paragraph,
    "SimpleText": render_simple_text,
    "SimpleImage": render_simple_image,
    "SimpleVideo": render_simple_video,
    "VideoAutoplay": render_video_autoplay,
    "PushThematique": render_push_thematique,
    "PushHub": render_push_hub,
    "PushProgram": render_push_program,
    "ArticleHub": render_article_hub,
    "ArticleHubPush": render_article_hub,
    "Quote": render_quote,
    "HubBackgroundQuote": render_hub_background_quote,
    "TextBackground": render_text_background,
    "TextImage": render_text_image,
    "TextSection": render_text_section,
    "TitleTextImage": render_title_text_image,
    "ParallaxedSection": render_parallaxed_section,
    "DirectLink": render_direct_link,
    "ExtLink": render_ext_link,
    "GridContribution": render_grid_contribution,
    "RelatedItems": render_related_items,
    "Infographic": render_infographic,
    "Stamp": render_stamp,
    "Location": render_location,
    "Facts": render_facts,
    "CoverGlobe": render_cover_globe,
    "IntroductionMP": render_intro,
    "ImageReveal": render_image_reveal,
    "TextVideoGradient": render_text_video_gradient,
    "RmpGrid": render_rmp_grid,
    # Ignored / no content to extract
    "Roller": lambda f: [],
    "RollerHome": lambda f: [],
    "Stories": lambda f: [],
    "Tags": lambda f: [],
    "Sharing": lambda f: [],
    "StickyBar": lambda f: [],
    "VideoPushSlideshow": lambda f: [],
    "VideoPlaylist": lambda f: [],
    "VideoPlaylistRoller": lambda f: [],
    "Search": lambda f: [],
    "LatestPodcast": lambda f: [],
    "PodcastPlaylist": lambda f: [],
    "ArticlePodcast": lambda f: [],
    "HansWilsdorfPage": lambda f: [],
    "Fact": lambda f: [],
}


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------

def get_field_value(field_obj):
    if isinstance(field_obj, dict):
        if "value" in field_obj:
            return field_obj["value"]
        if "fields" in field_obj:
            name_field = field_obj["fields"].get("name", {})
            if isinstance(name_field, dict):
                return name_field.get("value", "")
    return None


def convert_json_to_md(json_file: Path) -> str | None:
    try:
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  Error reading {json_file}: {e}", file=sys.stderr)
        return None

    try:
        route = data["sitecore"]["route"]
    except (KeyError, TypeError) as e:
        print(f"  No sitecore.route in {json_file}: {e}", file=sys.stderr)
        return None

    fields = route.get("fields", {})

    # --- frontmatter ---
    page_title = get_field_value(fields.get("pageTitle")) or ""
    wa_title = get_field_value(fields.get("WaPageTitle")) or ""
    meta_desc = get_field_value(fields.get("metadescription")) or ""
    page_type = ""
    pt = fields.get("pageType", {})
    if isinstance(pt, dict) and "fields" in pt:
        page_type = get_field_value(pt["fields"].get("name")) or ""

    url_path = str(json_file.relative_to(SOURCE_DIR)).replace("\\", "/").replace(".json", "")
    page_url = f"https://www.rolex.org/en/{url_path}" if url_path != "index" else "https://www.rolex.org/en/"

    fm_title = wa_title or html_to_md(page_title)

    md_lines = ["---"]
    if fm_title:
        safe = fm_title.replace('"', '\\"')
        md_lines.append(f'title: "{safe}"')
    if meta_desc:
        safe_desc = html_to_md(meta_desc).replace('"', '\\"')
        md_lines.append(f'description: "{safe_desc}"')
    if page_type:
        md_lines.append(f"type: {page_type}")
    md_lines.append(f'url: "{page_url}"')
    md_lines += ["---", ""]

    # --- page-level thumbnail ---
    thumb = get_field_value(fields.get("pageThumbnail_src"))
    thumb_alt = get_field_value(fields.get("pageThumbnail_alt")) or fm_title
    preview_img = get_field_value(fields.get("previewImage_src")) or get_field_value(fields.get("previewImageCustom_src"))

    # --- component content ---
    try:
        layout = route["placeholders"]["layout-placeholder"][0]
        jss_main = layout["placeholders"].get("jss-main", [])
    except (KeyError, IndexError, TypeError):
        jss_main = []

    component_lines = []
    has_title_component = False

    for component in jss_main:
        name = component.get("componentName", "")
        comp_fields = component.get("fields", {})

        # Flatten field values: each field may be {value: X} or a raw value
        flat = {}
        for k, v in comp_fields.items():
            flat[k] = v

        renderer = RENDERERS.get(name)
        if renderer:
            rendered = renderer(flat)
        else:
            # Generic fallback: extract any text/image fields
            rendered = []
            for k, v in flat.items():
                val = get_field_value(v) if isinstance(v, dict) else v
                if isinstance(val, str) and val.strip():
                    if k.endswith("_src"):
                        rendered += image_line(val)
                    elif k in ("text", "title", "description", "content"):
                        md = html_to_md(val)
                        if md:
                            rendered += [md, ""]

        if rendered:
            # Check if a heading was produced (h1 signals cover/title component)
            if any(line.startswith("# ") for line in rendered):
                has_title_component = True
            component_lines.extend(rendered)

    # If no component produced an h1, add the page title manually
    if not has_title_component and fm_title:
        component_lines = [f"# {fm_title}", ""] + component_lines

    # Add thumbnail if no image appeared yet
    first_img_idx = next((i for i, l in enumerate(component_lines) if l.startswith("![")), -1)
    if first_img_idx == -1:
        img_src = thumb or preview_img
        if img_src:
            insert_at = next((i for i, l in enumerate(component_lines) if l.startswith("# ")), 0)
            component_lines[insert_at:insert_at] = image_line(img_src, thumb_alt)

    md_lines.extend(component_lines)

    # Clean trailing blank lines
    while md_lines and md_lines[-1] == "":
        md_lines.pop()
    md_lines.append("")

    return "\n".join(md_lines)


def main():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    json_files = sorted(SOURCE_DIR.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files")

    converted = failed = 0
    for json_file in json_files:
        rel = json_file.relative_to(SOURCE_DIR)
        md_path = TARGET_DIR / rel.with_suffix(".md")
        md_path.parent.mkdir(parents=True, exist_ok=True)

        md_content = convert_json_to_md(json_file)
        if md_content is None:
            failed += 1
            continue

        try:
            md_path.write_text(md_content, encoding="utf-8")
            print(f"  ✓ {rel.with_suffix('.md')}")
            converted += 1
        except Exception as e:
            print(f"  ✗ {rel}: {e}", file=sys.stderr)
            failed += 1

    print(f"\nDone: {converted} converted, {failed} failed")


if __name__ == "__main__":
    main()
