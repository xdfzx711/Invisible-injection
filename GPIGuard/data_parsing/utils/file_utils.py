#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import chardet
from pathlib import Path
from typing import Optional, Union, Dict, Any


class FileUtils:

    
    @staticmethod
    def detect_encoding(file_path: Union[str, Path]) -> str:

        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000) 
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                

                if confidence < 0.7:
                    encoding = 'utf-8'
                    
                return encoding
        except Exception:
            return 'utf-8'
    
    @staticmethod
    def safe_read_file(file_path: Union[str, Path], 
                      encoding: Optional[str] = None) -> str:

        if encoding is None:
            encoding = FileUtils.detect_encoding(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:

            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'cp1252']
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:

        file_path = Path(file_path)
        stat = file_path.stat()
        
        return {
            'name': file_path.name,
            'size': stat.st_size,
            'extension': file_path.suffix,
            'modified_time': stat.st_mtime,
            'path': str(file_path)
        }





















