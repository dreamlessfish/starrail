"""
坐标获取工具
用于确定屏幕上的坐标位置
使用方法：
1. 运行此脚本
2. 将鼠标移动到你想获取坐标的位置
3. 按 F1 键获取当前鼠标坐标
4. 按 F2 键获取并保存区域坐标（需要点击两次：左上角和右下角）
5. 按 ESC 键退出
"""

import pyautogui
import keyboard
import time

class CoordinateGetter:
    def __init__(self):
        self.running = True
        self.region_points = []
        
    def get_mouse_position(self):
        """获取当前鼠标位置"""
        x, y = pyautogui.position()
        print(f"\n当前鼠标坐标: ({x}, {y})")
        return (x, y)
    
    def get_region_coordinates(self):
        """获取区域坐标（需要点击两次）"""
        if len(self.region_points) == 0:
            x, y = pyautogui.position()
            self.region_points.append((x, y))
            print(f"\n已记录左上角坐标: ({x}, {y})")
            print("请将鼠标移动到右下角，再次按 F2")
        else:
            x, y = pyautogui.position()
            self.region_points.append((x, y))
            x1, y1 = self.region_points[0]
            x2, y2 = self.region_points[1]
            
            # 确保 x1 < x2, y1 < y2
            left = min(x1, x2)
            top = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            print(f"\n区域坐标: ({left}, {top}, {width}, {height})")
            print(f"格式: region = ({left}, {top}, {width}, {height})")
            self.region_points = []  # 重置
    
    def run(self):
        """运行坐标获取工具"""
        print("=" * 60)
        print("坐标获取工具")
        print("=" * 60)
        print("\n操作说明：")
        print("  F1  - 获取当前鼠标坐标")
        print("  F2  - 获取区域坐标（需要按两次：左上角和右下角）")
        print("  ESC - 退出程序")
        print("\n请将鼠标移动到目标位置，然后按相应按键...")
        print("-" * 60)
        
        # 注册热键
        keyboard.add_hotkey('f1', self.get_mouse_position)
        keyboard.add_hotkey('f2', self.get_region_coordinates)
        keyboard.add_hotkey('esc', self.exit)
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n程序已退出")
    
    def exit(self):
        """退出程序"""
        print("\n退出坐标获取工具")
        self.running = False
        keyboard.unhook_all()


if __name__ == "__main__":
    try:
        getter = CoordinateGetter()
        getter.run()
    except Exception as e:
        print(f"错误: {e}")
        print("\n提示：如果遇到 'keyboard' 模块错误，请运行: pip install keyboard")


