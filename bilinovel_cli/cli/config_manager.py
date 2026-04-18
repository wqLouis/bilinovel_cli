"""Configuration management for bilinovel-cli."""

from dataclasses import dataclass
from pathlib import Path

import tomllib


CONFIG_DIR = Path.home() / ".config" / "bilinovel-cli"
CONFIG_FILE = CONFIG_DIR / "config.toml"
BROWSER_TYPES = ["chromium", "firefox", "webkit"]


@dataclass
class BrowserConfig:
    type: str = "chromium"


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
    browser_cfg = BrowserConfig(type=data.get("browser", {}).get("type", "chromium"))
    return Config(browser=browser_cfg)


def save_config(config: Config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("# bilinovel-cli configuration\n\n")
        f.write(f"[browser]\n")
        f.write(f'type = "{config.browser.type}"\n')


def get_installed_browsers() -> list[str]:
    import subprocess

    result = subprocess.run(
        ["playwright", "install", "--list"],
        capture_output=True,
        text=True,
    )
    installed = []
    for browser in BROWSER_TYPES:
        if browser in result.stdout:
            installed.append(browser)
    return installed


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


def uninstall_browser(browser: str) -> bool:
    import subprocess

    result = subprocess.run(
        ["playwright", "uninstall", browser],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
