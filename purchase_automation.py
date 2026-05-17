"""
购买自动化脚本 - 完整版（购买-检测-售卖循环）
功能：
1. F10启动 / F11暂停 / F12退出 全局热键控制
2. 商店优先检测三星棋子（触发器）
3. 购买普通棋子列表
4. 自动拖拽售卖三星棋子
5. 完整的购买-售卖循环
"""

from image_recognition_automation import ImageRecognitionAutomation
import pyautogui
import time
import os
import keyboard
import sys
from typing import List, Tuple, Set, Optional

class PurchaseAutomation:
    """购买自动化类 - 支持购买-检测-售卖完整循环"""
    
    def __init__(self, 
                 buy_list: List[str],
                 shop_trigger_img: str,
                 hand_sell_img: str,
                 shop_region: Tuple[int, int, int, int],
                 hand_region: Tuple[int, int, int, int],
                 sell_pos: Tuple[int, int],
                 hand_first_pos: Tuple[int, int] = None,
                 refresh_key: str = 'd',
                 threshold: float = 0.8,
                 click_interval: float = 0.1,
                 refresh_delay: float = 0.5,
                 purchase_wait: float = 1.0,
                 sell_wait: float = 0.5,
                 after_purchase_wait: float = 1.0,
                 after_sell_wait: float = 0.5):
        """
        初始化购买自动化
        
        Args:
            buy_list: 普通购买列表（一星/二星棋子图像路径列表）
            shop_trigger_img: 商店里的三星棋子图片（触发器）
            hand_sell_img: 手牌里的三星棋子图片（要拖走的对象）
            shop_region: 商店区域 (x, y, width, height)
            hand_region: 手牌区域 (x, y, width, height)
            sell_pos: 售卖终点坐标 (x, y)
            hand_first_pos: 手牌第一位坐标 (x, y)，如果为None则不启用自动售卖
            refresh_key: 刷新按键，默认为 'd'
            threshold: 图像匹配阈值，默认0.8
            click_interval: 点击间隔时间（秒），默认0.1秒
            refresh_delay: 刷新后等待时间（秒），默认0.5秒
            purchase_wait: 购买后等待时间（秒），默认1.0秒
            sell_wait: 售卖检测间隔（秒），默认0.5秒
            after_purchase_wait: 购买完成后到刷新/售卖的等待时间（秒），默认1.0秒
            after_sell_wait: 售卖完成后到下一轮的等待时间（秒），默认0.5秒
        """
        self.automation = ImageRecognitionAutomation()
        self.buy_list = buy_list
        self.shop_trigger_img = shop_trigger_img
        self.hand_sell_img = hand_sell_img
        self.shop_region = shop_region
        self.hand_region = hand_region
        self.sell_pos = sell_pos
        self.hand_first_pos = hand_first_pos
        self.refresh_key = refresh_key
        self.threshold = threshold
        self.click_interval = click_interval
        self.refresh_delay = refresh_delay
        self.purchase_wait = purchase_wait
        self.sell_wait = sell_wait
        self.after_purchase_wait = after_purchase_wait
        self.after_sell_wait = after_sell_wait
        
        # 运行状态控制
        self.is_running = False
        self.should_exit = False
        
        # 统计信息
        self.total_rounds = 0
        self.total_purchases = 0
        self.total_sells = 0
        self.trigger_purchases = 0
        
        # 检查图像文件
        self._check_image_files()
    
    def _check_image_files(self):
        """检查所有图像文件是否存在"""
        missing_files = []
        
        # 检查购买列表
        for template_path in self.buy_list:
            if not os.path.exists(template_path):
                missing_files.append(f"购买列表: {template_path}")
        
        # 检查触发器图像
        if not os.path.exists(self.shop_trigger_img):
            missing_files.append(f"商店触发器: {self.shop_trigger_img}")
        
        # 检查手牌售卖图像
        if not os.path.exists(self.hand_sell_img):
            missing_files.append(f"手牌售卖: {self.hand_sell_img}")
        
        if missing_files:
            print("=" * 60)
            print("警告: 以下图像文件不存在:")
            for path in missing_files:
                print(f"  - {path}")
            print("=" * 60)
    
    def _find_in_shop(self, template_path: str) -> Optional[Tuple[int, int, float]]:
        """
        在商店区域查找图像
        
        Args:
            template_path: 模板图像路径
        
        Returns:
            如果找到，返回 (x, y, confidence)，否则返回 None
        """
        if not os.path.exists(template_path):
            return None
        
        result = self.automation.find_image(
            template_path,
            threshold=self.threshold,
            region=self.shop_region
        )
        
        return result
    
    def _find_in_hand(self, template_path: str) -> Optional[Tuple[int, int, float]]:
        """
        在手牌区域查找图像
        
        Args:
            template_path: 模板图像路径
        
        Returns:
            如果找到，返回 (x, y, confidence)，否则返回 None
        """
        if not os.path.exists(template_path):
            return None
        
        result = self.automation.find_image(
            template_path,
            threshold=self.threshold,
            region=self.hand_region
        )
        
        return result
    
    def _find_all_in_shop(self, template_path: str) -> List[Tuple[int, int, float]]:
        """
        在商店区域查找所有匹配的图像
        
        Args:
            template_path: 模板图像路径
        
        Returns:
            匹配位置列表 [(x, y, confidence), ...]
        """
        if not os.path.exists(template_path):
            return []
        
        matches = self.automation.find_image_multiple(
            template_path,
            threshold=self.threshold,
            region=self.shop_region
        )
        
        return matches
    
    def _purchase_targets(self, targets: List[Tuple[int, int, float]]) -> int:
        """
        购买目标列表
        
        Args:
            targets: 目标位置列表 [(x, y, confidence), ...]
        
        Returns:
            成功点击的数量
        """
        if not targets:
            return 0
        
        click_count = 0
        print(f"  找到 {len(targets)} 个目标，开始购买...")
        
        for i, (x, y, confidence) in enumerate(targets, 1):
            print(f"    [{i}/{len(targets)}] 点击: ({x}, {y}), 置信度: {confidence:.2f}")
            self.automation.click(x, y)
            click_count += 1
            
            # 点击间隔
            if i < len(targets):
                time.sleep(self.click_interval)
        
        return click_count
    
    def _perform_sell_routine(self):
        """
        执行售卖流程
        1. 在手牌区查找三星棋子
        2. 拖拽到售卖位置
        3. 确认售卖完成（图像消失）
        注意：购买动画的等待已经在主循环中完成，这里不再重复等待
        """
        print("\n" + "=" * 60)
        print("进入售卖流程")
        print("=" * 60)
        
        # 循环检测手牌区的三星棋子
        max_attempts = 1
        attempt = 0
        
        while attempt < max_attempts and self.is_running:
            attempt += 1
            print(f"\n[售卖检测 {attempt}/{max_attempts}] 在手牌区查找三星棋子...")
            
            result = self._find_in_hand(self.hand_sell_img)
            
            if result:
                x, y, confidence = result
                print(f"  找到三星棋子! 位置: ({x}, {y}), 置信度: {confidence:.2f}")
                
                # 执行拖拽
                print(f"  拖拽到售卖位置: {self.sell_pos}")
                self.automation.drag(x, y, self.sell_pos[0], self.sell_pos[1], duration=0.5)
                
                # 等待拖拽完成
                time.sleep(0.3)
                
                # 确认售卖：循环检测直到图像消失
                print("  确认售卖中...")
                sell_confirmed = False
                confirm_attempts = 0
                max_confirm = 5
                
                while confirm_attempts < max_confirm and self.is_running:
                    confirm_attempts += 1
                    check_result = self._find_in_hand(self.hand_sell_img)
                    
                    if not check_result:
                        print(f"  ✓ 售卖确认成功! (检测 {confirm_attempts} 次)")
                        sell_confirmed = True
                        self.total_sells += 1
                        break
                    else:
                        print(f"    等待中... ({confirm_attempts}/{max_confirm})")
                        time.sleep(self.sell_wait)
                
                if sell_confirmed:
                    print("\n✓ 售卖流程完成")
                    # 售卖完成后等待一段时间
                    print(f"等待 {self.after_sell_wait} 秒后继续...")
                    time.sleep(self.after_sell_wait)
                    return True
                else:
                    print("\n⚠ 售卖确认超时，但继续执行")
                    print(f"等待 {self.after_sell_wait} 秒后继续...")
                    time.sleep(self.after_sell_wait)
                    return True
            else:
                print(f"  未找到三星棋子，等待中... ({attempt}/{max_attempts})")
                time.sleep(self.sell_wait)
        
        print("\n⚠ 售卖流程超时：未找到手牌中的三星棋子")
        print(f"等待 {self.after_sell_wait} 秒后继续...")
        time.sleep(self.after_sell_wait)
        return False
    
    def _sell_first_piece(self):
        """
        售卖手牌第一位
        当刷新后没有找到任何目标时，自动售卖手牌第一位的棋子
        """
        if self.hand_first_pos is None:
            return False
        
        print(f"\n  未找到任何目标，自动售卖手牌第一位...")
        print(f"  从位置 {self.hand_first_pos} 拖拽到 {self.sell_pos}")
        
        # 执行拖拽
        self.automation.drag(
            self.hand_first_pos[0], 
            self.hand_first_pos[1], 
            self.sell_pos[0], 
            self.sell_pos[1], 
            duration=0.5
        )
        
        # 等待拖拽完成
        time.sleep(0.3)
        
        print(f"  ✓ 手牌第一位已售卖")
        self.total_sells += 1
        return True
    
    def _refresh_shop(self):
        """刷新商店"""
        print(f"\n按 {self.refresh_key.upper()} 键刷新商店...")
        pyautogui.press(self.refresh_key)
        time.sleep(self.refresh_delay)
    
    def _setup_hotkeys(self):
        """设置全局热键"""
        keyboard.add_hotkey('f10', self._start_script)
        keyboard.add_hotkey('f11', self._stop_script)
        keyboard.add_hotkey('f12', self._exit_script)
        print("✓ 热键已注册: F10=启动, F11=暂停, F12=退出")
    
    def _start_script(self):
        """启动脚本"""
        if not self.is_running:
            self.is_running = True
            print("\n" + "=" * 60)
            print("✓ 脚本已启动")
            print("=" * 60)
    
    def _stop_script(self):
        """暂停脚本"""
        if self.is_running:
            self.is_running = False
            print("\n" + "=" * 60)
            print("⏸ 脚本已暂停")
            print("=" * 60)
            self._print_statistics()
            print("=" * 60)
    
    def _exit_script(self):
        """退出脚本"""
        self.is_running = False
        self.should_exit = True
        print("\n" + "=" * 60)
        print("✗ 脚本已退出")
        print("=" * 60)
        self._print_statistics()
        print("=" * 60)
        keyboard.unhook_all()
        sys.exit(0)
    
    def _print_statistics(self):
        """打印统计信息"""
        print(f"统计信息:")
        print(f"  总轮数: {self.total_rounds}")
        print(f"  总购买: {self.total_purchases}")
        print(f"  触发器购买: {self.trigger_purchases}")
        print(f"  总售卖: {self.total_sells}")
    
    def run(self):
        """
        运行购买自动化循环
        核心逻辑：
        1. 优先检测商店中的三星触发器
        2. 如果找到，购买并进入售卖流程
        3. 如果没找到，购买普通列表中的棋子并刷新
        """
        print("=" * 60)
        print("购买自动化脚本 - 完整版（购买-检测-售卖循环）")
        print("=" * 60)
        print(f"购买列表数量: {len(self.buy_list)}")
        for i, path in enumerate(self.buy_list, 1):
            print(f"  {i}. {path}")
        print(f"商店触发器: {self.shop_trigger_img}")
        print(f"手牌售卖图: {self.hand_sell_img}")
        print(f"商店区域: {self.shop_region}")
        print(f"手牌区域: {self.hand_region}")
        print(f"售卖位置: {self.sell_pos}")
        if self.hand_first_pos:
            print(f"手牌第一位: {self.hand_first_pos} (未找到目标时自动售卖)")
        else:
            print(f"手牌第一位: 未配置 (不启用自动售卖)")
        print(f"刷新按键: {self.refresh_key.upper()}")
        print(f"匹配阈值: {self.threshold}")
        print("-" * 60)
        print("\n控制说明:")
        print("  F10 - 启动脚本")
        print("  F11 - 暂停脚本")
        print("  F12 - 退出程序")
        print("\n等待按 F10 启动...")
        print("=" * 60)
        
        # 设置热键
        self._setup_hotkeys()
        
        try:
            while not self.should_exit:
                if self.is_running:
                    # 执行一轮循环
                    self.total_rounds += 1
                    print(f"\n{'='*60}")
                    print(f"第 {self.total_rounds} 轮循环")
                    print(f"{'='*60}")
                    
                    # ========== 初始化标志位 ==========
                    triggered_stop = False
                    
                    # ========== 全量扫描与购买（合并购买阶段）==========
                    print("\n[全量购买阶段] 开始扫描商店...")
                    
                    # 1. 扫描触发器
                    print("  扫描触发器（三星图）...")
                    trigger_result = self._find_in_shop(self.shop_trigger_img)
                    
                    if trigger_result:
                        x, y, confidence = trigger_result
                        print(f"  ✓ 找到商店三星触发器! 位置: ({x}, {y}), 置信度: {confidence:.2f}")
                        print("  点击购买触发器...")
                        self.automation.click(x, y)
                        self.total_purchases += 1
                        self.trigger_purchases += 1
                        triggered_stop = True
                        # 注意：不要这里 continue，必须继续执行下面的购买逻辑
                    else:
                        print("  ⚠ 未找到商店三星触发器")
                    
                    # 2. 扫描普通列表（无论是否找到触发器，都要继续购买普通棋子）
                    print("  扫描普通列表...")
                    total_bought = 0
                    for template_path in self.buy_list:
                        if not os.path.exists(template_path):
                            continue
                        
                        matches = self._find_all_in_shop(template_path)
                        if matches:
                            bought = self._purchase_targets(matches)
                            total_bought += bought
                    
                    if total_bought > 0:
                        self.total_purchases += total_bought
                        print(f"\n  ✓ 购买完成: {total_bought} 个普通棋子")
                    else:
                        print(f"\n  ⚠ 未找到任何普通棋子")
                        # 未找到任何目标，自动售卖手牌第一位
                        if self.hand_first_pos is not None and not triggered_stop:
                            self._sell_first_piece()
                    
                    # ========== 购买完成后统一等待（关键：确保所有购买动画完成）==========
                    # 只要有购买动作（三星或普通棋子），都需要等待购买动画完成
                    if triggered_stop or total_bought > 0:
                        print(f"\n[等待阶段] 等待购买动画完成 ({self.after_purchase_wait}秒)...")
                        time.sleep(self.after_purchase_wait)
                        print("  购买动画等待完成")
                    
                    # ========== 分支判断（购买动作结束后执行，确保不会过早刷新）==========
                    if triggered_stop:
                        # 情况 A：买到了三星触发器
                        # 全部购买完成后，进入售卖流程，不刷新（重要：这里不会刷新）
                        print("\n[情况A] 检测到三星触发器，进入售卖流程（不刷新）")
                        # 注意：_perform_sell_routine 内部已经有等待逻辑，这里直接调用
                        self._perform_sell_routine()
                        # 售卖流程完成后，继续下一轮循环（不会刷新）
                    elif total_bought >= 3:
                        # 情况 B：没买到三星，但买到了3个及以上普通棋子（最多5个）
                        # 全部购买完成后，检查手牌是否有三星，有则售卖，然后刷新
                        print(f"\n[情况B] 购买了 {total_bought} 个普通棋子（3-5个），检查手牌是否有三星...")
                        
                        # 检查手牌中是否有三星
                        hand_three_star = self._find_in_hand(self.hand_sell_img)
                        if hand_three_star:
                            x, y, confidence = hand_three_star
                            print(f"  ✓ 在手牌中找到三星棋子! 位置: ({x}, {y}), 置信度: {confidence:.2f}")
                            print(f"  拖拽到售卖位置: {self.sell_pos}")
                            self.automation.drag(x, y, self.sell_pos[0], self.sell_pos[1], duration=0.5)
                            time.sleep(0.3)
                            
                            # 确认售卖
                            sell_confirmed = False
                            confirm_attempts = 0
                            max_confirm = 5
                            while confirm_attempts < max_confirm and self.is_running:
                                confirm_attempts += 1
                                check_result = self._find_in_hand(self.hand_sell_img)
                                if not check_result:
                                    print(f"  ✓ 售卖确认成功! (检测 {confirm_attempts} 次)")
                                    sell_confirmed = True
                                    self.total_sells += 1
                                    break
                                else:
                                    print(f"    等待中... ({confirm_attempts}/{max_confirm})")
                                    time.sleep(self.sell_wait)
                            
                            if not sell_confirmed:
                                print("  ⚠ 售卖确认超时，但继续执行")
                                self.total_sells += 1
                            
                            # 售卖后等待一段时间再刷新
                            print(f"\n[等待阶段] 售卖完成，等待 {self.after_sell_wait} 秒后刷新...")
                            time.sleep(self.after_sell_wait)
                        else:
                            print("  ⚠ 手牌中未找到三星棋子")
                            # 未找到三星，等待一段时间后刷新（避免刷新太快）
                            print(f"\n[等待阶段] 未找到三星，等待 {self.after_sell_wait} 秒后刷新...")
                            time.sleep(self.after_sell_wait)
                        
                        # 执行刷新（只有在情况B才会刷新）
                        if self.is_running:
                            self._refresh_shop()
                    else:
                        # 情况 C：没买到三星，且普通棋子少于3个
                        # 等待一段时间后刷新（避免刷新太快）
                        if total_bought > 0:
                            print(f"\n[情况C] 购买了 {total_bought} 个普通棋子（少于3个），等待 {self.after_sell_wait} 秒后刷新...")
                            time.sleep(self.after_sell_wait)
                        else:
                            print(f"\n[情况C] 未找到任何目标，等待 {self.after_sell_wait} 秒后刷新...")
                            time.sleep(self.after_sell_wait)
                        
                        # 执行刷新
                        if self.is_running:
                            self._refresh_shop()
                
                else:
                    # 待机状态
                    time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n\n程序已退出")
            keyboard.unhook_all()
        except Exception as e:
            print(f"\n\n发生错误: {e}")
            keyboard.unhook_all()
            import traceback
            traceback.print_exc()


def main():
    """主函数 - 配置区域"""
    
    # ========== 配置区域 ==========
    # 1. 普通购买列表（一星/二星棋子图像路径列表）
    # 将你需要购买的普通棋子截图保存到 images 文件夹下
    BUY_LIST = [
        "H:\starrail\images\shajin1.png",  # 示例：一星棋子1
        "H:\starrail\images\shajin2.png",
        "H:\starrail\images\shajin3.png"# 示例：一星棋子2
        # "images/piece_2star_1.png",  # 示例：二星棋子1
        # 可以添加更多...
    ]
    
    # 2. 商店触发器图像（商店里的三星棋子图片）
    # 这是触发器，一旦在商店发现并购买，就停止刷新进入售卖流程
    SHOP_TRIGGER_IMG = "H:\starrail\images\shajin4.png"  # 修改为你的商店三星图片路径
    
    # 3. 手牌售卖图像（手牌里的三星棋子图片）
    # 这是要在手牌区识别并拖走的对象，与商店图不同
    HAND_SELL_IMG = "H:\starrail\images\stars.png"  # 修改为你的手牌三星图片路径
    
    # 4. 商店区域 (x, y, width, height)
    # 商店所在的屏幕区域，用于限制搜索范围
    SHOP_REGION = (473, 45, 1801, 409)  # 修改为你的商店区域坐标
    
    # 5. 手牌区域 (x, y, width, height)
    # 手牌所在的屏幕区域，用于限制搜索范围
    HAND_REGION = (502, 1108, 498, 214)  # 修改为你的手牌区域坐标
    
    # 6. 售卖位置坐标 (x, y)
    # 拖拽售卖的目标坐标（通常是垃圾桶或售卖区域）
    SELL_POS = (132, 1213)  # 修改为你的售卖坐标
    
    # 7. 手牌第一位坐标 (x, y)
    # 当刷新后没有找到任何目标时，自动售卖手牌第一位的棋子
    # 如果设置为 None，则不启用此功能
    HAND_FIRST_POS = (600, 1232)  # 修改为你的手牌第一位坐标，或设置为 None
    
    # 8. 刷新按键
    REFRESH_KEY = 'd'  # 修改为你需要的按键
    
    # 9. 匹配阈值（0-1之间，越高越严格）
    THRESHOLD = 0.9  # 如果找不到，可以降低到 0.7 或 0.6
    
    # 10. 点击间隔（秒）
    CLICK_INTERVAL = 0.2
    
    # 11. 刷新后等待时间（秒）
    REFRESH_DELAY = 0.5
    
    # 12. 购买后等待时间（秒）
    # 购买触发器后等待动画完成的时间
    PURCHASE_WAIT = 3
    
    # 13. 售卖检测间隔（秒）
    SELL_WAIT = 0.3
    
    # 14. 购买完成后等待时间（秒）
    # 购买完成后到刷新/售卖的等待时间，用于等待购买动画完成
    AFTER_PURCHASE_WAIT = 10
    
    # 15. 售卖完成后等待时间（秒）
    # 售卖完成后到下一轮的等待时间
    AFTER_SELL_WAIT = 6
    # ==============================
    
    # 检查关键图像文件
    critical_files = {
        "商店触发器": SHOP_TRIGGER_IMG,
        "手牌售卖图": HAND_SELL_IMG
    }
    
    missing_critical = []
    for name, path in critical_files.items():
        if not os.path.exists(path):
            missing_critical.append(f"{name}: {path}")
    
    if missing_critical:
        print("=" * 60)
        print("错误: 以下关键图像文件不存在!")
        print("=" * 60)
        for item in missing_critical:
            print(f"  ✗ {item}")
        print("=" * 60)
        print(f"\n请按照以下步骤操作：")
        print(f"1. 截取商店中的三星棋子图像，保存为: {SHOP_TRIGGER_IMG}")
        print(f"2. 截取手牌中的三星棋子图像，保存为: {HAND_SELL_IMG}")
        print(f"3. 确保两个图像不同（商店版和手牌版）")
        print(f"\n提示: 可以使用 Windows 自带的截图工具 (Win+Shift+S)")
        return
    
    # 检查购买列表
    existing_buy_list = [f for f in BUY_LIST if os.path.exists(f)]
    missing_buy_list = [f for f in BUY_LIST if not os.path.exists(f)]
    
    if not existing_buy_list:
        print("=" * 60)
        print("警告: 购买列表中没有有效的图像文件!")
        print("=" * 60)
        print(f"请将普通棋子图像添加到 BUY_LIST")
        print(f"当前配置:")
        for path in BUY_LIST:
            status = "✓" if os.path.exists(path) else "✗"
            print(f"  {status} {path}")
        print()
    else:
        if missing_buy_list:
            print("=" * 60)
            print("警告: 以下购买列表图像不存在，将被忽略:")
            for path in missing_buy_list:
                print(f"  - {path}")
            print("=" * 60)
            print(f"\n将使用以下 {len(existing_buy_list)} 个有效图像:")
            for path in existing_buy_list:
                print(f"  ✓ {path}")
            print()
    
    # 只使用存在的文件
    BUY_LIST = existing_buy_list if existing_buy_list else BUY_LIST
    
    # 创建自动化对象并运行
    automation = PurchaseAutomation(
        buy_list=BUY_LIST,
        shop_trigger_img=SHOP_TRIGGER_IMG,
        hand_sell_img=HAND_SELL_IMG,
        shop_region=SHOP_REGION,
        hand_region=HAND_REGION,
        sell_pos=SELL_POS,
        hand_first_pos=HAND_FIRST_POS,
        refresh_key=REFRESH_KEY,
        threshold=THRESHOLD,
        click_interval=CLICK_INTERVAL,
        refresh_delay=REFRESH_DELAY,
        purchase_wait=PURCHASE_WAIT,
        sell_wait=SELL_WAIT,
        after_purchase_wait=AFTER_PURCHASE_WAIT,
        after_sell_wait=AFTER_SELL_WAIT
    )
    
    automation.run()


if __name__ == "__main__":
    main()
