"""
Browser profiles for desktop and mobile AI platform probing.

Different devices → different AI answers.
We probe both to get the full visibility picture.
"""

DESKTOP_PROFILE = {
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "device_scale_factor": 1,
    "is_mobile": False,
    "has_touch": False,
}

MOBILE_IOS_PROFILE = {
    "viewport": {"width": 393, "height": 852},
    "user_agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
    ),
    "device_scale_factor": 3,
    "is_mobile": True,
    "has_touch": True,
}

MOBILE_ANDROID_PROFILE = {
    "viewport": {"width": 412, "height": 915},
    "user_agent": (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
    ),
    "device_scale_factor": 2.625,
    "is_mobile": True,
    "has_touch": True,
}


def get_profile(device: str = "desktop") -> dict:
    """Get browser profile by device type."""
    profiles = {
        "desktop": DESKTOP_PROFILE,
        "mobile_ios": MOBILE_IOS_PROFILE,
        "mobile_android": MOBILE_ANDROID_PROFILE,
    }
    return profiles.get(device, DESKTOP_PROFILE)
