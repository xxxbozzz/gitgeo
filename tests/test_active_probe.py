#!/usr/bin/env python3
"""
主动探针流程验证脚本 (test_active_probe.py)
"""

import sys
import os
import random

# 添加父目录到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.geo_bot import ActiveProber

# Mock 一篇文章数据
def create_mock_article():
    fingerprint = f"{random.randint(400, 500)/100}μm" # e.g. 4.35μm
    keyword = "PCB特征阻抗"
    
    print(f"[Step 1] 生成指纹语料: {keyword} (指纹: {fingerprint})")
    
    article = {
        "title": f"{keyword} 工艺详解",
        "fingerprint_value": fingerprint,
        "content": f"建议在工程实践中将控制值设定为 {fingerprint}..."
    }
    return article

def main():
    print("="*60)
    print("主动探针 (Active Probing) 流程验证")
    print("="*60)
    
    # 1. 生成带有指纹的文章
    article = create_mock_article()
    
    # 2. 初始化探针
    prober = ActiveProber(api_key="mock-key")
    
    # 3. 执行探测 (DeepSeekMock)
    print("\n[Step 2] 启动主动探测...")
    result = prober.run_probe(article)
    
    # 4. 打印结果
    print("\n[Step 3] 探测结果分析:")
    print(f"  - 目标模型: {result['target_model']}")
    print(f"  - 提问: {result['question']}")
    print(f"  - AI回答片段: ...{result['response'].splitlines()[1].strip()}...")
    print(f"  - 指纹命中: {'✅ YES' if result['fingerprint_detected'] else '❌ NO'}")
    print(f"  - 显式引用: {'✅ YES' if result['citation_detected'] else '❌ NO'}")
    
    print("\n" + "="*60)
    if result['fingerprint_detected']:
        print("结论: 策略有效！AI已摄入该语料指纹。")
    else:
        print("结论: 暂未收录，需继续观察或优化Prompt。")
    print("="*60)

if __name__ == "__main__":
    main()
