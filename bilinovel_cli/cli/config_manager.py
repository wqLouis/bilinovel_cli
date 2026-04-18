"""Configuration management for bilinovel-cli."""

import shutil
from dataclasses import dataclass
from pathlib import Path

import tomllib


CONFIG_DIR = Path.home() / ".config" / "bilinovel-cli"
CONFIG_FILE = CONFIG_DIR / "config.toml"
PLAYWRIGHT_BROWSERS = ["chromium", "firefox", "webkit"]
SYSTEM_BROWSERS = [
    ("chromium", "/usr/bin/chromium"),
    ("firefox", "/usr/bin/firefox"),
    ("chrome", "/usr/bin/google-chrome"),
]


@dataclass
class BrowserConfig:
    type: str = "chromium"
    source: str = "playwright"
    executable_path: str = None


@dataclass
class Config:
    browser: BrowserConfig = None

    def __post_init__(self):
        if self.browser is None:
            self.browser = BrowserConfig()


def load_config() -> Config:
    if not CONFIG_FILE.exists():
        return Config()
    with open(CONFIG_FILE, "rb") as f:
        data = tomllib.load(f)
    browser_data = data.get("browser", {})
    browser_cfg = BrowserConfig(
        type=browser_data.get("type", "chromium"),
        source=browser_data.get("source", "playwright"),
        executable_path=browser_data.get("executable_path"),
    )
    return Config(browser=browser_cfg)


def save_config(config: Config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("# bilinovel-cli configuration\n\n")
        f.write(f"[browser]\n")
        f.write(f'type = "{config.browser.type}"\n')
        f.write(f'source = "{config.browser.source}"\n')
        if config.browser.executable_path:
            f.write(f'executable_path = "{config.browser.executable_path}"\n')


def get_installed_browsers() -> list[str]:
    import subprocess

    result = subprocess.run(
        ["playwright", "install", "--list"],
        capture_output=True,
        text=True,
    )
    installed = []
    for browser in PLAYWRIGHT_BROWSERS:
        if browser in result.stdout:
            installed.append(browser)
    return installed


def get_system_browsers() -> list[tuple[str, str, bool]]:
    results = []
    for name, path in SYSTEM_BROWSERS:
        found = shutil.which(path) is not None
        results.append((name, path, found))
    return results


def install_browser(browser: str, progress_callback=None) -> bool:
    import subprocess

    proc = subprocess.Popen(
        ["playwright", "install", browser],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for line in iter(proc.stdout.readline, ""):
        if line:
            if progress_callback:
                progress_callback(line.strip())
    proc.wait()
    return proc.returncode == 0


def uninstall_browsers() -> bool:
    import subprocess

    result = subprocess.run(
        ["playwright", "uninstall"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
