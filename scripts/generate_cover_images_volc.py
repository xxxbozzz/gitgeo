#!/usr/bin/env python3
"""
Batch-generate article cover images with Volcengine CV image generation.

Design goals:
1. Do not modify exported HTML files.
2. Generate a sibling image next to each `slug.html`, defaulting to `slug.jpg`.
3. Keep all credentials in environment variables only.
4. Default to missing-only generation so reruns are safe.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from volcenginesdkcore.api_client import ApiClient
from volcenginesdkcore.configuration import Configuration
from volcenginesdkcv20240606 import CV20240606Api, HighAesGeneralV20LRequest


DEFAULT_HTML_DIR = "output/website_sync"
DEFAULT_EXT = "jpg"
DEFAULT_REQ_KEY = "high_aes_general_v20_L"
DEFAULT_MODEL_VERSION = "general_v2.0_L"
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
DEFAULT_SCALE = 3.5
DEFAULT_DDIM_STEPS = 25
DEFAULT_SLEEP_SECONDS = 1.0


@dataclass
class HtmlArticle:
    html_path: Path
    image_path: Path
    slug: str
    title: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate same-name cover images for exported article HTML files using Volcengine."
    )
    parser.add_argument(
        "--html-dir",
        default=DEFAULT_HTML_DIR,
        help=f"Directory containing exported HTML files. Default: {DEFAULT_HTML_DIR}",
    )
    parser.add_argument(
        "--ext",
        default=DEFAULT_EXT,
        choices=("jpg", "jpeg", "png", "webp"),
        help="Image extension to save. Default: jpg",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process the first N files after filtering. 0 means no limit.",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=[],
        help="Only generate these basenames/slugs, for example slug-a slug-b.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing images instead of skipping them.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned operations without calling the API.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=DEFAULT_SLEEP_SECONDS,
        help=f"Seconds to wait between requests. Default: {DEFAULT_SLEEP_SECONDS}",
    )
    parser.add_argument(
        "--style-preset",
        default="pcb-tech-cover",
        choices=("pcb-tech-cover", "micrograph", "factory-process", "material-engineering"),
        help="Prompt template preset. Default: pcb-tech-cover",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"Output width. Default: {DEFAULT_WIDTH}",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help=f"Output height. Default: {DEFAULT_HEIGHT}",
    )
    return parser.parse_args()


def get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def build_api() -> CV20240606Api:
    config = Configuration()
    config.ak = get_required_env("VOLC_ACCESS_KEY_ID")
    config.sk = get_required_env("VOLC_SECRET_ACCESS_KEY")

    region = os.getenv("VOLC_REGION", "").strip()
    if region:
        config.region = region

    host = os.getenv("VOLC_CV_HOST", "").strip()
    if host:
        config.host = host

    return CV20240606Api(ApiClient(config))


def extract_title(html_text: str, fallback_slug: str) -> str:
    title_match = re.search(r"<title>\s*(.*?)\s*</title>", html_text, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = html.unescape(title_match.group(1))
        title = re.sub(r"\s*-\s*深亚电子PCB技术百科\s*$", "", title).strip()
        if title:
            return title

    h1_match = re.search(r"<h1>\s*(.*?)\s*</h1>", html_text, re.IGNORECASE | re.DOTALL)
    if h1_match:
        title = html.unescape(re.sub(r"<[^>]+>", "", h1_match.group(1))).strip()
        if title:
            return title

    return fallback_slug.replace("-", " ").strip()


def iter_articles(html_dir: Path, image_ext: str, overwrite: bool, only: set[str]) -> list[HtmlArticle]:
    items: list[HtmlArticle] = []
    for html_path in sorted(html_dir.glob("*.html")):
        slug = html_path.stem
        if only and slug not in only:
            continue

        image_path = html_path.with_suffix(f".{image_ext}")
        if image_path.exists() and not overwrite:
            continue

        html_text = html_path.read_text(encoding="utf-8", errors="ignore")
        title = extract_title(html_text, slug)
        items.append(
            HtmlArticle(
                html_path=html_path,
                image_path=image_path,
                slug=slug,
                title=title,
            )
        )
    return items


def slug_keywords(slug: str) -> str:
    parts = [part for part in slug.replace("_", "-").split("-") if part]
    if not parts:
        return ""
    return ", ".join(parts[:10])


def build_prompt(article: HtmlArticle, preset: str) -> str:
    keyword_hint = slug_keywords(article.slug)

    base = (
        f"为一篇 PCB 技术文章生成官网列表封面图。"
        f" 主题标题：{article.title}。"
        f" 关键词参考：{keyword_hint or article.title}。"
        " 横版 16:9 构图，适合作为技术文章列表封面。"
        " 不要文字，不要 logo，不要水印，不要人物特写，不要 UI 截图。"
        " 画面需要干净、专业、工程导向，适合 B2B 工业技术网站。"
    )

    preset_map = {
        "pcb-tech-cover": (
            " 主体突出 PCB 板、走线、过孔、层压结构、材料纹理或相关工程装置。"
            " 整体风格为深蓝与青色科技工业风，克制、高级、真实感强。"
        ),
        "micrograph": (
            " 画面偏微观视角，突出铜箔、镀层、孔壁、纤维、树脂或失效分析显微结构。"
            " 整体风格为高精度工业显微摄影质感，冷色调。"
        ),
        "factory-process": (
            " 画面偏制造工艺现场，突出曝光、钻孔、电镀、压合、AOI、测试等产线环节。"
            " 整体风格为现代化电子制造工厂纪录片质感，工业蓝灰色调。"
        ),
        "material-engineering": (
            " 画面偏材料与工程应用，突出高频板材、绝缘介质、铜厚、热管理与可靠性主题。"
            " 整体风格为半写实工业概念图，信息明确但不花哨。"
        ),
    }

    return base + preset_map[preset]


def generate_image(
    api: CV20240606Api,
    *,
    prompt: str,
    width: int,
    height: int,
) -> str:
    request = HighAesGeneralV20LRequest(
        prompt=prompt,
        req_key=os.getenv("VOLC_CV_REQ_KEY", DEFAULT_REQ_KEY),
        model_version=os.getenv("VOLC_CV_MODEL_VERSION", DEFAULT_MODEL_VERSION),
        width=width,
        height=height,
        return_url=True,
        scale=float(os.getenv("VOLC_CV_SCALE", str(DEFAULT_SCALE))),
        ddim_steps=int(os.getenv("VOLC_CV_DDIM_STEPS", str(DEFAULT_DDIM_STEPS))),
    )
    response = api.high_aes_general_v20_l(request)
    data = getattr(response, "data", None)
    image_urls = getattr(data, "image_urls", None) or []
    if not image_urls:
        raise RuntimeError(f"Volcengine returned no image URLs: {response.to_dict()}")
    return str(image_urls[0])


def download_file(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as response:
        content = response.read()
    output_path.write_bytes(content)


def print_plan(articles: Iterable[HtmlArticle], preset: str) -> None:
    for item in articles:
        print(f"[PLAN] {item.html_path.name} -> {item.image_path.name}")
        print(f"       title: {item.title}")
        print(f"       preset: {preset}")


def main() -> int:
    args = parse_args()
    html_dir = Path(args.html_dir).expanduser().resolve()
    if not html_dir.exists():
        raise SystemExit(f"HTML directory does not exist: {html_dir}")

    only = {value.strip() for value in args.only if value.strip()}
    articles = iter_articles(html_dir, args.ext, args.overwrite, only)
    if args.limit and args.limit > 0:
        articles = articles[: args.limit]

    if not articles:
        print("No matching HTML files need cover generation.")
        return 0

    print(f"HTML dir: {html_dir}")
    print(f"Found {len(articles)} article(s) to process.")
    print_plan(articles, args.style_preset)

    if args.dry_run:
        return 0

    api = build_api()
    failures = 0

    for index, article in enumerate(articles, start=1):
        prompt = build_prompt(article, args.style_preset)
        print(f"[{index}/{len(articles)}] Generating cover for {article.slug}")
        try:
            image_url = generate_image(
                api,
                prompt=prompt,
                width=args.width,
                height=args.height,
            )
            download_file(image_url, article.image_path)
            print(f"  saved -> {article.image_path}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  failed -> {article.slug}: {exc}", file=sys.stderr)
        time.sleep(max(args.sleep, 0))

    if failures:
        print(f"Completed with {failures} failure(s).", file=sys.stderr)
        return 1

    print("All cover images generated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
