"""
平台登录助手 (Platform Login Helper)
==================================
用于手动登录知乎和微信公众号，保存 Cookies 以便自动化脚本使用。

使用方法：
    python scripts/login_platforms.py --platform zhihu
    python scripts/login_platforms.py --platform wechat

它会启动一个有头浏览器 (Headful Browser)，请在浏览器中扫码登录。
登录成功后，脚本会自动保存 `cookies.json` 到 `config/` 目录。
"""

import os
import time
import json
import argparse
from playwright.sync_api import sync_playwright

# ─── 配置 ───
COOKIES_DIR = "config/cookies"
os.makedirs(COOKIES_DIR, exist_ok=True)

def login_and_save_cookies(platform: str):
    """启动浏览器手动登录并保存 Cookie"""
    
    urls = {
        "zhihu": "https://zhuanlan.zhihu.com/write",
        "wechat": "https://mp.weixin.qq.com/"
    }
    
    if platform not in urls:
        print(f"❌ 不支持的平台: {platform}")
        return

    print(f"🚀 启动浏览器进行 {platform} 登录...")
    print("⚠️ 请在浏览器窗口中完成扫码/密码登录。登录成功后，脚本会自动检测并保存。")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # 必须有头
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(urls[platform])
        
        # 轮询检测登录状态
        # 知乎: 检查是否包含 'Write' 界面元素
        # 微信: 检查是否进入后台首页
        
        max_wait = 300 # 5分钟有效期
        start_time = time.time()
        
        logged_in = False
        
        while time.time() - start_time < max_wait:
            try:
                if platform == "zhihu":
                    # 检查是否跳转到编辑器或专栏页，且没有登录弹窗
                    if "zhuanlan.zhihu.com/write" in page.url and not page.query_selector(".SignFlow"):
                        logged_in = True
                elif platform == "wechat":
                    # 检查 URL 是否包含 token 参数 (公众号后台特征)
                    if "mp.weixin.qq.com/cgi-bin/home" in page.url and "token=" in page.url:
                        logged_in = True
                
                if logged_in:
                    print("✅ 检测到登录成功！")
                    break
                    
                time.sleep(1)
            except Exception:
                pass
        
        if logged_in:
            # 保存 Cookies
            cookies = context.cookies()
            cookie_file = os.path.join(COOKIES_DIR, f"{platform}.json")
            with open(cookie_file, "w") as f:
                json.dump(cookies, f)
            print(f"💾 Cookies 已保存至: {cookie_file}")
            
            # 这里的 Storage State 更完整 (包含 localStorage)
            state_file = os.path.join(COOKIES_DIR, f"{platform}_state.json")
            context.storage_state(path=state_file)
            print(f"💾 Storage State 已保存至: {state_file}")
            
        else:
            print("❌ 登录超时或失败。")
            
        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["zhihu", "wechat"], required=True, help="目标平台")
    args = parser.parse_args()
    
    login_and_save_cookies(args.platform)
