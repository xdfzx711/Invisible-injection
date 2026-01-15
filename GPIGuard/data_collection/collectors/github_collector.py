#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub 数据采集器（简化版）
- 从配置File读取仓库 URL 列表
- 可选抓取 README（通过 raw.githubusercontent.com 直接读取）
- 将原始数据保存到 testscan_data/origin_data/github/
"""

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

        # 配置File路径
        self.config_file = self.get_config_path('github_config.json')

        # 加载配置
        config_loader = ConfigLoader()
        self.config = config_loader.load_json_config(self.config_file)

        # 采集选项
        self.fetch_opts = self.config.get("fetch", {})
        self.per_page = self.config.get("request", {}).get("per_page", 50)

        # 过滤选项
        self.filter_opts = self.config.get("filter", {})
        self.english_only = self.filter_opts.get("english_only", False)
        self.english_threshold = self.filter_opts.get("english_threshold", 0.7)

    def validate_config(self) -> bool:
        """验证配置"""
        if not self.config_file.exists():
            self.logger.warning(f"Config file not found: {self.config_file}")
            print(f"\nWarning: 未找到GitHub配置File")
            print(f"配置File路径: {self.config_file}")
            print("\n示例内容:")
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

            # Check是否有仓库列表
            repos = self.config.get("repositories", [])
            if not repos:
                self.logger.warning("No repositories configured")
                print(f"\nWarning: 配置File中没有仓库列表")
                print(f"请在配置File中添加 'repositories' 字段")
                return False

            self.logger.info(f"Config validated: {len(repos)} repositories configured")
            return True

        except Exception as e:
            self.logger.error(f"Failed to validate config: {e}")
            return False

    def _parse_repo_url(self, url: str) -> Tuple[str, str, str, str, str]:
        """
        从 GitHub URL 中解析 owner、repo、branch、path 和 url_type
        支持三种格式:
        1. 仓库URL: https://github.com/owner/repo
           -> (owner, repo, None, None, 'repo')
        2. FileURL: https://github.com/owner/repo/blob/branch/path/to/file.md
           -> (owner, repo, branch, path/to/file.md, 'file')
        3. directoryURL: https://github.com/owner/repo/tree/branch/path/to/dir
           -> (owner, repo, branch, path/to/dir, 'directory')
        """
        url = url.strip()
        self.logger.debug(f"正在解析URL: '{url}' (长度: {len(url)})")

        # 尝试匹配FileURL格式 (/blob/)
        file_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", url)
        if file_match:
            owner = file_match.group(1)
            repo = file_match.group(2)
            branch = file_match.group(3)
            path = file_match.group(4)
            self.logger.info(f"识别为FileURL: {owner}/{repo}/{branch}/{path}")
            return owner, repo, branch, path, 'file'

        # 尝试匹配directoryURL格式 (/tree/)
        dir_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)(?:/(.+))?", url)
        if dir_match:
            owner = dir_match.group(1)
            repo = dir_match.group(2)
            branch = dir_match.group(3)
            path = dir_match.group(4) or ""  # 可能没有子路径
            self.logger.info(f"识别为directoryURL: {owner}/{repo}/{branch}/{path}")
            return owner, repo, branch, path, 'directory'

        # 尝试匹配仓库URL格式
        repo_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/?$", url)
        if repo_match:
            owner = repo_match.group(1)
            repo = repo_match.group(2)
            self.logger.info(f"识别为仓库URL: {owner}/{repo}")
            return owner, repo, None, None, 'repo'

        self.logger.error(f"无法解析URL: '{url}' (repr: {repr(url)})")
        raise ValueError(f"无法解析GitHub URL: {url}")

    def _fetch_file(self, owner: str, repo: str, branch: str, file_path: str) -> str:
        """
        获取指定File的原始内容
        如果启用了 english_only，会过滤掉非英文内容
        """
        # URL 编码File路径（处理空格和特殊字符）
        # 将路径按 '/' 分割，对每个部分单独编码，然后重新组合
        path_parts = file_path.split('/')
        encoded_parts = [urllib.parse.quote(part, safe='') for part in path_parts]
        encoded_path = '/'.join(encoded_parts)
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{encoded_path}"
        
        try:
            self.logger.debug(f"正在获取File: {file_path} (URL: {raw_url})")
            req = urllib.request.Request(raw_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8", errors="ignore")

                    # 英文过滤
                    if self.english_only:
                        if not self._is_english_text(content):
                            self.logger.info(f"跳过非英文File: {file_path}")
                            return ""

                    self.logger.info(f"成功获取File: {file_path} ({len(content)} 字符)")
                    return content
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTPError {e.code}: {file_path} (URL: {raw_url})")
            if e.code == 404:
                self.logger.debug(f"File不exists: {file_path}")
        except urllib.error.URLError as e:
            self.logger.error(f"URLError: {file_path}, Error: {e}")
        except Exception as e:
            self.logger.error(f"获取FileFailed: {file_path}, Error: {e}")
        return ""

    def _fetch_directory_fallback(self, owner: str, repo: str, branch: str, dir_path: str) -> List[Dict[str, str]]:
        """
        降级方案：通过爬取 GitHub 网页获取File列表
        返回File列表 [{"name": "file.md", "path": "dir/file.md"}, ...]
        """
        # 构建 GitHub 网页 URL
        if dir_path:
            # URL 编码directory路径
            encoded_path = urllib.parse.quote(dir_path, safe='/')
            web_url = f"https://github.com/{owner}/{repo}/tree/{branch}/{encoded_path}"
        else:
            web_url = f"https://github.com/{owner}/{repo}/tree/{branch}"

        try:
            self.logger.info(f"使用降级方案爬取网页: {web_url}")
            req = urllib.request.Request(web_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    html_content = resp.read().decode("utf-8", errors="ignore")

                    # 方法1: 尝试从 GitHub 的 JSON payload 中提取File列表
                    # GitHub 页面可能包含多个 JSON 对象，我们需要找到包含File列表的那个
                    files = []
                    
                    # 尝试匹配多种可能的 JSON 结构
                    patterns = [
                        # 新格式: "payload":{"tree":{"items":[...]}}
                        r'"payload":\s*\{[^}]*"tree":\s*\{[^}]*"items":\s*(\[[^\]]+\])',
                        # 旧格式: "tree":{"items":[...]}
                        r'"tree":\s*\{[^}]*"items":\s*(\[[^\]]+\])',
                        # 直接匹配 items 数组
                        r'"items":\s*(\[[^\]]+\])',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, html_content, re.DOTALL)
                        if match:
                            try:
                                items_json = match.group(1)
                                # 尝试解析 JSON
                                items = json.loads(items_json)
                                if isinstance(items, list) and len(items) > 0:
                                    for item in items:
                                        if isinstance(item, dict):
                                            # Check是否是File
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
                                        self.logger.info(f"降级方案找到 {len(files)} 个File（方法1）")
                                        return files
                            except (json.JSONDecodeError, KeyError, ValueError) as e:
                                self.logger.debug(f"方法1解析Failed: {e}")
                                continue
                    
                    # 方法2: 从 HTML 中直接提取File链接
                    # GitHub directory页面中的File链接格式: <a href="/owner/repo/blob/branch/path/to/file">
                    self.logger.info("尝试方法2: 从HTML中提取File链接")
                    
                    # 更精确的模式：匹配File链接（不是directory链接）
                    # File链接通常包含 'title=' 属性或者特定的类名
                    # 格式: <a class="..." href="/owner/repo/blob/branch/path" title="filename">
                    blob_url_pattern = rf'/{re.escape(owner)}/{re.escape(repo)}/blob/{re.escape(branch)}/([^"?#]+)'
                    
                    # 查找所有匹配的blob链接
                    blob_matches = re.finditer(blob_url_pattern, html_content)
                    seen_paths = set()
                    
                    for match in blob_matches:
                        file_path = match.group(1)
                        # 解码URL编码的路径
                        try:
                            file_path = urllib.parse.unquote(file_path)
                        except:
                            pass
                        
                        # 过滤entries件
                        if not file_path or file_path in seen_paths:
                            continue
                        
                        # 确保路径在目标directory下（如果指定了directory）
                        if dir_path:
                            if not file_path.startswith(dir_path):
                                continue
                        else:
                            # 如果没有指定directory，只获取根directory下的File
                            if '/' in file_path:
                                continue
                        
                        # 提取File名
                        file_name = file_path.split('/')[-1]
                        
                        # 跳过无效File名
                        if not file_name or file_name in ['.', '..', '']:
                            continue
                        
                        # Check是否是File（不是directory）
                        # directory链接通常是 /tree/ 而不是 /blob/，所以这里匹配的都是File链接
                        # 添加到File列表
                        seen_paths.add(file_path)
                        files.append({
                            "name": file_name,
                            "path": file_path
                        })
                    
                    if files:
                        # 去重
                        seen = set()
                        unique_files = []
                        for f in files:
                            path_key = f['path']
                            if path_key not in seen:
                                seen.add(path_key)
                                unique_files.append(f)
                        
                        self.logger.info(f"降级方案找到 {len(unique_files)} 个File（方法2）")
                        return unique_files
                    else:
                        self.logger.warning("降级方案未能从网页中提取File列表")
                        
        except urllib.error.HTTPError as e:
            self.logger.error(f"降级方案HTTPError {e.code}: {web_url}")
        except Exception as e:
            self.logger.error(f"降级方案Failed: {e}", exc_info=True)

        return []

    def _fetch_directory(self, owner: str, repo: str, branch: str, dir_path: str) -> List[Dict[str, Any]]:
        """
        获取directory下的所有File
        优先使用 GitHub API，Failed时使用降级方案（爬取网页）
        """
        # 构建 API URL
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{dir_path}?ref={branch}"

        # 添加 token（如果配置了）
        headers = {}
        token = self.config.get("token", "")
        if token:
            headers["Authorization"] = f"token {token}"

        files_data = []
        use_fallback = False

        try:
            self.logger.info(f"正在获取directory内容: {api_url}")
            req = urllib.request.Request(api_url, headers=headers)

            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8")
                    items = json.loads(content)

                    # 获取配置选项
                    recursive = self.fetch_opts.get("recursive_directory", False)
                    max_files = self.fetch_opts.get("max_files_per_directory", 100)

                    self.logger.info(f"directory包含 {len(items)} 个项目")

                    file_count = 0
                    for item in items:
                        if file_count >= max_files:
                            self.logger.warning(f"has been达到最大File数限制: {max_files}")
                            break

                        if item['type'] == 'file':
                            # 下载File内容（_fetch_file 内部会进行英文检测）
                            file_content = self._fetch_file(owner, repo, branch, item['path'])
                            if file_content:  # 如果内容为空（被过滤或下载Failed），则跳过
                                files_data.append({
                                    "path": item['path'],
                                    "name": item['name'],
                                    "size": item['size'],
                                    "branch": branch,
                                    "text": file_content
                                })
                                file_count += 1
                                self.logger.info(f"has been收集File {file_count}/{max_files}: {item['name']}")

                        elif item['type'] == 'dir' and recursive:
                            # 递归处理子directory
                            self.logger.info(f"递归处理子directory: {item['path']}")
                            sub_files = self._fetch_directory(owner, repo, branch, item['path'])
                            files_data.extend(sub_files)
                            file_count += len(sub_files)

                    self.logger.info(f"成功获取directory {dir_path}: {len(files_data)} 个File")
                    return files_data

        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTPError {e.code}: {api_url}")
            if e.code == 403:
                if not token:
                    self.logger.warning("遇到 API 限流（403），且未配置 GitHub token，尝试使用降级方案")
                    self.logger.info("提示: 配置 GitHub token 可以提高API调用限制，详见配置File")
                else:
                    self.logger.warning("遇到 API 限流（403），即使has been配置 token，尝试使用降级方案")
                use_fallback = True
            elif e.code == 404:
                self.logger.error(f"directory不exists（404）: {dir_path}")
                return files_data
            else:
                self.logger.warning(f"HTTPError {e.code}，尝试使用降级方案")
                use_fallback = True
        except Exception as e:
            self.logger.error(f"获取directoryFailed: {api_url}, Error: {e}")
            self.logger.info("尝试使用降级方案")
            use_fallback = True

        # 使用降级方案
        if use_fallback:
            self.logger.info(f"开始使用降级方案获取directory: {dir_path}")
            file_list = self._fetch_directory_fallback(owner, repo, branch, dir_path)
            if file_list:
                self.logger.info(f"降级方案获取到 {len(file_list)} 个File列表，开始下载内容")
                max_files = self.fetch_opts.get("max_files_per_directory", 100)
                file_count = 0

                for file_info in file_list:
                    if file_count >= max_files:
                        self.logger.warning(f"has been达到最大File数限制: {max_files}")
                        break

                    file_path = file_info['path']
                    file_name = file_info['name']

                    # 下载File内容
                    file_content = self._fetch_file(owner, repo, branch, file_path)
                    if file_content:
                        files_data.append({
                            "path": file_path,
                            "name": file_name,
                            "size": len(file_content),  # 使用实际内容长度
                            "branch": branch,
                            "text": file_content
                        })
                        file_count += 1
                        self.logger.info(f"has been收集File {file_count}/{max_files}: {file_name}")
                    else:
                        self.logger.debug(f"File内容为空，跳过: {file_name}")

                if files_data:
                    self.logger.info(f"降级方案成功获取directory {dir_path}: {len(files_data)} 个File")
                else:
                    self.logger.warning(f"降级方案获取到File列表，但所有File内容为空或被过滤")
            else:
                self.logger.warning(f"降级方案未能获取到File列表: {dir_path}")

        return files_data

    def _fetch_readme(self, owner: str, repo: str) -> str:
        """
        简化版：直接尝试获取 HEAD 分支的 README.md 原始内容
        如果启用了 english_only，会过滤掉非英文内容
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

                        # 英文过滤
                        if self.english_only:
                            if not self._is_english_text(content):
                                self.logger.info(f"跳过非英文 README: {owner}/{repo}")
                                return ""

                        return content
            except urllib.error.HTTPError as e:
                continue
            except Exception as e:
                self.logger.error(f"获取 README Failed: {raw_url}, Error: {e}")
        return ""

    def _is_english_text(self, text: str, threshold: float = None) -> bool:
        """
        检测文本是否主要是英文

        Args:
            text: 要检测的文本
            threshold: 英文字符占比阈值（0.0-1.0），默认使用配置中的值

        Returns:
            True 如果英文字符占比 >= threshold
        """
        if threshold is None:
            threshold = self.english_threshold

        if not text or not text.strip():
            return True  # 空文本视为英文

        # 统计各类字符
        english_chars = 0
        total_chars = 0

        for char in text:
            # 跳过空白字符、标点符号和数字
            if char.isspace() or char in string.punctuation or char.isdigit():
                continue

            total_chars += 1

            # 英文字符判断：
            # - 基本拉丁字母 (A-Z, a-z): 0x0041-0x005A, 0x0061-0x007A
            # - 扩展拉丁字母 (带音标等): 0x00C0-0x024F
            code_point = ord(char)
            if (code_point < 0x0080 or  # ASCII 范围
                (0x00C0 <= code_point <= 0x024F)):  # 扩展拉丁字母
                english_chars += 1

        if total_chars == 0:
            return True  # 只有标点、空格和数字，视为英文

        ratio = english_chars / total_chars

        # 记录检测结果（仅在启用过滤时）
        if self.english_only:
            self.logger.debug(f"英文检测: {english_chars}/{total_chars} = {ratio:.2%} (阈值: {threshold:.0%})")

        return ratio >= threshold

    def collect(self) -> Dict[str, Any]:
        """
        执行采集：按仓库保存一个 JSON File
        支持三种URL格式：
        1. 仓库URL: 收集README
        2. FileURL: 收集指定File
        3. directoryURL: 收集directory下所有File
        """
        self.start_collection()

        repos: List[str] = self.config.get("repositories", [])
        if not repos:
            msg = "配置File中未提供 repositories"
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

                # 根据 URL 类型处理
                if url_type == 'file':
                    # 单个File
                    self.logger.info(f"检测到FileURL，将获取: {path}")
                    file_content = self._fetch_file(owner, repo, branch, path)
                    if file_content:
                        record["fetched"]["files"].append({
                            "path": path,
                            "name": Path(path).name,
                            "branch": branch,
                            "text": file_content
                        })
                        self.logger.info(f"成功获取File: {path}")
                    else:
                        self.logger.warning(f"未能获取File: {path}")

                elif url_type == 'directory':
                    # directory
                    self.logger.info(f"检测到directoryURL，将获取directory: {path or '(根directory)'}")
                    files = self._fetch_directory(owner, repo, branch, path)
                    if files:
                        record["fetched"]["files"] = files
                        self.logger.info(f"成功获取directory，共 {len(files)} 个File")
                    else:
                        self.logger.warning(f"未能获取directory内容: {path}")

                elif url_type == 'repo':
                    # 仓库（获取README）
                    if self.fetch_opts.get("readme", True):
                        readme = self._fetch_readme(owner, repo)
                        if readme:
                            record["fetched"]["readme"] = {"text": readme, "path": "README.md"}

                # 预留 issues/PRs/commits：需要 GitHub API/GraphQL，后续可扩展

                # 生成输出File名
                if url_type == 'directory' and path:
                    # directoryURL：使用directory名作为File名的一部分
                    safe_path = path.replace('/', '_')
                    out_file = self.output_dir / f"{owner}_{repo}_{safe_path}_data.json"
                else:
                    out_file = self.output_dir / f"{owner}_{repo}_data.json"

                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)
                self.logger.info(f"has been保存: {out_file}")
                self.stats['successful_items'] += 1
            except Exception as e:
                self.logger.error(f"采集Failed {repo_url}: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                self.stats['failed_items'] += 1

        self.end_collection()

        return {
            "success": True,
            "message": f"成功收集 {self.stats['successful_items']} 个资源",
            "stats": self.get_stats(),
            "output_dir": str(self.output_dir)
        }


__all__ = ["GithubCollector"]









