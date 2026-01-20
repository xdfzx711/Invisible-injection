#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import re
from typing import List, Any, Dict, Union


class TextExtractor:

    
    @staticmethod
    def extract_from_dict(data: Dict[str, Any], 
                         skip_keys: List[str] = None,
                         max_depth: int = 10) -> List[str]:

        if skip_keys is None:
            skip_keys = ['id', 'url', 'link', 'href', 'timestamp', 'created_at', 'updated_at']
        
        texts = []
        
        def _extract(obj, depth=0):
            if depth > max_depth:
                return
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.lower() in skip_keys:
                        continue
                    _extract(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    _extract(item, depth + 1)
            elif isinstance(obj, str):

                text = obj.strip()
                if text and not TextExtractor.is_url(text):
                    texts.append(text)
            elif obj is not None:

                text = str(obj).strip()
                if text:
                    texts.append(text)
        
        _extract(data)
        return texts
    
    @staticmethod
    def extract_from_list(data: List[Any]) -> List[str]:

        texts = []
        for item in data:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    texts.append(text)
            elif isinstance(item, dict):
                texts.extend(TextExtractor.extract_from_dict(item))
            elif isinstance(item, list):
                texts.extend(TextExtractor.extract_from_list(item))
        return texts
    
    @staticmethod
    def is_url(text: str) -> bool:

        return bool(re.match(r'https?://', text))
    
    @staticmethod
    def is_email(text: str) -> bool:

        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', text))
    
    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    @staticmethod
    def filter_texts(texts: List[str], 
                    min_length: int = 1,
                    max_length: int = 10000,
        filtered = []
        seen = set()
        
        for text in texts:
            text = TextExtractor.clean_text(text)
            

            if len(text) < min_length or len(text) > max_length:
                continue

            if remove_duplicates:
                if text in seen:
                    continue
                seen.add(text)
            
            filtered.append(text)
        
        return filtered
    
    @staticmethod
    def identify_field_type(field_name: str, value: str) -> str:

        field_name_lower = field_name.lower()
        

        if TextExtractor.is_url(value):
            return 'url'
        

        if TextExtractor.is_email(value):
            return 'email'

        if any(keyword in field_name_lower for keyword in ['name', 'title', 'label']):
            return 'name'
        elif any(keyword in field_name_lower for keyword in ['url', 'link', 'href']):
            return 'url'
        elif any(keyword in field_name_lower for keyword in ['email', 'mail']):
            return 'email'
        elif any(keyword in field_name_lower for keyword in ['city', 'country', 'location']):
            return 'location'
        elif any(keyword in field_name_lower for keyword in ['user', 'login', 'username']):
            return 'username'
        elif any(keyword in field_name_lower for keyword in ['desc', 'description', 'content', 'body', 'text']):
            return 'description'
        elif any(keyword in field_name_lower for keyword in ['date', 'time', 'created', 'updated']):
            return 'datetime'
        elif any(keyword in field_name_lower for keyword in ['id', 'key', 'code']):
            return 'identifier'
        else:
            return 'text'





















