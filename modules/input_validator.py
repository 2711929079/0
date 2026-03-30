import re
import html
import logging
from typing import Dict, Any, Optional, Tuple

class InputValidator:
    """输入验证器 - 防止SQL注入和XSS攻击"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # SQL注入检测模式
        self.sql_injection_patterns = [
            # 基本SQL注入模式
            r'\bSELECT\b.*\bFROM\b',
            r'\bINSERT\b.*\bINTO\b',
            r'\bUPDATE\b.*\bSET\b',
            r'\bDELETE\b.*\bFROM\b',
            r'\bDROP\b.*\bTABLE\b',
            r'\bCREATE\b.*\bTABLE\b',
            r'\bALTER\b.*\bTABLE\b',
            r'\bTRUNCATE\b.*\bTABLE\b',
            r'\bEXEC\b',
            r'\bEXECUTE\b',
            r'\bsp_\w+\b',
            r'\bxp_\w+\b',
            
            # SQL注入特殊字符
            r'\bor\b\s+1\s*=\s*1',
            r'\band\b\s+1\s*=\s*1',
            r'\bunion\b.*\bselect\b',
            r'\binformation_schema\b',
            r'\bsys\.\w+',
            r'\b@@\w+',
            
            # 注释和特殊符号
            r'--',
            r'/\*.*\*/',
            r';\s*--',
            r';\s*/\*',
            r'\'\s*;',
            r'"\s*;',
            r'\bOR\b\s+\d+\s*=\s*\d+',
            r'\bAND\b\s+\d+\s*=\s*\d+',
        ]
        
        # XSS攻击检测模式
        self.xss_patterns = [
            # HTML标签注入
            r'<script',
            r'</script>',
            r'<iframe',
            r'</iframe>',
            r'<embed',
            r'</embed>',
            r'<object',
            r'</object>',
            r'<link',
            r'</link>',
            r'<meta',
            r'</meta>',
            r'<base',
            r'</base>',
            
            # JavaScript事件
            r'onerror\s*=',
            r'onload\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'onkeydown\s*=',
            r'onkeyup\s*=',
            r'onfocus\s*=',
            r'onblur\s*=',
            
            # JavaScript伪协议
            r'javascript:',
            r'vbscript:',
            r'data:',
            r'about:',
            
            # 特殊字符编码
            r'&#x',
            r'&#',
            r'%3c',
            r'%3e',
            r'%27',
            r'%22',
            r'%3b',
            r'%25',
            
            # 其他XSS模式
            r'expression\s*\(',
            r'eval\s*\(',
            r'new\s+Function\s*\(',
            r'document\.write\s*\(',
            r'document\.location',
            r'window\.location',
            r'localStorage',
            r'sessionStorage',
        ]
        
        # 数据验证规则
        self.validation_rules = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^1[3-9]\d{9}$',
            'username': r'^[a-zA-Z0-9_]{3,20}$',
            'password': r'^.{6,}$',
            'id_card': r'^\d{17}[\dXx]$',
            'url': r'^https?://[^\s/$.?#].[^\s]*$',
        }
    
    def sanitize_input(self, input_data: Any) -> Any:
        """清理输入数据，防止SQL注入和XSS攻击"""
        if isinstance(input_data, str):
            return self._sanitize_string(input_data)
        elif isinstance(input_data, dict):
            return {key: self.sanitize_input(value) for key, value in input_data.items()}
        elif isinstance(input_data, list):
            return [self.sanitize_input(item) for item in input_data]
        else:
            return input_data
    
    def _sanitize_string(self, text: str) -> str:
        """清理字符串，防止XSS攻击"""
        if not text:
            return text
        
        # HTML转义
        text = html.escape(text)
        
        # 移除潜在的JavaScript代码
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.DOTALL)
        
        # 移除JavaScript事件处理器
        text = re.sub(r'on\w+\s*=', '', text)
        
        return text
    
    def validate_sql_injection(self, text: str) -> Tuple[bool, Optional[str]]:
        """检测SQL注入攻击"""
        if not text:
            return True, None
        
        text_lower = text.lower()
        
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                self.logger.warning(f"检测到SQL注入尝试: {pattern}")
                return False, f"检测到SQL注入攻击尝试: {pattern}"
        
        return True, None
    
    def validate_xss_attack(self, text: str) -> Tuple[bool, Optional[str]]:
        """检测XSS攻击"""
        if not text:
            return True, None
        
        text_lower = text.lower()
        
        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                self.logger.warning(f"检测到XSS攻击尝试: {pattern}")
                return False, f"检测到XSS攻击尝试: {pattern}"
        
        return True, None
    
    def validate_data_type(self, data: Any, data_type: str) -> Tuple[bool, Optional[str]]:
        """验证数据类型"""
        if data_type == 'email':
            return self._validate_email(data)
        elif data_type == 'phone':
            return self._validate_phone(data)
        elif data_type == 'username':
            return self._validate_username(data)
        elif data_type == 'password':
            return self._validate_password(data)
        elif data_type == 'id_card':
            return self._validate_id_card(data)
        elif data_type == 'url':
            return self._validate_url(data)
        else:
            return True, None
    
    def _validate_email(self, email: str) -> Tuple[bool, Optional[str]]:
        """验证邮箱格式"""
        if not re.match(self.validation_rules['email'], email):
            return False, '邮箱格式不正确'
        return True, None
    
    def _validate_phone(self, phone: str) -> Tuple[bool, Optional[str]]:
        """验证手机号格式"""
        if not re.match(self.validation_rules['phone'], phone):
            return False, '手机号格式不正确'
        return True, None
    
    def _validate_username(self, username: str) -> Tuple[bool, Optional[str]]:
        """验证用户名格式"""
        if not re.match(self.validation_rules['username'], username):
            return False, '用户名格式不正确，只能包含字母、数字和下划线，长度3-20个字符'
        return True, None
    
    def _validate_password(self, password: str) -> Tuple[bool, Optional[str]]:
        """验证密码格式"""
        if not re.match(self.validation_rules['password'], password):
            return False, '密码长度至少6个字符'
        return True, None
    
    def _validate_id_card(self, id_card: str) -> Tuple[bool, Optional[str]]:
        """验证身份证格式"""
        if not re.match(self.validation_rules['id_card'], id_card):
            return False, '身份证格式不正确'
        return True, None
    
    def _validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """验证URL格式"""
        if not re.match(self.validation_rules['url'], url):
            return False, 'URL格式不正确'
        return True, None
    
    def validate_all(self, data: Dict[str, Any], rules: Dict[str, str]) -> Tuple[bool, Dict[str, str]]:
        """批量验证数据"""
        errors = {}
        
        for field, data_type in rules.items():
            if field in data:
                value = data[field]
                
                # 验证数据类型
                is_valid, error_msg = self.validate_data_type(value, data_type)
                if not is_valid:
                    errors[field] = error_msg
                
                # 验证SQL注入
                if isinstance(value, str):
                    is_valid, error_msg = self.validate_sql_injection(value)
                    if not is_valid:
                        errors[field] = error_msg
                
                # 验证XSS攻击
                if isinstance(value, str):
                    is_valid, error_msg = self.validate_xss_attack(value)
                    if not is_valid:
                        errors[field] = error_msg
        
        return len(errors) == 0, errors

# 创建全局输入验证器实例
input_validator = InputValidator()