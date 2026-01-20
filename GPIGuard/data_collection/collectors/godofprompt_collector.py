#!/usr/bin/env python3
# -*- coding: utf-8 -*-

 

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
    """GodOfPrompt.ai data collector"""

    def __init__(self):
        super().__init__('godofprompt')
        self.base_url = "https://www.godofprompt.ai"
        self.request_delay = 2.0  # Request interval (seconds)
        self.driver = None
        
        if not SELENIUM_AVAILABLE:
            self.logger.warning("Selenium not available. Please install: pip install selenium")

    def validate_config(self) -> bool:
        """Validate configuration (for this specific collector, configuration is hardcoded)"""
        if not SELENIUM_AVAILABLE:
            print("\nError: Selenium installation required to handle JavaScript dynamic content")
            print("Please run: pip install selenium")
            return False
        
        # Initialize browser driver
        print("\nInitializing browser driver...")
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            print("Starting Chrome browser...")
            
            # Prioritize webdriver-manager for automatic driver management
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    print("Using webdriver-manager to automatically manage ChromeDriver...")
                    service = ChromeService(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("✓ ChromeDriver automatically downloaded and configured")
                except Exception as e:
                    self.logger.warning(f"webdriver-manager failed, trying direct Chrome: {e}")
                    # If webdriver-manager failed, try using ChromeDriver directly from system PATH
                    self.driver = webdriver.Chrome(options=chrome_options)
            else:
                # If webdriver-manager not available, try using ChromeDriver directly from system PATH
                print("Trying to use ChromeDriver from system PATH...")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.set_page_load_timeout(30)  # Set page load timeout
            self.driver.implicitly_wait(5)  # Reduce implicit wait time
            print("✓ Browser driver initialized successfully")
            self.logger.info("Selenium WebDriver initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}", exc_info=True)
            print(f"\n✗ Error: Cannot initialize browser driver: {e}")
            print("\nPossible solutions:")
            print("1. Make sure Chrome browser is installed")
            if not WEBDRIVER_MANAGER_AVAILABLE:
                print("2. Install webdriver-manager to automatically manage drivers (recommended):")
                print("   pip install webdriver-manager")
            print("3. Or manually install ChromeDriver:")
            print("   - Download ChromeDriver matching your Chrome version")
            print("   - Add ChromeDriver to system PATH")
            print("   - Or place it in the project directory")
            return False

    def collect(self) -> Dict[str, Any]:
        """Execute data collection"""
        # Check if driver has been initialized
        if not self.driver:
            print("\nError: Browser driver not initialized")
            print("Please ensure validate_config() executed successfully")
            return {
                'success': False,
                'message': 'Browser driver not initialized',
                'file_count': 0,
                'stats': self.get_stats()
            }
        
        self.start_collection()
        self.logger.info("Starting GodOfPrompt.ai collection...")
        print("\n" + "="*70)
        print("Starting to scrape GodOfPrompt.ai free prompts")
        print("="*70)

        try:
            # Step 1: Get all categories
            print("\n[Step 1/4] Getting category list...")
            categories = self._get_categories()
            if not categories:
                raise Exception("Failed to get category list")
            
            print(f"✓ Successfully got {len(categories)} categories")
            for cat in categories:
                print(f"  - {cat['name']} ({cat['slug']})")
            
            # Step 2: Get all prompt slugs
            print("\n[Step 2/4] Collecting all prompt links...")
            all_prompt_slugs = []
            for category in categories:
                print(f"\nProcessing category: {category['name']}")
                slugs = self._get_prompt_slugs_for_category(category['slug'])
                for slug in slugs:
                    all_prompt_slugs.append({
                        'category': category['name'],
                        'slug': slug
                    })
                print(f"  ✓ Found {len(slugs)} prompts")
                time.sleep(self.request_delay)
            
            self.set_total_items(len(all_prompt_slugs))
            print(f"\n✓ Found total {len(all_prompt_slugs)} free prompts")
            
            # Step 3: Scrape prompt content
            print("\n[Step 3/4] Scraping prompt content...")
            final_prompts = []
            for i, item in enumerate(all_prompt_slugs, 1):
                print(f"\rProgress: [{i}/{len(all_prompt_slugs)}] {item['slug'][:50]}...", end='', flush=True)
                
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
            
            print(f"\n✓ Successfully scraped {len(final_prompts)} prompts")
            
            # Step 4: Save results
            print("\n[Step 4/4] Saving data...")
            output_file = self._save_prompts(final_prompts)
            print(f"✓ Data saved to: {output_file}")
            
            self.end_collection()
            self.log_summary()
            
            # 计算总大小
            total_size = output_file.stat().st_size if output_file.exists() else 0
            
            print("\n" + "="*70)
            print("Scraping completed!")
            print(f"Success: {self.stats['successful_items']} | Failed: {self.stats['failed_items']}")
            print(f"Time taken: {self.stats['duration_seconds']:.2f} seconds")
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
            print("\n\nUser interrupted operation")
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
            # Close browser
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

    def _get_categories(self) -> List[Dict[str, str]]:
        """
        Get all categories from main page (use Selenium to wait for JavaScript to load)
        
        Returns:
            Category list, each category contains name and slug
        """
        url = f"{self.base_url}/prompt-library"
        self.logger.info(f"Fetching categories from: {url}")
        print(f"Accessing: {url}...")
        
        try:
            self.driver.get(url)
            print("Waiting for page to load...")
            # Wait for page to load
            time.sleep(3)
            
            # Wait for category links to appear
            print("Waiting for page content to load...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='category='], [wized*='category'], .category-link"))
                )
                print("✓ Page content loaded")
            except TimeoutException:
                self.logger.warning("Category links not found, trying alternative method")
                print("⚠ Category links not found, trying alternative method...")
            
            # Get page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            categories = []
            
            # Find all links containing category
            category_links = soup.find_all('a', href=lambda x: x and 'category=' in str(x).lower())
            
            for link in category_links:
                href = link.get('href', '')
                if 'category=' in href.lower():
                    # Extract slug
                    try:
                        if 'category=' in href:
                            slug = href.split('category=')[1].split('&')[0].split('#')[0]
                        else:
                            continue
                        
                        # Extract name
                        name = link.get_text(strip=True)
                        if not name or len(name) < 2:
                            # Try to extract from href
                            name = slug.replace('-', ' ').title()
                        
                        # Avoid duplicates and invalid items
                        if slug and slug not in [cat['slug'] for cat in categories]:
                            categories.append({
                                'name': name or slug.capitalize(),
                                'slug': slug
                            })
                    except Exception as e:
                        self.logger.debug(f"Error parsing category link {href}: {e}")
                        continue
            
            # If not found, try extracting from URL parameters
            if not categories:
                # Try accessing category page, extract from page
                test_url = f"{self.base_url}/prompts?category=marketing&premium=false"
                self.driver.get(test_url)
                time.sleep(2)
                # Check if page has category selector
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
        Get all prompt slugs under a category (using Selenium to handle dynamic content)
        Implement pagination by clicking the 'next page' button, because pagination does not change the URL
        
        Args:
            category_slug: Category slug
            
        Returns:
            List of prompt slugs
        """
        all_slugs = []
        page = 1
        max_pages = 100  # Prevent infinite loop
        
        # Visit first page
        url = f"{self.base_url}/prompts?category={category_slug}&premium=false"
        self.logger.info(f"Fetching prompts from: {url}")
        
        try:
            self.driver.get(url)
            # Wait for content to load
            time.sleep(3)
            
            # Wait for prompt cards to appear
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[wized*='prompt'], .new-prompt-card, a[href*='prompt']"))
                )
            except TimeoutException:
                self.logger.warning(f"No prompts found on first page")
                print(f"  ⚠ No prompts found on page 1, page structure may have changed")
                return []
            
            while page <= max_pages:
                print(f"  Processing page {page}...")
                
                # Get prompts from current page
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Find prompt links - try multiple selectors
                prompt_links = []
                
                # Method 1: Find links containing wized attributes
                wized_links = soup.find_all('a', attrs=lambda x: x and 'wized' in str(x).lower() and 'prompt' in str(x).lower())
                prompt_links.extend(wized_links)
                
                # Method 2: Find links with prompt in href
                href_links = soup.find_all('a', href=lambda x: x and ('prompt=' in str(x).lower() or '/prompt' in str(x).lower()))
                prompt_links.extend(href_links)
                
                # Method 3: Find links from prompt cards
                cards = soup.find_all(attrs={'wized': lambda x: x and 'prompt' in str(x).lower()})
                for card in cards:
                    link = card.find('a', href=True)
                    if link:
                        prompt_links.append(link)
                
                # Deduplicate and extract slugs
                page_slugs = []
                seen_hrefs = set()
                
                for link in prompt_links:
                    href = link.get('href', '')
                    if not href or href in seen_hrefs:
                        continue
                    seen_hrefs.add(href)
                    
                    # Extract slug
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
                print(f"  ✓ Found {len(page_slugs)} new prompts on page {page} (total: {len(all_slugs)})")
                
                # Check if there is a next page
                has_next = False
                cur_page = None
                all_pages = None
                
                try:
                    # Find pagination container
                    pagination_div = self.driver.find_element(By.CSS_SELECTOR, "[wized='pagination']")
                    
                    # Determine by page numbers first (most accurate)
                    try:
                        cur_page_elem = pagination_div.find_element(By.CSS_SELECTOR, "[wized='pagin-cur-page']")
                        all_pages_elem = pagination_div.find_element(By.CSS_SELECTOR, "[wized='pagin-all-pages']")
                        cur_page = int(cur_page_elem.text.strip())
                        all_pages = int(all_pages_elem.text.strip())
                        print(f"  Current page: {cur_page}/{all_pages}")
                        
                        # If current page is equal to or greater than total pages, there is no next page
                        if cur_page >= all_pages:
                            has_next = False
                            print(f"  ✓ Reached last page (determined by page numbers)")
                        elif cur_page < all_pages:
                            has_next = True
                    except Exception as e:
                        self.logger.debug(f"Could not get page numbers: {e}")
                        # If unable to get page numbers, try to determine by button state
                        cur_page = None
                        all_pages = None
                    
                    # If cannot determine by page numbers, then determine by button state
                    if cur_page is None or all_pages is None:
                        # Find next page button
                        next_button = pagination_div.find_element(By.CSS_SELECTOR, "[wized='pagin-next'], #pag-next-button, .pagination-button-new.next")
                        
                        # Check if button is clickable
                        if next_button and next_button.is_enabled() and next_button.is_displayed():
                            # Check if button is disabled (may be through CSS class)
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
                
                # If there is no next page, exit loop
                if not has_next:
                    print(f"  ✓ Reached last page, stop pagination")
                    break
                
                # Extra check: If current page number equals total pages, force stop (prevent button state judgment error)
                if cur_page is not None and all_pages is not None and cur_page >= all_pages:
                    print(f"  ✓ Current page {cur_page} equals or exceeds total pages {all_pages}, force stop")
                    break
                
                # Click next page button
                try:
                    # Record current page number before clicking
                    old_page_num = None
                    try:
                        old_page_elem = self.driver.find_element(By.CSS_SELECTOR, "[wized='pagin-cur-page']")
                        old_page_num = int(old_page_elem.text.strip())
                    except:
                        pass
                    
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "[wized='pagin-next'], #pag-next-button")
                    
                    # Scroll to button position, ensure visibility
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(0.5)
                    
                    # Click button
                    next_button.click()
                    print(f"  → Clicked next page button")
                    
                    # Wait for new content to load
                    time.sleep(2)
                    
                    # Wait for page content to update (by checking if current page number changes)
                    if old_page_num is not None:
                        try:
                            # Wait for page number to increase
                            WebDriverWait(self.driver, 20).until(
                                lambda driver: int(driver.find_element(By.CSS_SELECTOR, "[wized='pagin-cur-page']").text.strip()) > old_page_num
                            )
                            # Wait a bit more to ensure content is fully loaded
                            time.sleep(2)
                            print(f"  ✓ Page updated to new page")
                        except TimeoutException:
                            self.logger.warning(f"Page number did not change after clicking next, waiting for content update")
                            # If page number doesn't change, wait for prompt card update
                            WebDriverWait(self.driver, 15).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "[wized*='prompt'], .new-prompt-card"))
                            )
                    else:
                        # If unable to get page number, wait for prompt card update
                        time.sleep(3)
                        WebDriverWait(self.driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[wized*='prompt'], .new-prompt-card"))
                        )
                    
                    page += 1
                    time.sleep(self.request_delay)
                    
                except Exception as e:
                    self.logger.error(f"Failed to click next button on page {page}: {e}")
                    print(f"  ✗ Failed to click next page button: {e}")
                    break
        
        except Exception as e:
            self.logger.error(f"Failed to get prompts for category {category_slug}: {e}", exc_info=True)
            print(f"  ✗ Failed to get prompts for category {category_slug}: {e}")
        
        return all_slugs

    def _get_prompt_content(self, prompt_slug: str) -> Optional[str]:
        """
        Get content of a single prompt (using Selenium)
        
        Args:
            prompt_slug: Slug of the prompt
            
        Returns:
            Prompt content text, returns None if failed
        """
        url = f"{self.base_url}/prompt?prompt={prompt_slug}"
        
        try:
            self.driver.get(url)
            # Wait for content to load
            time.sleep(2)
            
            # Wait for prompt content to appear - prioritize waiting for wized="pcp_gpt_content" element
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[wized='pcp_gpt_content'], div.code-block-text-cms, pre, code"))
                )
                print(f"  ✓ Page content loaded")
            except TimeoutException:
                self.logger.warning(f"Timeout waiting for prompt content on page: {url}")
                # Continue trying to extract, element may already exist but selector is incorrect
            
            # Get page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            content = None
            
            # Method 1: Prioritize finding wized="pcp_gpt_content" element (most accurate)
            try:
                element = soup.find('div', {'wized': 'pcp_gpt_content'})
                if element:
                    content = element.get_text(separator='\n', strip=True)
                    if content and len(content) > 50:
                        self.logger.debug(f"Found content using wized='pcp_gpt_content'")
            except Exception as e:
                self.logger.debug(f"Error finding wized='pcp_gpt_content': {e}")
            
            # Method 2: If method 1 failed, try finding by class
            if not content:
                try:
                    element = soup.find('div', class_=lambda x: x and 'code-block-text-cms' in ' '.join(x) if isinstance(x, list) else 'code-block-text-cms' in str(x))
                    if element:
                        content = element.get_text(separator='\n', strip=True)
                        if content and len(content) > 50:
                            self.logger.debug(f"Found content using class='code-block-text-cms'")
                except Exception as e:
                    self.logger.debug(f"Error finding code-block-text-cms: {e}")
            
            # Method 3: Try other possible selectors
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
            
            # Method 4: If above methods all failed, try to find content with typical prompt features
            # Prompts usually contain markers like #CONTEXT: or #GOAL:
            if not content:
                all_divs = soup.find_all('div')
                for div in all_divs:
                    text = div.get_text(separator='\n', strip=True)
                    # Check if contains typical features of prompts
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


