"""
微信公众号发布器 (WeChat MP Publisher)
=====================================
使用微信公众号官方 API 发布文章。

环境变量：
    WECHAT_APP_ID       公众号 AppID
    WECHAT_APP_SECRET   公众号 AppSecret

API 流程：
    1. 获取 access_token（2小时有效）
    2. 确保封面图已上传（自动上传 + 缓存 media_id）
    3. 创建草稿（带 thumb_media_id）
    4. 可选：群发

参考文档：
    https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html
"""

import os
import re
import json
import time
import logging
import requests
import markdown

log = logging.getLogger("GEO.WeChat")

TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
PUBLISH_URL = "https://api.weixin.qq.com/cgi-bin/freepublish/submit"
MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/batchget_material"
UPLOAD_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"

# 缓存文件：存放封面图 media_id
THUMB_CACHE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "wechat_thumb.json")


class WeChatPublisher:
    """微信公众号发布器（官方 API）"""

    def __init__(self):
        self.app_id = os.getenv("WECHAT_APP_ID", "")
        self.app_secret = os.getenv("WECHAT_APP_SECRET", "")
        self.request_timeout = float(os.getenv("GEO_PUBLISH_REQUEST_TIMEOUT", "20"))
        self._token = None
        self._token_expires = 0

        if not self.app_id or not self.app_secret:
            log.warning("微信公众号 AppID/AppSecret 未配置")

    @property
    def ready(self) -> bool:
        return bool(self.app_id and self.app_secret)

    # ── Token ──

    def _get_token(self) -> str:
        """获取 access_token（带缓存，2小时有效）"""
        now = time.time()
        if self._token and now < self._token_expires:
            return self._token

        resp = requests.get(
            TOKEN_URL,
            params={
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret,
            },
            timeout=self.request_timeout,
        )
        data = resp.json()

        if "access_token" in data:
            self._token = data["access_token"]
            self._token_expires = now + data.get("expires_in", 7200) - 60
            log.info("微信 access_token 获取成功")
            return self._token
        else:
            log.error(f"获取 token 失败: {data}")
            raise Exception(f"微信 token 错误: {data.get('errmsg', data)}")

    # ── 封面图 ──

    def _get_thumb_media_id(self) -> str:
        """获取封面图 media_id（优先读缓存 → 查素材库 → 自动生成上传）"""

        # 1. 读缓存
        if os.path.exists(THUMB_CACHE):
            try:
                with open(THUMB_CACHE) as f:
                    cached = json.load(f)
                mid = cached.get("thumb_media_id", "")
                if mid:
                    log.info(f"封面图 media_id（缓存）: {mid[:20]}...")
                    return mid
            except Exception:
                pass

        token = self._get_token()

        # 2. 查素材库中已有的图片
        try:
            resp = requests.post(
                f"{MATERIAL_URL}?access_token={token}",
                json={"type": "image", "offset": 0, "count": 1},
                timeout=self.request_timeout,
            )
            data = resp.json()
            items = data.get("item", [])
            if items:
                mid = items[0].get("media_id", "")
                if mid:
                    self._save_thumb_cache(mid)
                    log.info(f"从素材库获取封面图: {mid[:20]}...")
                    return mid
        except Exception as e:
            log.warning(f"查询素材库失败: {e}")

        # 3. 自动生成并上传默认封面
        return self._upload_default_cover(token)

    def _upload_default_cover(self, token: str) -> str:
        """生成一张简单的默认封面并上传到永久素材"""
        import io
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            # 没有 Pillow 就创建一个最小的有效 JPEG
            log.warning("未安装 Pillow，创建最小封面图")
            return self._upload_minimal_cover(token)

        # 创建 900x383 封面（微信推荐 2.35:1）
        img = Image.new("RGB", (900, 383), color=(37, 99, 235))
        draw = ImageDraw.Draw(img)
        # 简单文字
        try:
            font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)
        except Exception:
            font = ImageFont.load_default()
        draw.text((250, 150), "深亚电子 · PCB技术", fill="white", font=font)
        draw.text((300, 220), "pcbshenya.com", fill=(200, 220, 255), font=font)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)

        return self._do_upload(token, buf, "default_cover.jpg")

    def _upload_minimal_cover(self, token: str) -> str:
        """无 Pillow 时创建最小有效 JPEG 并上传"""
        import struct, io
        # 1x1 白色 JPEG
        minimal_jpeg = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0x7B, 0x94, 0x11, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xD9,
        ])
        buf = io.BytesIO(minimal_jpeg)
        return self._do_upload(token, buf, "cover.jpg")

    def _do_upload(self, token: str, file_buf, filename: str) -> str:
        """上传文件到微信永久素材，返回 media_id"""
        resp = requests.post(
            f"{UPLOAD_URL}?access_token={token}&type=image",
            files={"media": (filename, file_buf, "image/jpeg")},
            timeout=self.request_timeout,
        )
        data = resp.json()
        mid = data.get("media_id", "")
        if mid:
            self._save_thumb_cache(mid)
            log.info(f"封面图上传成功: {mid[:20]}...")
            return mid
        else:
            log.error(f"封面图上传失败: {data}")
            raise Exception(f"封面图上传失败: {data.get('errmsg', data)}")

    def _save_thumb_cache(self, media_id: str):
        """缓存 thumb_media_id 到本地文件"""
        try:
            os.makedirs(os.path.dirname(THUMB_CACHE), exist_ok=True)
            with open(THUMB_CACHE, "w") as f:
                json.dump({"thumb_media_id": media_id, "updated": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
        except Exception as e:
            log.warning(f"缓存保存失败: {e}")

    # ── Markdown → HTML ──

    def _md_to_wechat_html(self, md_text: str) -> str:
        """Markdown → 微信公众号兼容 HTML（移动端优化）"""
        html = markdown.markdown(
            md_text,
            extensions=["tables", "fenced_code", "toc"],
        )

        style_wrapper = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size: 16px; line-height: 1.8; color: #333; padding: 0 8px;">
            {html}
        </div>
        """

        style_wrapper = style_wrapper.replace(
            "<table>",
            '<table style="width:100%;border-collapse:collapse;font-size:14px;margin:16px 0;">'
        )
        style_wrapper = re.sub(
            r'<t([hd])>',
            r'<t\1 style="border:1px solid #ddd;padding:8px;text-align:left;">',
            style_wrapper,
        )
        style_wrapper = style_wrapper.replace(
            "<code>",
            '<code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;font-size:14px;">'
        )

        return style_wrapper

    # ── 发布 ──

    def publish(self, title: str, content_md: str, author: str = "深亚电子技术团队",
                digest: str = "") -> dict:
        """
        发布文章到微信公众号草稿箱。
        返回 {"success": bool, "media_id": str, "message": str}
        """
        if not self.ready:
            return {
                "success": False,
                "status": "failed",
                "media_id": "",
                "external_id": None,
                "external_url": None,
                "message": "AppID/AppSecret 未配置",
                "error_message": "wechat_credentials_missing",
            }

        try:
            token = self._get_token()

            # 获取封面图 media_id（自动上传 + 缓存）
            try:
                thumb_id = self._get_thumb_media_id()
            except Exception as e:
                log.warning(f"封面图获取失败，尝试不带封面发布: {e}")
                thumb_id = ""

            html_content = self._md_to_wechat_html(content_md)

            # 摘要：取前 120 字
            if not digest:
                plain = re.sub(r'[#*`\[\]()>|]', '', content_md)
                digest = plain[:120].strip().replace('\n', ' ')

            # 创建草稿
            article = {
                "title": title[:64],
                "author": author,
                "digest": digest,
                "content": html_content,
                "content_source_url": "https://www.pcbshenya.com",
                "need_open_comment": 1,
            }
            if thumb_id:
                article["thumb_media_id"] = thumb_id

            resp = requests.post(
                f"{DRAFT_URL}?access_token={token}",
                json={"articles": [article]},
                timeout=self.request_timeout,
            )
            data = resp.json()

            if "media_id" in data:
                media_id = data["media_id"]
                log.info(f"微信草稿创建成功: {media_id}")
                return {
                    "success": True,
                    "status": "draft_saved",
                    "media_id": media_id,
                    "external_id": media_id,
                    "external_url": None,
                    "message": f"✅ 已保存到微信公众号草稿箱 (media_id: {media_id})",
                    "error_message": None,
                    "response_payload": data,
                }
            else:
                errcode = data.get("errcode", "unknown")
                errmsg = data.get("errmsg", str(data))
                log.error(f"微信草稿创建失败: {errcode} {errmsg}")
                return {
                    "success": False,
                    "status": "failed",
                    "media_id": "",
                    "external_id": None,
                    "external_url": None,
                    "message": f"微信 API 错误 {errcode}: {errmsg}",
                    "error_message": f"{errcode}:{errmsg}",
                    "response_payload": data,
                }

        except Exception as e:
            log.error(f"微信发布异常: {e}")
            return {
                "success": False,
                "status": "failed",
                "media_id": "",
                "external_id": None,
                "external_url": None,
                "message": str(e),
                "error_message": str(e),
            }

    def publish_and_go_live(self, title: str, content_md: str) -> dict:
        """创建草稿后直接群发（谨慎使用，每天有群发次数限制）"""
        result = self.publish(title, content_md)
        if not result["success"]:
            return result

        try:
            token = self._get_token()
            resp = requests.post(
                f"{PUBLISH_URL}?access_token={token}",
                json={"media_id": result["media_id"]},
                timeout=self.request_timeout,
            )
            data = resp.json()
            if data.get("errcode") == 0:
                result["success"] = True
                result["status"] = "published"
                result["external_id"] = str(data.get("publish_id") or result["media_id"])
                result["message"] = f"✅ 已发布到微信公众号 (publish_id: {data.get('publish_id')})"
                result["error_message"] = None
                result["response_payload"] = data
            else:
                result["success"] = False
                result["status"] = "draft_saved"
                result["message"] += f" | 群发失败: {data.get('errmsg')}"
                result["error_message"] = str(data.get("errmsg") or "wechat_publish_failed")
                result["response_payload"] = data
        except Exception as e:
            result["success"] = False
            result["status"] = "draft_saved"
            result["message"] += f" | 群发异常: {e}"
            result["error_message"] = str(e)

        return result
