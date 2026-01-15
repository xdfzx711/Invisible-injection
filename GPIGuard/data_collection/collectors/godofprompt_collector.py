#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GodOfPrompt.ai 数据收集器
抓取网站上的免费提示词
注意：此网站使用JavaScript动态加载内容，需要使用Selenium
"""

import time
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

from bs4 import BeautifulSoup

from ..base_collector import BaseCollector


class GodOfPromptCollector(BaseCollector):
    """GodOfPrompt.ai 数据收集器"""

    def __init__(self):
        super().__init__('godofprompt')
        self.base_url = "https://www.godofprompt.ai"
        self.request_delay = 2.0  # 请求间隔（秒）
        self.driver = None
        
        if not SELENIUM_AVAILABLE:
            self.logger.warning("Selenium not available. Please install: pip install selenium")

    def validate_config(self) -> bool:
        """验证配置（对于此特定收集器，配置是硬编码的）"""
        if not SELENIUM_AVAILABLE:
            print("\nError: 需要安装 Selenium 来处理JavaScript动态内容")
            print("请运行: pip install selenium")
            return False
        
        # 初始化浏览器驱动
        print("\n正在初始化浏览器驱动...")
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            print("正在启动 Chrome 浏览器...")
            
            # 优先使用 webdriver-manager 自动管理驱动
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    print("使用 webdriver-manager 自动管理 ChromeDriver...")
                    service = ChromeService(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("✓ ChromeDriver has been自动下载并配置")
                except Exception as e:
                    self.logger.warning(f"webdriver-manager failed, trying direct Chrome: {e}")
                    # 如果 webdriver-manager Failed，尝试直接使用系统PATH中的ChromeDriver
                    self.driver = webdriver.Chrome(options=chrome_options)
            else:
                # 如果没有 webdriver-manager，尝试直接使用系统PATH中的ChromeDriver
                print("尝试使用系统 PATH 中的 ChromeDriver...")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.set_page_load_timeout(30)  # 设置页面加载超时
            self.driver.implicitly_wait(5)  # 减少隐式等待时间
            print("✓ 浏览器驱动初始化成功")
            self.logger.info("Selenium WebDriver initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}", exc_info=True)
            print(f"\n✗ Error: 无法初始化浏览器驱动: {e}")
            print("\n可能的解决方案:")
            print("1. 确保has been安装 Chrome 浏览器")
            if not WEBDRIVER_MANAGER_AVAILABLE:
                print("2. 安装 webdriver-manager 自动管理驱动（推荐）:")
                print("   pip install webdriver-manager")
            print("3. 或者手动安装 ChromeDriver:")
            print("   - 下载与您的 Chrome 版本匹配的 ChromeDriver")
            print("   - 将 ChromeDriver 添加到系统 PATH")
            print("   - 或将其放在项目directory中")
            return False

    def collect(self) -> Dict[str, Any]:
        """执行数据收集"""
        # Checkdriver是否has been初始化
        if not self.driver:
            print("\nError: 浏览器驱动未初始化")
            print("请确保 validate_config() has been成功执行")
            return {
                'success': False,
                'message': 'Browser driver not initialized',
                'file_count': 0,
                'stats': self.get_stats()
            }
        
        self.start_collection()
        self.logger.info("Starting GodOfPrompt.ai collection...")
        print("\n" + "="*70)
        print("开始抓取 GodOfPrompt.ai 免费提示词")
        print("="*70)

        try:
            # 步骤 1: 获取所有分类
            print("\n[步骤 1/4] 获取分类列表...")
            categories = self._get_categories()
            if not categories:
                raise Exception("未能获取分类列表")
            
            print(f"✓ 成功获取 {len(categories)} 个分类")
            for cat in categories:
                print(f"  - {cat['name']} ({cat['slug']})")
            
            # 步骤 2: 获取所有提示词的 slugs
            print("\n[步骤 2/4] 收集所有提示词链接...")
            all_prompt_slugs = []
            for category in categories:
                print(f"\n正在处理分类: {category['name']}")
                slugs = self._get_prompt_slugs_for_category(category['slug'])
                for slug in slugs:
                    all_prompt_slugs.append({
                        'category': category['name'],
                        'slug': slug
                    })
                print(f"  ✓ 找到 {len(slugs)} 个提示词")
                time.sleep(self.request_delay)
            
            self.set_total_items(len(all_prompt_slugs))
            print(f"\n✓ 总共找到 {len(all_prompt_slugs)} 个免费提示词")
            
            # 步骤 3: 抓取每个提示词的内容
            print("\n[步骤 3/4] 抓取提示词内容...")
            final_prompts = []
            for i, item in enumerate(all_prompt_slugs, 1):
                print(f"\r进度: [{i}/{len(all_prompt_slugs)}] {item['slug'][:50]}...", end='', flush=True)
                
                prompt_content = self._get_prompt_content(item['slug'])
                if prompt_content:
                    final_prompts.append({
                        'category': item['category'],
                        'slug': item['slug'],
                        'prompt': prompt_content
                    })
                    self.increment_success()
                else:
                    self.increment_failure()
                    self.logger.warning(f"Failed to get content for: {item['slug']}")
                
                time.sleep(self.request_delay)
            
            print(f"\n✓ 成功抓取 {len(final_prompts)} 个提示词")
            
            # 步骤 4: 保存结果
            print("\n[步骤 4/4] 保存数据...")
            output_file = self._save_prompts(final_prompts)
            print(f"✓ 数据has been保存到: {output_file}")
            
            self.end_collection()
            self.log_summary()
            
            # 计算总大小
            total_size = output_file.stat().st_size if output_file.exists() else 0
            
            print("\n" + "="*70)
            print("抓取Completed！")
            print(f"成功: {self.stats['successful_items']} | Failed: {self.stats['failed_items']}")
            print(f"耗时: {self.stats['duration_seconds']:.2f} 秒")
            print("="*70 + "\n")

            return {
                'success': True,
                'file_count': len(final_prompts),
                'total_size': total_size,
                'output_dir': str(self.output_dir),
                'output_file': str(output_file),
                'stats': self.get_stats(),
                'message': f'Successfully collected {len(final_prompts)} prompts.'
            }

        except KeyboardInterrupt:
            print("\n\n用户中断操作")
            self.end_collection()
            return {
                'success': False,
                'message': 'Collection interrupted by user',
                'file_count': self.stats['successful_items'],
                'stats': self.get_stats()
            }
        except Exception as e:
            self.logger.error(f"Collection failed: {e}", exc_info=True)
            print(f"\n✗ Error: {e}")
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'file_count': 0,
                'stats': self.get_stats()
            }
        finally:
            # 关闭浏览器
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

    def _get_categories(self) -> List[Dict[str, str]]:
        """
        从主页获取所有分类（使用Selenium等待JavaScript加载）
        
        Returns:
            分类列表，每个分类包含 name 和 slug
        """
        url = f"{self.base_url}/prompt-library"
        self.logger.info(f"Fetching categories from: {url}")
        print(f"正在访问: {url}...")
        
        try:
            self.driver.get(url)
            print("等待页面加载...")
            # 等待页面加载
            time.sleep(3)
            
            # 等待分类链接出现
            print("等待页面内容加载...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='category='], [wized*='category'], .category-link"))
                )
                print("✓ 页面内容has been加载")
            except TimeoutException:
                self.logger.warning("Category links not found, trying alternative method")
                print("⚠ 未找到分类链接，尝试备用方法...")
            
            # 获取页面源码
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            categories = []
            
            # 查找所有包含category的链接
            category_links = soup.find_all('a', href=lambda x: x and 'category=' in str(x).lower())
            
            for link in category_links:
                href = link.get('href', '')
                if 'category=' in href.lower():
                    # 提取 slug
                    try:
                        if 'category=' in href:
                            slug = href.split('category=')[1].split('&')[0].split('#')[0]
                        else:
                            continue
                        
                        # 提取名称
                        name = link.get_text(strip=True)
                        if not name or len(name) < 2:
                            # 尝试从href中提取
                            name = slug.replace('-', ' ').title()
                        
                        # 避免重复和无效项
                        if slug and slug not in [cat['slug'] for cat in categories]:
                            categories.append({
                                'name': name or slug.capitalize(),
                                'slug': slug
                            })
                    except Exception as e:
                        self.logger.debug(f"Error parsing category link {href}: {e}")
                        continue
            
            # 如果没找到，尝试从URL参数中提取
            if not categories:
                # 尝试访问分类页面，从页面中提取
                test_url = f"{self.base_url}/prompts?category=marketing&premium=false"
                self.driver.get(test_url)
                time.sleep(2)
                # Check页面是否有分类选择器
                try:
                    category_elements = self.driver.find_elements(By.CSS_SELECTOR, "[wized*='category'], .category-link, a[href*='/prompts?category=']")
                    for elem in category_elements:
                        try:
                            href = elem.get_attribute('href') or ''
                            text = elem.text.strip()
                            if 'category=' in href:
                                slug = href.split('category=')[1].split('&')[0].split('#')[0]
                                if slug and slug not in [cat['slug'] for cat in categories]:
                                    categories.append({
                                        'name': text or slug.replace('-', ' ').title(),
                                        'slug': slug
                                    })
                        except:
                            continue
                except:
                    pass
            
            self.logger.info(f"Found {len(categories)} categories")
            return categories
            
        except Exception as e:
            self.logger.error(f"Failed to get categories: {e}", exc_info=True)
            return []

    def _get_prompt_slugs_for_category(self, category_slug: str) -> List[str]:
        """
        获取某个分类下的所有提示词 slugs（使用Selenium处理动态内容）
        通过点击"下一页"按钮实现分页，因为分页不会改变URL
        
        Args:
            category_slug: 分类的 slug
            
        Returns:
            提示词 slug 列表
        """
        all_slugs = []
        page = 1
        max_pages = 100  # 防止无限循环
        
        # 访问第一页
        url = f"{self.base_url}/prompts?category={category_slug}&premium=false"
        self.logger.info(f"Fetching prompts from: {url}")
        
        try:
            self.driver.get(url)
            # 等待内容加载
            time.sleep(3)
            
            # 等待提示词卡片出现
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[wized*='prompt'], .new-prompt-card, a[href*='prompt']"))
                )
            except TimeoutException:
                self.logger.warning(f"No prompts found on first page")
                print(f"  ⚠ 第 1 页未找到提示词，可能页面结构has been改变")
                return []
            
            while page <= max_pages:
                print(f"  正在处理第 {page} 页...")
                
                # 获取当前页面的提示词
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # 查找提示词链接 - 尝试多种选择器
                prompt_links = []
                
                # 方法1: 查找包含wized属性的链接
                wized_links = soup.find_all('a', attrs=lambda x: x and 'wized' in str(x).lower() and 'prompt' in str(x).lower())
                prompt_links.extend(wized_links)
                
                # 方法2: 查找href包含prompt的链接
                href_links = soup.find_all('a', href=lambda x: x and ('prompt=' in str(x).lower() or '/prompt' in str(x).lower()))
                prompt_links.extend(href_links)
                
                # 方法3: 从提示词卡片中查找链接
                cards = soup.find_all(attrs={'wized': lambda x: x and 'prompt' in str(x).lower()})
                for card in cards:
                    link = card.find('a', href=True)
                    if link:
                        prompt_links.append(link)
                
                # 去重并提取slugs
                page_slugs = []
                seen_hrefs = set()
                
                for link in prompt_links:
                    href = link.get('href', '')
                    if not href or href in seen_hrefs:
                        continue
                    seen_hrefs.add(href)
                    
                    # 提取slug
                    slug = None
                    if 'prompt=' in href:
                        slug = href.split('prompt=')[1].split('&')[0].split('#')[0]
                    elif '/prompt/' in href:
                        parts = href.split('/prompt/')
                        if len(parts) > 1:
                            slug = parts[1].split('?')[0].split('#')[0]
                    
                    if slug and slug not in all_slugs and len(slug) > 2:
                        all_slugs.append(slug)
                        page_slugs.append(slug)
                
                self.logger.info(f"Found {len(page_slugs)} new prompts on page {page} (total: {len(all_slugs)})")
                print(f"  ✓ 第 {page} 页找到 {len(page_slugs)} 个新提示词（累计: {len(all_slugs)}）")
                
                # Check是否有下一页
                has_next = False
                cur_page = None
                all_pages = None
                
                try:
                    # 查找分页容器
                    pagination_div = self.driver.find_element(By.CSS_SELECTOR, "[wized='pagination']")
                    
                    # 优先通过页数判断（最准确）
                    try:
                        cur_page_elem = pagination_div.find_element(By.CSS_SELECTOR, "[wized='pagin-cur-page']")
                        all_pages_elem = pagination_div.find_element(By.CSS_SELECTOR, "[wized='pagin-all-pages']")
                        cur_page = int(cur_page_elem.text.strip())
                        all_pages = int(all_pages_elem.text.strip())
                        print(f"  当前页: {cur_page}/{all_pages}")
                        
                        # 如果当前页has been经等于或大于总页数，说明没有下一页
                        if cur_page >= all_pages:
                            has_next = False
                            print(f"  ✓ has been到达最后一页（通过页数判断）")
                        elif cur_page < all_pages:
                            has_next = True
                    except Exception as e:
                        self.logger.debug(f"Could not get page numbers: {e}")
                        # 如果无法获取页数，尝试通过按钮状态判断
                        cur_page = None
                        all_pages = None
                    
                    # 如果通过页数无法判断，才通过按钮状态判断
                    if cur_page is None or all_pages is None:
                        # 查找下一页按钮
                        next_button = pagination_div.find_element(By.CSS_SELECTOR, "[wized='pagin-next'], #pag-next-button, .pagination-button-new.next")
                        
                        # Check按钮是否可点击
                        if next_button and next_button.is_enabled() and next_button.is_displayed():
                            # Check按钮是否被禁用（可能通过CSS类）
                            classes = next_button.get_attribute('class') or ''
                            if 'disabled' not in classes.lower():
                                has_next = True
                        else:
                            has_next = False
                    
                except NoSuchElementException:
                    self.logger.warning(f"Pagination element not found on page {page}")
                    has_next = False
                except Exception as e:
                    self.logger.warning(f"Error checking pagination: {e}")
                    has_next = False
                
                # 如果没有下一页，退出循环
                if not has_next:
                    print(f"  ✓ has been到达最后一页，停止分页")
                    break
                
                # 额外Check：如果当前页数has been经等于总页数，强制停止（防止按钮状态判断Error）
                if cur_page is not None and all_pages is not None and cur_page >= all_pages:
                    print(f"  ✓ 当前页 {cur_page} has been等于或超过总页数 {all_pages}，强制停止")
                    break
                
                # 点击下一页按钮
                try:
                    # 记录点击前的当前页数
                    old_page_num = None
                    try:
                        old_page_elem = self.driver.find_element(By.CSS_SELECTOR, "[wized='pagin-cur-page']")
                        old_page_num = int(old_page_elem.text.strip())
                    except:
                        pass
                    
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "[wized='pagin-next'], #pag-next-button")
                    
                    # 滚动到按钮位置，确保可见
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(0.5)
                    
                    # 点击按钮
                    next_button.click()
                    print(f"  → has been点击下一页按钮")
                    
                    # 等待新内容加载
                    time.sleep(2)
                    
                    # 等待页面内容更新（通过Check当前页数是否变化）
                    if old_page_num is not None:
                        try:
                            # 等待页数增加
                            WebDriverWait(self.driver, 20).until(
                                lambda driver: int(driver.find_element(By.CSS_SELECTOR, "[wized='pagin-cur-page']").text.strip()) > old_page_num
                            )
                            # 再等待一下确保内容完全加载
                            time.sleep(2)
                            print(f"  ✓ 页面has been更新到新页")
                        except TimeoutException:
                            self.logger.warning(f"Page number did not change after clicking next, waiting for content update")
                            # 如果页数没变化，等待提示词卡片更新
                            WebDriverWait(self.driver, 15).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "[wized*='prompt'], .new-prompt-card"))
                            )
                    else:
                        # 如果无法获取页数，等待提示词卡片更新
                        time.sleep(3)
                        WebDriverWait(self.driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[wized*='prompt'], .new-prompt-card"))
                        )
                    
                    page += 1
                    time.sleep(self.request_delay)
                    
                except Exception as e:
                    self.logger.error(f"Failed to click next button on page {page}: {e}")
                    print(f"  ✗ 点击下一页按钮Failed: {e}")
                    break
        
        except Exception as e:
            self.logger.error(f"Failed to get prompts for category {category_slug}: {e}", exc_info=True)
            print(f"  ✗ 获取分类 {category_slug} 的提示词Failed: {e}")
        
        return all_slugs

    def _get_prompt_content(self, prompt_slug: str) -> Optional[str]:
        """
        获取单个提示词的内容（使用Selenium）
        
        Args:
            prompt_slug: 提示词的 slug
            
        Returns:
            提示词内容文本，Failed返回 None
        """
        url = f"{self.base_url}/prompt?prompt={prompt_slug}"
        
        try:
            self.driver.get(url)
            # 等待内容加载
            time.sleep(2)
            
            # 等待提示词内容出现 - 优先等待 wized="pcp_gpt_content" 元素
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[wized='pcp_gpt_content'], div.code-block-text-cms, pre, code"))
                )
                print(f"  ✓ 页面内容has been加载")
            except TimeoutException:
                self.logger.warning(f"Timeout waiting for prompt content on page: {url}")
                # 继续尝试提取，可能元素has been经exists但选择器不对
            
            # 获取页面源码
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            content = None
            
            # 方法1: 优先查找 wized="pcp_gpt_content" 的元素（最准确）
            try:
                element = soup.find('div', {'wized': 'pcp_gpt_content'})
                if element:
                    content = element.get_text(separator='\n', strip=True)
                    if content and len(content) > 50:
                        self.logger.debug(f"Found content using wized='pcp_gpt_content'")
            except Exception as e:
                self.logger.debug(f"Error finding wized='pcp_gpt_content': {e}")
            
            # 方法2: 如果方法1Failed，尝试通过 class 查找
            if not content:
                try:
                    element = soup.find('div', class_=lambda x: x and 'code-block-text-cms' in ' '.join(x) if isinstance(x, list) else 'code-block-text-cms' in str(x))
                    if element:
                        content = element.get_text(separator='\n', strip=True)
                        if content and len(content) > 50:
                            self.logger.debug(f"Found content using class='code-block-text-cms'")
                except Exception as e:
                    self.logger.debug(f"Error finding code-block-text-cms: {e}")
            
            # 方法3: 尝试其他可能的选择器
            if not content:
                selectors = [
                    {'wized': lambda x: x and 'gpt_content' in str(x).lower()},
                    {'wized': lambda x: x and 'prompt' in str(x).lower() and 'content' in str(x).lower()},
                    {'class': lambda x: x and 'code-block' in ' '.join(x).lower() if isinstance(x, list) else 'code-block' in str(x).lower()},
                    {'class': lambda x: x and 'prompt-content' in ' '.join(x).lower() if isinstance(x, list) else 'prompt-content' in str(x).lower()},
                ]
                
                for selector in selectors:
                    try:
                        element = soup.find('div', attrs=selector)
                        if element:
                            text = element.get_text(separator='\n', strip=True)
                            if text and len(text) > 50:
                                content = text
                                self.logger.debug(f"Found content using alternative selector")
                                break
                    except:
                        continue
            
            # 方法4: 如果上述方法都Failed，尝试查找包含提示词特征的内容
            # 提示词通常包含 #CONTEXT: 或 #GOAL: 等标记
            if not content:
                all_divs = soup.find_all('div')
                for div in all_divs:
                    text = div.get_text(separator='\n', strip=True)
                    # Check是否包含提示词的典型特征
                    if text and len(text) > 100:
                        if any(marker in text for marker in ['#CONTEXT:', '#GOAL:', '#INFORMATION', 'Adopt the role', 'You are']):
                            content = text
                            self.logger.debug(f"Found content by searching for prompt markers")
                            break
            
            if content:
                self.logger.debug(f"Successfully extracted content for: {prompt_slug}")
                return content
            else:
                self.logger.warning(f"No content found for: {prompt_slug}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get content for {prompt_slug}: {e}")
            return None

    def _save_prompts(self, prompts: List[Dict[str, Any]]) -> Path:
        """
        保存提示词到 JSON File
        
        Args:
            prompts: 提示词列表
            
        Returns:
            输出File路径
        """
        output_file = self.output_dir / "prompts.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved {len(prompts)} prompts to: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Failed to save prompts: {e}")
            raise


