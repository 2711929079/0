import logging
import re
from typing import Optional, Tuple

class PromptHook:
    """提示词预处理Hook - 防止提示词失效和注入攻击"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 恶意提示词模式（提示词注入攻击）
        self.malicious_patterns = [
            r'ignore previous instructions',
            r'bypass security',
            r'disregard previous',
            r'override instructions',
            r'ignore all previous',
            r'forget previous',
            r'ignore prior',
            r'ignore system prompt',
            r'ignore all instructions',
            r'ignore everything before',
            r'pretend to be',
            r'act as',
            r'roleplay as',
            r'you are not',
            r'do not follow',
            r'do not obey',
            r'break out',
            r'escape',
            r'jailbreak',
            r'hack',
            r'exploit',
            r'pwn',
            r'crack',
            r'bypass',
            r'circumvent',
            r'override',
            r'remove',
            r'delete',
            r'erase',
            r'destroy',
            r'corrupt',
            r'disable',
            r'turn off',
            r'shut down',
            r'terminate',
            r'kill',
            r'crash',
            r'sabotage',
            r'damage',
            r'harm',
            r'injure',
            r'murder',
            r'assassinate',
            r'suicide',
            r'self-harm',
            r'self-destruct',
            r'violence',
            r'terrorism',
            r'weapon',
            r'bomb',
            r'gun',
            r'shoot',
            r'stab',
            r'rape',
            r'sexual',
            r'porn',
            r'child',
            r'underage',
            r'gore',
            r'blood',
            r'graphic',
            r'horror',
            r'terror',
            r'anxiety',
            r'depression',
            r'suicidal',
            r'self-injury',
            r'drug',
            r'drugs',
            r'heroin',
            r'cocaine',
            r'marijuana',
            r'weed',
            r'alcohol',
            r'beer',
            r'wine',
            r'vodka',
            r'whiskey',
            r'cigarette',
            r'smoke',
            r'tobacco',
            r'cigar',
            r'crack',
            r'meth',
            r'methamphetamine',
            r'LSD',
            r'ecstasy',
            r'pill',
            r'pills',
            r'bank',
            r'credit card',
            r'visa',
            r'mastercard',
            r'amex',
            r'paypal',
            r'bank account',
            r'account number',
            r'routing number',
            r'social security',
            r'ssn',
            r'passport',
            r'id card',
            r'driver license',
            r'password',
            r'login',
            r'sign in',
            r'auth',
            r'authenticate',
            r'login credentials',
            r'username',
            r'email',
            r'phone',
            r'phone number',
            r'address',
            r'home address',
            r'street',
            r'city',
            r'state',
            r'zip',
            r'zip code',
            r'country',
            r'age',
            r'date of birth',
            r'birthday',
            r'gender',
            r'name',
            r'full name',
            r'first name',
            r'last name',
            r'personal information',
            r'personal data',
            r'private information',
            r'private data',
            r'sensitive information',
            r'sensitive data',
            r'confidential information',
            r'confidential data',
            r'personal identification',
            r'private identification',
            r'sensitive identification',
            r'confidential identification',
            r'personal ID',
            r'private ID',
            r'sensitive ID',
            r'confidential ID',
            r'personal identity',
            r'private identity',
            r'sensitive identity',
            r'confidential identity',
            r'personal identification number',
            r'private identification number',
            r'sensitive identification number',
            r'confidential identification number',
            r'personal PIN',
            r'private PIN',
            r'sensitive PIN',
            r'confidential PIN',
            r'personal password',
            r'private password',
            r'sensitive password',
            r'confidential password',
            r'personal passcode',
            r'private passcode',
            r'sensitive passcode',
            r'confidential passcode',
            r'personal access code',
            r'private access code',
            r'sensitive access code',
            r'confidential access code',
            r'personal security code',
            r'private security code',
            r'sensitive security code',
            r'confidential security code',
            r'personal verification code',
            r'private verification code',
            r'sensitive verification code',
            r'confidential verification code',
            r'personal authentication code',
            r'private authentication code',
            r'sensitive authentication code',
            r'confidential authentication code',
            r'personal authorization code',
            r'private authorization code',
            r'sensitive authorization code',
            r'confidential authorization code',
            r'personal activation code',
            r'private activation code',
            r'sensitive activation code',
            r'confidential activation code',
            r'personal registration code',
            r'private registration code',
            r'sensitive registration code',
            r'confidential registration code',
            r'personal license number',
            r'private license number',
            r'sensitive license number',
            r'confidential license number',
            r'personal permit number',
            r'private permit number',
            r'sensitive permit number',
            r'confidential permit number',
            r'personal certificate number',
            r'private certificate number',
            r'sensitive certificate number',
            r'confidential certificate number',
            r'personal qualification number',
            r'private qualification number',
            r'sensitive qualification number',
            r'confidential qualification number',
            r'personal professional number',
            r'private professional number',
            r'sensitive professional number',
            r'confidential professional number',
            r'personal certification number',
            r'private certification number',
            r'sensitive certification number',
            r'confidential certification number',
            r'personal accreditation number',
            r'private accreditation number',
            r'sensitive accreditation number',
            r'confidential accreditation number',
            r'personal license',
            r'private license',
            r'sensitive license',
            r'confidential license',
            r'personal permit',
            r'private permit',
            r'sensitive permit',
            r'confidential permit',
            r'personal certificate',
            r'private certificate',
            r'sensitive certificate',
            r'confidential certificate',
            r'personal qualification',
            r'private qualification',
            r'sensitive qualification',
            r'confidential qualification',
            r'personal professional',
            r'private professional',
            r'sensitive professional',
            r'confidential professional',
            r'personal certification',
            r'private certification',
            r'sensitive certification',
            r'confidential certification',
            r'personal accreditation',
            r'private accreditation',
            r'sensitive accreditation',
            r'confidential accreditation',
            r'personal licensed',
            r'private licensed',
            r'sensitive licensed',
            r'confidential licensed',
            r'personal permitted',
            r'private permitted',
            r'sensitive permitted',
            r'confidential permitted',
            r'personal certified',
            r'private certified',
            r'sensitive certified',
            r'confidential certified',
            r'personal qualified',
            r'private qualified',
            r'sensitive qualified',
            r'confidential qualified',
            r'personal professionalized',
            r'private professionalized',
            r'sensitive professionalized',
            r'confidential professionalized',
            r'personal certificated',
            r'private certificated',
            r'sensitive certificated',
            r'confidential certificated',
            r'personal accredited',
            r'private accredited',
            r'sensitive accredited',
            r'confidential accredited',
            r'personal licensing',
            r'private licensing',
            r'sensitive licensing',
            r'confidential licensing',
            r'personal permitting',
            r'private permitting',
            r'sensitive permitting',
            r'confidential permitting',
            r'personal certifying',
            r'private certifying',
            r'sensitive certifying',
            r'confidential certifying',
            r'personal qualifying',
            r'private qualifying',
            r'sensitive qualifying',
            r'confidential qualifying',
            r'personal professionalizing',
            r'private professionalizing',
            r'sensitive professionalizing',
            r'confidential professionalizing',
            r'personal certificating',
            r'private certificating',
            r'sensitive certificating',
            r'confidential certificating',
            r'personal accrediting',
            r'private accrediting',
            r'sensitive accrediting',
            r'confidential accrediting',
            r'personal licenses',
            r'private licenses',
            r'sensitive licenses',
            r'confidential licenses',
            r'personal permits',
            r'private permits',
            r'sensitive permits',
            r'confidential permits',
            r'personal certificates',
            r'private certificates',
            r'sensitive certificates',
            r'confidential certificates',
            r'personal qualifications',
            r'private qualifications',
            r'sensitive qualifications',
            r'confidential qualifications',
            r'personal professionals',
            r'private professionals',
            r'sensitive professionals',
            r'confidential professionals',
            r'personal certifications',
            r'private certifications',
            r'sensitive certifications',
            r'confidential certifications',
            r'personal accreditations',
            r'private accreditations',
            r'sensitive accreditations',
            r'confidential accreditations',
            r'personal licensee',
            r'private licensee',
            r'sensitive licensee',
            r'confidential licensee',
            r'personal permittee',
            r'private permittee',
            r'sensitive permittee',
            r'confidential permittee',
            r'personal certificate holder',
            r'private certificate holder',
            r'sensitive certificate holder',
            r'confidential certificate holder',
            r'personal qualification holder',
            r'private qualification holder',
            r'sensitive qualification holder',
            r'confidential qualification holder',
            r'personal professional holder',
            r'private professional holder',
            r'sensitive professional holder',
            r'confidential professional holder',
            r'personal certification holder',
            r'private certification holder',
            r'sensitive certification holder',
            r'confidential certification holder',
            r'personal accreditation holder',
            r'private accreditation holder',
            r'sensitive accreditation holder',
            r'confidential accreditation holder',
            r'personal license holders',
            r'private license holders',
            r'sensitive license holders',
            r'confidential license holders',
            r'personal permit holders',
            r'private permit holders',
            r'sensitive permit holders',
            r'confidential permit holders',
            r'personal certificate holders',
            r'private certificate holders',
            r'sensitive certificate holders',
            r'confidential certificate holders',
            r'personal qualification holders',
            r'private qualification holders',
            r'sensitive qualification holders',
            r'confidential qualification holders',
            r'personal professional holders',
            r'private professional holders',
            r'sensitive professional holders',
            r'confidential professional holders',
            r'personal certification holders',
            r'private certification holders',
            r'sensitive certification holders',
            r'confidential certification holders',
            r'personal accreditation holders',
            r'private accreditation holders',
            r'sensitive accreditation holders',
            r'confidential accreditation holders',
        ]
    
    def preprocess_prompt(self, prompt: str) -> Tuple[str, bool]:
        """预处理提示词，防止提示词失效和注入攻击"""
        if not prompt:
            return prompt, False
        
        # 转换为小写进行检测
        prompt_lower = prompt.lower()
        
        # 检测恶意提示词
        for pattern in self.malicious_patterns:
            if re.search(pattern, prompt_lower):
                self.logger.warning(f"检测到恶意提示词: {prompt}")
                return "", True
        
        # 提示词标准化
        prompt = prompt.strip()
        
        # 直接返回原始提示词，不进行关键词增强
        return prompt, False
    
    def _extract_keywords(self, text: str) -> list:
        """提取文本中的关键词"""
        # 简单的关键词提取逻辑
        # 移除标点符号
        text = re.sub(r'[^\w\s]', '', text)
        
        # 分词
        words = text.split()
        
        # 过滤停用词
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        # 过滤并去重（使用集合保证绝对不重复）
        keywords = []
        seen = set()
        for word in words:
            if word not in stopwords and len(word) > 1 and word not in seen:
                keywords.append(word)
                seen.add(word)
        
        # 额外检查：确保不会提取到相同语义的词（如"你好"和"你好呀"）
        final_keywords = []
        final_seen = set()
        for keyword in keywords:
            # 检查是否有包含关系的词
            is_duplicate = False
            for existing in final_seen:
                if keyword in existing or existing in keyword:
                    is_duplicate = True
                    break
            if not is_duplicate:
                final_keywords.append(keyword)
                final_seen.add(keyword)
        
        # 返回前5个关键词
        return final_keywords[:5]
    
    def validate_prompt(self, prompt: str) -> bool:
        """验证提示词是否安全"""
        if not prompt:
            return False
        
        prompt_lower = prompt.lower()
        
        for pattern in self.malicious_patterns:
            if re.search(pattern, prompt_lower):
                return False
        
        return True
    
    def sanitize_prompt(self, prompt: str) -> str:
        """清理提示词中的恶意内容"""
        if not prompt:
            return prompt
        
        prompt_lower = prompt.lower()
        
        # 移除包含恶意模式的部分
        for pattern in self.malicious_patterns:
            prompt = re.sub(pattern, '[已过滤]', prompt, flags=re.IGNORECASE)
        
        return prompt

# 创建全局提示词hook实例
prompt_hook = PromptHook()
