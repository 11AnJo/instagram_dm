import zipfile
from urllib.parse import urlparse
import uuid
import os
import json
from typing import Optional, Tuple

class ProxyUtils:
    """Utility class for handling proxy configuration in Selenium WebDriver."""
    
    PROXY_SCHEMES = ('http://', 'https://')
    UNSUPPORTED_SCHEMES = ('socks5://',)
    PLUGIN_PREFIX = 'proxy_auth_plugin_'
    
    def __init__(self):
        self._proxy_extension_path = None

    def parse_proxy(self, proxy_string: str) -> Tuple[str, int, Optional[str], Optional[str]]:
        """
        Parse proxy string into components.
        
        Args:
            proxy_string: Proxy string in format [scheme://][username:password@]host:port
            
        Returns:
            Tuple of (host, port, username, password)
            
        Raises:
            ValueError: If proxy string is invalid or uses unsupported scheme
        """
        try:
            if any(proxy_string.startswith(scheme) for scheme in self.UNSUPPORTED_SCHEMES):
                raise ValueError(f"Unsupported proxy scheme in: {proxy_string}")
                
            if not proxy_string.startswith(self.PROXY_SCHEMES):
                proxy_string = f"http://{proxy_string}"

            parsed = urlparse(proxy_string)
            
            if not parsed.hostname or not parsed.port:
                raise ValueError(f"Invalid proxy format: {proxy_string}")

            return (
                parsed.hostname,
                parsed.port,
                parsed.username,
                parsed.password
            )
            
        except Exception as e:
            raise ValueError(f"Error parsing proxy '{proxy_string}': {str(e)}") from e

    def create_proxy_extension(self, proxy_string: str) -> str:
        """
        Create a Chrome proxy extension ZIP file.
        
        Args:
            proxy_string: Proxy string to configure
            
        Returns:
            Path to the created extension ZIP file
        """
        host, port, username, password = self.parse_proxy(proxy_string)
        
        manifest = {
            "version": "1.0.0",
            "manifest_version": 3,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "storage",
                "webRequest",
                "webRequestAuthProvider"
            ],
            "host_permissions": ["<all_urls>"],
            "background": {
                "service_worker": "background.js"
            },
            "minimum_chrome_version": "88.0.0"
        }

        background_js = f"""
        const config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{host}",
                    port: parseInt({port})
                }},
                bypassList: ["localhost"]
            }}
        }};
        
        chrome.proxy.settings.set({{ value: config, scope: "regular" }}, () => {{}});
        
        chrome.webRequest.onAuthRequired.addListener(
            (details) => ({{
                authCredentials: {{
                    username: "{username or ''}",
                    password: "{password or ''}"
                }}
            }}),
            {{ urls: ["<all_urls>"] }},
            ["blocking"]
        );
        """
        
        self._proxy_extension_path = f"{self.PLUGIN_PREFIX}{uuid.uuid4()}.zip"
        
        with zipfile.ZipFile(self._proxy_extension_path, 'w') as zp:
            zp.writestr("manifest.json", json.dumps(manifest, indent=4))
            zp.writestr("background.js", background_js.strip())
            
        return self._proxy_extension_path

    def cleanup_proxy_extension(self) -> None:
        """Clean up proxy extension file when it's no longer needed."""
        if not self._proxy_extension_path:
            return

        try:
            if os.path.exists(self._proxy_extension_path):
                os.remove(self._proxy_extension_path)
                self._proxy_extension_path = None
        except OSError as e:
            print(f"Warning: Failed to remove proxy extension {self._proxy_extension_path}: {e}")

    def __del__(self):
        """Destructor"""
        self.cleanup_proxy_extension()
