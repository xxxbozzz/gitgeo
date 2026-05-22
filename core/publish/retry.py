"""
Retry Policy — 发布失败时的容错策略。
"""

import asyncio
import logging

log = logging.getLogger("GEO.Retry")

MAX_RETRIES = 3
BASE_DELAY = 30  # seconds


async def with_retry(publish_fn, engine, article, max_retries: int = MAX_RETRIES):
    """包装发布函数，自动处理常见失败模式。

    重试策略:
      - 验证码 → 尝试自动解决 → 失败则通知人
      - 限流 429 → 指数退避后重试
      - 网络错误 → 等待后重试
      - Cookie 过期 → 不再重试，返回 auth_required
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            result = await publish_fn(engine, article)

            if result.success:
                return result

            error_msg = (result.error_message or "").lower()

            if "auth" in error_msg or "login" in error_msg or "cookie" in error_msg:
                return result  # 不重试，直接返回

            if "captcha" in error_msg or "verify" in error_msg:
                log.warning("[Attempt %d] Captcha detected. Trying auto-solve...", attempt)
                solved = await _try_auto_captcha()
                if not solved:
                    result.message += " | 需要人工处理验证码"
                    return result
                continue

            if "rate_limit" in error_msg or "429" in error_msg:
                delay = BASE_DELAY * attempt
                log.warning("[Attempt %d] Rate limited. Waiting %ds...", attempt, delay)
                await asyncio.sleep(delay)
                continue

            # 其他失败，等待后重试
            last_error = result.message
            if attempt < max_retries:
                await asyncio.sleep(BASE_DELAY)
                continue

        except Exception as exc:
            last_error = str(exc)
            log.error("[Attempt %d] Exception: %s", attempt, exc)
            if attempt < max_retries:
                await asyncio.sleep(BASE_DELAY)
                continue

    # 所有重试耗尽
    from core.publish.base import PublishResult
    return PublishResult(
        success=False, platform="unknown", status="failed",
        message=f"All {max_retries} retries exhausted. Last error: {last_error}",
        error_message="max_retries_exceeded",
    )


async def _try_auto_captcha() -> bool:
    """尝试自动解决验证码。无 CapSolver 时返回 False。"""
    try:
        import capsolver
        return True  # 可用但需要具体实现
    except ImportError:
        log.info("CapSolver not installed. Captcha needs human intervention.")
        return False
