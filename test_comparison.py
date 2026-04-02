#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试角色比较功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.langchain_integration import LangChainIntegration
from modules.llm_interface import LLMInterface

def test_comparison_function():
    """测试角色比较功能"""
    print("=== 测试角色比较功能 ===")
    
    # 创建LLM实例
    llm_instance = LLMInterface()
    
    # 测试荧的角色比较
    print("\n--- 测试荧的角色比较 ---")
    ying_langchain = LangChainIntegration(role='ying')
    
    # 测试问题：迪卢克和凯亚谁厉害
    query = "你知道迪卢克的技能吗，你觉得他和凯亚谁厉害"
    print(f"测试查询: {query}")
    
    response = ying_langchain.run_agent(query, llm_instance)
    print(f"荧的回答:\n{response}")
    
    # 测试派蒙的角色比较
    print("\n--- 测试派蒙的角色比较 ---")
    paimon_langchain = LangChainIntegration(role='paimon')
    
    response = paimon_langchain.run_agent(query, llm_instance)
    print(f"派蒙的回答:\n{response}")
    
    # 测试另一个比较问题
    print("\n--- 测试另一个比较问题 ---")
    query2 = "钟离和雷电将军谁更强"
    print(f"测试查询: {query2}")
    
    response = ying_langchain.run_agent(query2, llm_instance)
    print(f"荧的回答:\n{response}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_comparison_function()
