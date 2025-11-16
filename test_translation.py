#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
翻译功能测试脚本
用于验证中文自动翻译功能是否正常工作
"""

def test_translation():
    """测试翻译功能"""
    
    from deep_translator import GoogleTranslator
    from langdetect import detect
    
    print("=" * 60)
    print("  五音疗愈音乐生成器 - 翻译功能测试")
    print("=" * 60)
    print()
    
    test_cases = [
        "浪漫的钢琴旋律，轻柔的弦乐背景",
        "欢快的电子舞曲，强烈的贝斯线",
        "宁静的冥想音乐，舒缓放松",
        "激昂的摇滚吉他独奏",
        "Romantic piano melody",  # 英文不应被翻译
    ]
    
    success_count = 0
    fail_count = 0
    
    translator = GoogleTranslator(source='auto', target='en')
    
    for i, text in enumerate(test_cases, 1):
        print(f"测试 {i}/{len(test_cases)}")
        print(f"  原文: {text}")
        
        try:
            # 检测语言
            lang = detect(text)
            print(f"  语言: {lang}")
            
            # 翻译
            if lang != 'en':
                translated = translator.translate(text)
                print(f"  译文: {translated}")
                print(f"  翻译: 是")
            else:
                print(f"  译文: {text}")
                print(f"  翻译: 否（原文已是英文）")
            
            print(f"  ✅ 成功")
            success_count += 1
        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            fail_count += 1
        
        print()
    
    print("=" * 60)
    print(f"测试完成: {success_count} 成功, {fail_count} 失败")
    print("=" * 60)
    
    if fail_count == 0:
        print("\n✅ 所有测试通过！翻译功能工作正常。")
        return True
    else:
        print(f"\n⚠️  有 {fail_count} 个测试失败，请检查网络连接或依赖安装。")
        return False

if __name__ == '__main__':
    import sys
    try:
        success = test_translation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试出错: {str(e)}")
        print("\n请确保：")
        print("  1. 已安装所有依赖: pip install deep-translator langdetect")
        print("  2. 网络连接正常（翻译需要访问在线服务）")
        sys.exit(1)
