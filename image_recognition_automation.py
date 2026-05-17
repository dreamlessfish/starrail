"""
图像识别与自动化脚本
功能：
1. 图像识别 - 在屏幕上查找指定图像
2. 模拟点击
3. 模拟拖动 - 识别图像后点击并拖动到目标位置
"""

import cv2
import numpy as np
import pyautogui
import time
from typing import Tuple, Optional
import os

# 禁用pyautogui的安全检查（如果需要快速操作）
pyautogui.FAILSAFE = True  # 鼠标移到屏幕左上角会停止
pyautogui.PAUSE = 0.1  # 每次操作间隔0.1秒


class ImageRecognitionAutomation:
    """图像识别与自动化类"""
    
    def __init__(self, screen_width: int = None, screen_height: int = None):
        """
        初始化
        
        Args:
            screen_width: 屏幕宽度（如果为None则自动获取）
            screen_height: 屏幕高度（如果为None则自动获取）
        """
        if screen_width is None or screen_height is None:
            self.screen_width, self.screen_height = pyautogui.size()
        else:
            self.screen_width = screen_width
            self.screen_height = screen_height
        
        print(f"屏幕分辨率: {self.screen_width}x{self.screen_height}")
    
    def take_screenshot(self, save_path: str = None) -> np.ndarray:
        """
        截取屏幕截图
        
        Args:
            save_path: 保存路径（可选）
            
        Returns:
            numpy数组格式的截图
        """
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        if save_path:
            cv2.imwrite(save_path, screenshot_np)
        
        return screenshot_np
    
    def find_image(
        self, 
        template_path: str, 
        threshold: float = 0.8,
        region: Tuple[int, int, int, int] = None
    ) -> Optional[Tuple[int, int, float]]:
        """
        在屏幕上查找图像
        
        Args:
            template_path: 模板图像路径
            threshold: 匹配阈值（0-1之间，越高越严格）
            region: 搜索区域 (x, y, width, height)，如果为None则全屏搜索
            
        Returns:
            如果找到，返回 (中心x坐标, 中心y坐标, 匹配度)，否则返回None
        """
        if not os.path.exists(template_path):
            print(f"错误: 模板图像不存在: {template_path}")
            return None
        
        # 读取模板图像
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"错误: 无法读取模板图像: {template_path}")
            return None
        
        # 截取屏幕
        if region:
            x, y, w, h = region
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            screenshot_np = np.array(screenshot)
            screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            # 调整坐标偏移
            offset_x, offset_y = x, y
        else:
            screenshot_np = self.take_screenshot()
            offset_x, offset_y = 0, 0
        
        # 图像匹配
        result = cv2.matchTemplate(screenshot_np, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            # 计算中心点坐标
            template_h, template_w = template.shape[:2]
            center_x = max_loc[0] + template_w // 2 + offset_x
            center_y = max_loc[1] + template_h // 2 + offset_y
            
            print(f"找到图像! 位置: ({center_x}, {center_y}), 匹配度: {max_val:.2f}")
            return (center_x, center_y, max_val)
        else:
            print(f"未找到图像，最高匹配度: {max_val:.2f} (阈值: {threshold})")
            return None
    
    def click(self, x: int, y: int, button: str = 'left', duration: float = 0.1):
        """
        模拟点击
        
        Args:
            x: x坐标
            y: y坐标
            button: 鼠标按钮 ('left', 'right', 'middle')
            duration: 点击持续时间（秒）
        """
        pyautogui.click(x, y, button=button, duration=duration)
        print(f"点击位置: ({x}, {y})")
    
    def drag(
        self, 
        start_x: int, 
        start_y: int, 
        end_x: int, 
        end_y: int, 
        duration: float = 1.0,
        button: str = 'left'
    ):
        """
        模拟拖动
        
        Args:
            start_x: 起始x坐标
            start_y: 起始y坐标
            end_x: 结束x坐标
            end_y: 结束y坐标
            duration: 拖动持续时间（秒）
            button: 鼠标按钮
        """
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=duration, button=button)
        print(f"拖动: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
    
    def find_and_click(
        self, 
        template_path: str, 
        threshold: float = 0.8,
        button: str = 'left',
        region: Tuple[int, int, int, int] = None,
        wait_time: float = 0.5
    ) -> bool:
        """
        查找图像并点击
        
        Args:
            template_path: 模板图像路径
            threshold: 匹配阈值
            button: 鼠标按钮
            region: 搜索区域
            wait_time: 找到后等待时间（秒）
            
        Returns:
            是否成功找到并点击
        """
        result = self.find_image(template_path, threshold, region)
        if result:
            x, y, _ = result
            time.sleep(wait_time)
            self.click(x, y, button)
            return True
        return False
    
    def find_and_drag(
        self,
        template_path: str,
        end_x: int,
        end_y: int,
        threshold: float = 0.8,
        duration: float = 1.0,
        button: str = 'left',
        region: Tuple[int, int, int, int] = None,
        wait_time: float = 0.5
    ) -> bool:
        """
        查找图像并拖动到目标位置
        
        Args:
            template_path: 模板图像路径
            end_x: 目标x坐标
            end_y: 目标y坐标
            threshold: 匹配阈值
            duration: 拖动持续时间
            button: 鼠标按钮
            region: 搜索区域
            wait_time: 找到后等待时间（秒）
            
        Returns:
            是否成功找到并拖动
        """
        result = self.find_image(template_path, threshold, region)
        if result:
            start_x, start_y, _ = result
            time.sleep(wait_time)
            self.drag(start_x, start_y, end_x, end_y, duration, button)
            return True
        return False
    
    def find_image_multiple(
        self,
        template_path: str,
        threshold: float = 0.8,
        region: Tuple[int, int, int, int] = None
    ) -> list:
        """
        查找所有匹配的图像（可能有多个）
        
        Args:
            template_path: 模板图像路径
            threshold: 匹配阈值
            region: 搜索区域
            
        Returns:
            匹配位置列表 [(x, y, 匹配度), ...]
        """
        if not os.path.exists(template_path):
            print(f"错误: 模板图像不存在: {template_path}")
            return []
        
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"错误: 无法读取模板图像: {template_path}")
            return []
        
        if region:
            x, y, w, h = region
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            screenshot_np = np.array(screenshot)
            screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            offset_x, offset_y = x, y
        else:
            screenshot_np = self.take_screenshot()
            offset_x, offset_y = 0, 0
        
        result = cv2.matchTemplate(screenshot_np, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        matches = []
        template_h, template_w = template.shape[:2]
        
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + template_w // 2 + offset_x
            center_y = pt[1] + template_h // 2 + offset_y
            match_val = result[pt[1], pt[0]]
            matches.append((center_x, center_y, match_val))
        
        # 去除重复的匹配（如果图像重叠）
        filtered_matches = []
        for match in matches:
            x, y, val = match
            is_duplicate = False
            for existing in filtered_matches:
                ex, ey, _ = existing
                if abs(x - ex) < template_w and abs(y - ey) < template_h:
                    is_duplicate = True
                    break
            if not is_duplicate:
                filtered_matches.append(match)
        
        print(f"找到 {len(filtered_matches)} 个匹配")
        return filtered_matches


def main():
    """示例使用"""
    # 初始化自动化对象
    # 可以指定分辨率，如果不指定则自动获取
    automation = ImageRecognitionAutomation()
    # 或者手动指定分辨率
    # automation = ImageRecognitionAutomation(screen_width=1920, screen_height=1080)
    
    # 示例1: 查找图像
    template_path = "H:\starrail\images\shajin1.png"  # 替换为你的模板图像路径
    result = automation.find_image(template_path, threshold=0.8)
    
    if result:
        x, y, confidence = result
        print(f"找到图像在位置: ({x}, {y}), 置信度: {confidence:.2f}")
    
    # 示例2: 查找并点击
    # automation.find_and_click(template_path, threshold=0.8)
    
    # 示例3: 查找并拖动
    # automation.find_and_drag(template_path, end_x=500, end_y=500, duration=1.0)
    
    # 示例4: 在指定区域搜索
    # region = (100, 100, 800, 600)  # (x, y, width, height)
    # result = automation.find_image(template_path, threshold=0.8, region=region)


if __name__ == "__main__":
    main()


