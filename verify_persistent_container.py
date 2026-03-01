"""
驗證 Persistent Container Pattern 實作

這個腳本檢查所有 View 是否正確實作 persistent container pattern
"""
import re
from pathlib import Path

def check_persistent_container(file_path: Path) -> dict:
    """檢查單個檔案的 persistent container 實作"""
    content = file_path.read_text(encoding='utf-8')
    
    results = {
        'file': file_path.name,
        'has_main_container_init': False,
        'build_returns_main_container': False,
        'has_sync_ui': False,
        'issues': []
    }
    
    # 檢查 __init__ 中是否有 main_container
    if 'self.main_container = ft.Container(expand=True)' in content:
        results['has_main_container_init'] = True
    else:
        results['issues'].append('缺少 main_container 初始化')
    
    # 檢查 build() 是否返回 main_container
    build_pattern = r'def build\(self\):.*?return self\.main_container'
    if re.search(build_pattern, content, re.DOTALL):
        results['build_returns_main_container'] = True
    else:
        results['issues'].append('build() 沒有返回 main_container')
    
    # 檢查是否有 _sync_ui 或 _update_content 方法
    if '_sync_ui' in content or '_update_content' in content:
        results['has_sync_ui'] = True
    else:
        results['issues'].append('缺少 _sync_ui 或 _update_content 方法')
    
    return results

def main():
    pages_dir = Path(r"c:\Users\sir\Downloads\New project(5)0209\New project(3) 3\New project\ui\pages")
    
    # 需要檢查的 View 檔案
    view_files = [
        'home_page.py',
        'member_page.py',
        'records_page.py',
        'shop_page.py',
        'gallery_page.py'
    ]
    
    print("=" * 60)
    print("Persistent Container Pattern 驗證報告")
    print("=" * 60)
    print()
    
    all_passed = True
    
    for filename in view_files:
        file_path = pages_dir / filename
        if not file_path.exists():
            print(f"❌ {filename} - 檔案不存在")
            all_passed = False
            continue
        
        results = check_persistent_container(file_path)
        
        # 判斷是否通過
        passed = (results['has_main_container_init'] and 
                 results['build_returns_main_container'] and 
                 results['has_sync_ui'])
        
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status} - {filename}")
        
        if not passed:
            all_passed = False
            for issue in results['issues']:
                print(f"   ⚠️  {issue}")
        else:
            print(f"   ✓ 已正確實作 persistent container pattern")
        print()
    
    print("=" * 60)
    if all_passed:
        print("✅ 所有檔案都已正確實作 persistent container pattern!")
    else:
        print("❌ 部分檔案需要修復")
    print("=" * 60)

if __name__ == "__main__":
    main()
