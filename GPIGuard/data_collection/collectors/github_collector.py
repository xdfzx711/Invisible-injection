#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from pathlib import Path
from typing import Dict, Any, List, Tuple
import json
import re
import urllib.request
import urllib.error
import urllib.parse
import string

import sys, os
sys.path.append(str(Path(__file__).parent.parent.parent))
from data_collection.base_collector import BaseCollector
from data_collection.utils.config_loader import ConfigLoader


class GithubCollector(BaseCollector):
    def __init__(self):
        super().__init__('github')

        # Config file path
        self.config_file = self.get_config_path('github_config.json')

        # Load configuration
        config_loader = ConfigLoader()
        self.config = config_loader.load_json_config(self.config_file)

        # Fetch options
        self.fetch_opts = self.config.get("fetch", {})
        self.per_page = self.config.get("request", {}).get("per_page", 50)

        # Filter options
        self.filter_opts = self.config.get("filter", {})
        self.english_only = self.filter_opts.get("english_only", False)
        self.english_threshold = self.filter_opts.get("english_threshold", 0.7)

    def validate_config(self) -> bool:
        """Validate configuration"""
        if not self.config_file.exists():
            self.logger.warning(f"Config file not found: {self.config_file}")
            print(f"\nWarning: GitHub config file not found")
            print(f"Config file path: {self.config_file}")
            print("\nExample content:")
            print(json.dumps({
                "token": "",
                "repositories": [
                    "https://github.com/owner/repo"
                ],
                "fetch": {
                    "readme": True,
                    "issues": False,
                    "pull_requests": False,
                    "commits": False
                },
                "request": {
                    "per_page": 50
                }
            }, indent=2))
            return False

        try:
            if not self.config:
                self.logger.error("Failed to load config")
                return False

            # Check if repository list exists
            repos = self.config.get("repositories", [])
            if not repos:
                self.logger.warning("No repositories configured")
                print(f"\nWarning: No repository list in config file")
                print(f"Please add 'repositories' field to config file")
                return False

            self.logger.info(f"Config validated: {len(repos)} repositories configured")
            return True

        except Exception as e:
            self.logger.error(f"Failed to validate config: {e}")
            return False

    def _parse_repo_url(self, url: str) -> Tuple[str, str, str, str, str]:
        """
        Parse owner, repo, branch, path and url_type from GitHub URL
        Supports three formats:
        1. Repository URL: https://github.com/owner/repo
           -> (owner, repo, None, None, 'repo')
        2. File URL: https://github.com/owner/repo/blob/branch/path/to/file.md
           -> (owner, repo, branch, path/to/file.md, 'file')
        3. Directory URL: https://github.com/owner/repo/tree/branch/path/to/dir
           -> (owner, repo, branch, path/to/dir, 'directory')
        """
        url = url.strip()
        self.logger.debug(f"Parsing URL: '{url}' (length: {len(url)})")

        # Try to match file URL format (/blob/)
        file_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", url)
        if file_match:
            owner = file_match.group(1)
            repo = file_match.group(2)
            branch = file_match.group(3)
            path = file_match.group(4)
            self.logger.info(f"Identified as file URL: {owner}/{repo}/{branch}/{path}")
            return owner, repo, branch, path, 'file'

        # Try to match directory URL format (/tree/)
        dir_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)(?:/(.+))?", url)
        if dir_match:
            owner = dir_match.group(1)
            repo = dir_match.group(2)
            branch = dir_match.group(3)
            path = dir_match.group(4) or ""  # May not have sub-path
            self.logger.info(f"Identified as directory URL: {owner}/{repo}/{branch}/{path}")
            return owner, repo, branch, path, 'directory'

        # Try to match repository URL format
        repo_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/?$", url)
        if repo_match:
            owner = repo_match.group(1)
            repo = repo_match.group(2)
            self.logger.info(f"Identified as repository URL: {owner}/{repo}")
            return owner, repo, None, None, 'repo'

        self.logger.error(f"Failed to parse URL: '{url}' (repr: {repr(url)})")
        raise ValueError(f"Failed to parse GitHub URL: {url}")

    def _fetch_file(self, owner: str, repo: str, branch: str, file_path: str) -> str:
        """
        Fetch the raw content of a specified file
        If english_only is enabled, non-English content will be filtered out
        """
        # URL encode file path (handle spaces and special characters)
        # Split the path by '/', encode each part separately, then reassemble
        path_parts = file_path.split('/')
        encoded_parts = [urllib.parse.quote(part, safe='') for part in path_parts]
        encoded_path = '/'.join(encoded_parts)
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{encoded_path}"
        
        try:
            self.logger.debug(f"Fetching file: {file_path} (URL: {raw_url})")
            req = urllib.request.Request(raw_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8", errors="ignore")

                    # English text filtering
                    if self.english_only:
                        if not self._is_english_text(content):
                            self.logger.info(f"Skipping non-English file: {file_path}")
                            return ""

                    self.logger.info(f"Successfully fetched file: {file_path} ({len(content)} characters)")
                    return content
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTPError {e.code}: {file_path} (URL: {raw_url})")
            if e.code == 404:
                self.logger.debug(f"File does not exist: {file_path}")
        except urllib.error.URLError as e:
            self.logger.error(f"URLError: {file_path}, Error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to fetch file: {file_path}, Error: {e}")
        return ""

    def _fetch_directory_fallback(self, owner: str, repo: str, branch: str, dir_path: str) -> List[Dict[str, str]]:
        """
        Fallback method: Fetch file list by scraping GitHub webpage
        Returns file list [{"name": "file.md", "path": "dir/file.md"}, ...]
        """
        # Build GitHub web page URL
        if dir_path:
            # URL encode directory path
            encoded_path = urllib.parse.quote(dir_path, safe='/')
            web_url = f"https://github.com/{owner}/{repo}/tree/{branch}/{encoded_path}"
        else:
            web_url = f"https://github.com/{owner}/{repo}/tree/{branch}"

        try:
            self.logger.info(f"Using fallback method to scrape webpage: {web_url}")
            req = urllib.request.Request(web_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    html_content = resp.read().decode("utf-8", errors="ignore")

                    # Method 1: Try to extract file list from GitHub's JSON payload
                    # GitHub pages may contain multiple JSON objects, we need to find the one containing the file list
                    files = []
                    
                    # Try to match various possible JSON structures
                    patterns = [
                        # New format: "payload":{"tree":{"items":[...]}}
                        r'"payload":\s*\{[^}]*"tree":\s*\{[^}]*"items":\s*(\[[^\]]+\])',
                        # Old format: "tree":{"items":[...]}
                        r'"tree":\s*\{[^}]*"items":\s*(\[[^\]]+\])',
                        # Direct match items array
                        r'"items":\s*(\[[^\]]+\])',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, html_content, re.DOTALL)
                        if match:
                            try:
                                items_json = match.group(1)
                                # Try to parse JSON
                                items = json.loads(items_json)
                                if isinstance(items, list) and len(items) > 0:
                                    for item in items:
                                        if isinstance(item, dict):
                                            # Check if it is a file
                                            content_type = item.get('contentType', '')
                                            item_type = item.get('type', '')
                                            if content_type == 'file' or item_type == 'file':
                                                file_path = item.get('path', '') or item.get('name', '')
                                                file_name = item.get('name', '')
                                                if file_path and file_name:
                                                    files.append({
                                                        "name": file_name,
                                                        "path": file_path
                                                    })
                                    if files:
                                        self.logger.info(f"Fallback method found {len(files)} files (method 1)")
                                        return files
                            except (json.JSONDecodeError, KeyError, ValueError) as e:
                                self.logger.debug(f"Method 1 parsing failed: {e}")
                                continue
                    
                    # Method 2: Extract file links directly from HTML
                    # File link format in GitHub directory page: <a href="/owner/repo/blob/branch/path/to/file">
                    self.logger.info("Trying method 2: Extract file links from HTML")
                    
                    # More precise pattern: match file links (not directory links)
                    # File links usually contain 'title=' attribute or specific class names
                    # Format: <a class="..." href="/owner/repo/blob/branch/path" title="filename">
                    blob_url_pattern = rf'/{re.escape(owner)}/{re.escape(repo)}/blob/{re.escape(branch)}/([^"?#]+)'
                    
                    # Find all matching blob links
                    blob_matches = re.finditer(blob_url_pattern, html_content)
                    seen_paths = set()
                    
                    for match in blob_matches:
                        file_path = match.group(1)
                        # Decode URL-encoded path
                        try:
                            file_path = urllib.parse.unquote(file_path)
                        except:
                            pass
                        
                        # Filter entries
                        if not file_path or file_path in seen_paths:
                            continue
                        
                        # Ensure the path is in the target directory (if specified)
                        if dir_path:
                            if not file_path.startswith(dir_path):
                                continue
                        else:
                            # If no directory is specified, only get files in the root directory
                            if '/' in file_path:
                                continue
                        
                        # Extract file name
                        file_name = file_path.split('/')[-1]
                        
                        # Skip invalid file names
                        if not file_name or file_name in ['.', '..', '']:
                            continue
                        
                        # Check if it is a file (not a directory)
                        # Directory links are usually /tree/ instead of /blob/, so matches here are all file links
                        # Add to file list
                        seen_paths.add(file_path)
                        files.append({
                            "name": file_name,
                            "path": file_path
                        })
                    
                    if files:
                        # Deduplication
                        seen = set()
                        unique_files = []
                        for f in files:
                            path_key = f['path']
                            if path_key not in seen:
                                seen.add(path_key)
                                unique_files.append(f)
                        
                        self.logger.info(f"Fallback method found {len(unique_files)} files (method 2)")
                        return unique_files
                    else:
                        self.logger.warning("Fallback method failed to extract file list from webpage")
                        
        except urllib.error.HTTPError as e:
            self.logger.error(f"Fallback method HTTPError {e.code}: {web_url}")
        except Exception as e:
            self.logger.error(f"Fallback method failed: {e}", exc_info=True)

        return []

    def _fetch_directory(self, owner: str, repo: str, branch: str, dir_path: str) -> List[Dict[str, Any]]:
        """
        Fetch all files in a directory
        Prioritize using GitHub API, fallback to webpage scraping on failure
        """
        # Build API URL
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{dir_path}?ref={branch}"

        # Add token (if configured)
        headers = {}
        token = self.config.get("token", "")
        if token:
            headers["Authorization"] = f"token {token}"

        files_data = []
        use_fallback = False

        try:
            self.logger.info(f"Fetching directory contents: {api_url}")
            req = urllib.request.Request(api_url, headers=headers)

            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8")
                    items = json.loads(content)

                    # Get configuration options
                    recursive = self.fetch_opts.get("recursive_directory", False)
                    max_files = self.fetch_opts.get("max_files_per_directory", 100)

                    self.logger.info(f"Directory contains {len(items)} items")

                    file_count = 0
                    for item in items:
                        if file_count >= max_files:
                            self.logger.warning(f"Reached maximum file limit: {max_files}")
                            break

                        if item['type'] == 'file':
                            # Download file content (_fetch_file performs English detection internally)
                            file_content = self._fetch_file(owner, repo, branch, item['path'])
                            if file_content:  # Skip if content is empty (filtered or download failed)
                                files_data.append({
                                    "path": item['path'],
                                    "name": item['name'],
                                    "size": item['size'],
                                    "branch": branch,
                                    "text": file_content
                                })
                                file_count += 1
                                self.logger.info(f"Collected file {file_count}/{max_files}: {item['name']}")

                        elif item['type'] == 'dir' and recursive:
                            # Recursively process subdirectory
                            self.logger.info(f"Recursively processing subdirectory: {item['path']}")
                            sub_files = self._fetch_directory(owner, repo, branch, item['path'])
                            files_data.extend(sub_files)
                            file_count += len(sub_files)

                    self.logger.info(f"Successfully fetched directory {dir_path}: {len(files_data)} files")
                    return files_data

        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTPError {e.code}: {api_url}")
            if e.code == 403:
                if not token:
                    self.logger.warning("Encountered API rate limit (403) without GitHub token configured, trying fallback method")
                    self.logger.info("Tip: Configuring GitHub token can increase API call limits, see config file")
                else:
                    self.logger.warning("Encountered API rate limit (403) even with token configured, trying fallback method")
                use_fallback = True
            elif e.code == 404:
                self.logger.error(f"Directory does not exist (404): {dir_path}")
                return files_data
            else:
                self.logger.warning(f"HTTPError {e.code}, trying fallback method")
                use_fallback = True
        except Exception as e:
            self.logger.error(f"Failed to fetch directory: {api_url}, Error: {e}")
            self.logger.info("Trying fallback method")
            use_fallback = True

        # Use fallback method
        if use_fallback:
            self.logger.info(f"Starting to fetch directory using fallback method: {dir_path}")
            file_list = self._fetch_directory_fallback(owner, repo, branch, dir_path)
            if file_list:
                self.logger.info(f"Fallback method retrieved {len(file_list)} file list, starting download")
                max_files = self.fetch_opts.get("max_files_per_directory", 100)
                file_count = 0

                for file_info in file_list:
                    if file_count >= max_files:
                        self.logger.warning(f"Reached maximum file limit: {max_files}")
                        break

                    file_path = file_info['path']
                    file_name = file_info['name']

                    # Download file content
                    file_content = self._fetch_file(owner, repo, branch, file_path)
                    if file_content:
                        files_data.append({
                            "path": file_path,
                            "name": file_name,
                            "size": len(file_content),  # Use actual content length
                            "branch": branch,
                            "text": file_content
                        })
                        file_count += 1
                        self.logger.info(f"Collected file {file_count}/{max_files}: {file_name}")
                    else:
                        self.logger.debug(f"File content is empty, skipping: {file_name}")

                if files_data:
                    self.logger.info(f"Fallback method successfully fetched directory {dir_path}: {len(files_data)} files")
                else:
                    self.logger.warning(f"Fallback method retrieved file list, but all file contents are empty or filtered")
            else:
                self.logger.warning(f"Fallback method failed to retrieve file list: {dir_path}")

        return files_data

    def _fetch_readme(self, owner: str, repo: str) -> str:
        """
        Simplified version: Directly try to fetch the raw content of README.md from HEAD branch
        If english_only is enabled, non-English content will be filtered out
        """
        raw_urls = [
            f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
        ]
        for raw_url in raw_urls:
            try:
                with urllib.request.urlopen(raw_url, timeout=15) as resp:
                    if resp.status == 200:
                        content = resp.read().decode("utf-8", errors="ignore")

                        # English text filtering
                        if self.english_only:
                            if not self._is_english_text(content):
                                self.logger.info(f"Skipping non-English README: {owner}/{repo}")
                                return ""

                        return content
            except urllib.error.HTTPError as e:
                continue
            except Exception as e:
                self.logger.error(f"Failed to fetch README: {raw_url}, Error: {e}")
        return ""

    def _is_english_text(self, text: str, threshold: float = None) -> bool:
        """
        Detect if text is primarily English

        Args:
            text: Text to detect
            threshold: English character ratio threshold (0.0-1.0), defaults to value in config

        Returns:
            True if English character ratio >= threshold
        """
        if threshold is None:
            threshold = self.english_threshold

        if not text or not text.strip():
            return True  # Empty text is considered English

        # Count various character types
        english_chars = 0
        total_chars = 0

        for char in text:
            # Skip whitespace, punctuation and numbers
            if char.isspace() or char in string.punctuation or char.isdigit():
                continue

            total_chars += 1

            # English character judgment:
            # - Basic Latin letters (A-Z, a-z): 0x0041-0x005A, 0x0061-0x007A
            # - Extended Latin letters (with diacritics etc): 0x00C0-0x024F
            code_point = ord(char)
            if (code_point < 0x0080 or  # ASCII range
                (0x00C0 <= code_point <= 0x024F)):  # Extended Latin letters
                english_chars += 1

        if total_chars == 0:
            return True  # Only punctuation, spaces and numbers, treat as English

        ratio = english_chars / total_chars

        # Log detection result (only when filtering is enabled)
        if self.english_only:
            self.logger.debug(f"English detection: {english_chars}/{total_chars} = {ratio:.2%} (threshold: {threshold:.0%})")

        return ratio >= threshold

    def collect(self) -> Dict[str, Any]:
        """
        Execute collection: Save one JSON file per repository
        Supports three URL formats:
        1. Repository URL: Collect README
        2. File URL: Collect specified file
        3. Directory URL: Collect all files under directory
        """
        self.start_collection()

        repos: List[str] = self.config.get("repositories", [])
        if not repos:
            msg = "repositories not provided in config file"
            self.logger.error(msg)
            return {"success": False, "message": msg, "stats": self.get_stats()}

        self.stats['total_items'] = len(repos)

        for repo_url in repos:
            try:
                owner, repo, branch, path, url_type = self._parse_repo_url(repo_url)

                record: Dict[str, Any] = {
                    "repository_url": repo_url,
                    "url_type": url_type,
                    "owner": owner,
                    "repo": repo,
                    "fetched": {
                        "files": [],
                        "readme": None,
                        "issues": [],
                        "pull_requests": [],
                        "commits": []
                    },
                    "fetch_options": self.fetch_opts
                }

                # Process based on URL type
                if url_type == 'file':
                    # Single file
                    self.logger.info(f"Detected file URL, will fetch: {path}")
                    file_content = self._fetch_file(owner, repo, branch, path)
                    if file_content:
                        record["fetched"]["files"].append({
                            "path": path,
                            "name": Path(path).name,
                            "branch": branch,
                            "text": file_content
                        })
                        self.logger.info(f"Successfully fetched file: {path}")
                    else:
                        self.logger.warning(f"Failed to fetch file: {path}")

                elif url_type == 'directory':
                    # directory
                    self.logger.info(f"Detected directory URL, will fetch directory: {path or '(root directory)'}")
                    files = self._fetch_directory(owner, repo, branch, path)
                    if files:
                        record["fetched"]["files"] = files
                        self.logger.info(f"Successfully fetched directory, total {len(files)} files")
                    else:
                        self.logger.warning(f"Failed to fetch directory contents: {path}")

                elif url_type == 'repo':
                    # Repository (fetch README)
                    if self.fetch_opts.get("readme", True):
                        readme = self._fetch_readme(owner, repo)
                        if readme:
                            record["fetched"]["readme"] = {"text": readme, "path": "README.md"}

                # Reserved for issues/PRs/commits: Requires GitHub API/GraphQL, can be extended later

                # Generate output file name
                if url_type == 'directory' and path:
                    # Directory URL: Use directory name as part of file name
                    safe_path = path.replace('/', '_')
                    out_file = self.output_dir / f"{owner}_{repo}_{safe_path}_data.json"
                else:
                    out_file = self.output_dir / f"{owner}_{repo}_data.json"

                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Saved: {out_file}")
                self.stats['successful_items'] += 1
            except Exception as e:
                self.logger.error(f"Collection failed {repo_url}: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                self.stats['failed_items'] += 1

        self.end_collection()

        return {
            "success": True,
            "message": f"Successfully collected {self.stats['successful_items']} resources",
            "stats": self.get_stats(),
            "output_dir": str(self.output_dir)
        }


__all__ = ["GithubCollector"]









