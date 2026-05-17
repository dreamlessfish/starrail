"""
基于策略表的购买自动化主程序
使用Excel策略表进行离线决策
"""

from image_recognition_automation import ImageRecognitionAutomation
import pandas as pd
import pyautogui
import time
import os
import keyboard
import sys
from typing import List, Tuple, Optional

class StrategyBasedAutomation:
    """基于策略表的购买自动化类"""
    
    def __init__(self,
                 strategy_table_path: str,
                 buy_list: List[str],
                 hand_sell_img: str,
                 hand_1star_img: str,
                 hand_2star_img: str,
                 shop_region: Tuple[int, int, int, int],
                 hand_region: Tuple[int, int, int, int],
                 sell_pos: Tuple[int, int],
                 refresh_key: str,
                 threshold: float,
                 click_interval: float,
                 refresh_delay: float,
                 after_purchase_wait: float,
                 after_sell_wait: float,
                 synthesis_wait: float):
        """
        初始化基于策略表的自动化
        
        Args:
            strategy_table_path: 策略表Excel文件路径
            buy_list: 目标卡牌图像路径列表（用于识别商店中的1星牌）
            hand_sell_img: 手牌里的三星棋子图片（用于售卖检测）
            hand_1star_img: 手牌中的1星棋子图片（用于状态校准）
            hand_2star_img: 手牌中的2星棋子图片（用于状态校准）
            shop_region: 商店区域 (x, y, width, height)
            hand_region: 手牌区域 (x, y, width, height)
            sell_pos: 售卖终点坐标 (x, y)
            refresh_key: 刷新按键，默认为 'd'
            threshold: 图像匹配阈值，默认0.8
            click_interval: 点击间隔时间（秒），默认0.1秒
            refresh_delay: 刷新后等待时间（秒），默认0.5秒
            after_purchase_wait: 购买完成后等待时间（秒），默认10.0秒
            after_sell_wait: 售卖完成后等待时间（秒），默认6.0秒
            synthesis_wait: 合成三星动画等待时间（秒），默认5.0秒
        """
        self.automation = ImageRecognitionAutomation()
        self.buy_list = buy_list
        self.hand_sell_img = hand_sell_img
        self.hand_1star_img = hand_1star_img
        self.hand_2star_img = hand_2star_img
        self.hand_3star_img = hand_sell_img  # 3星就是原有的hand_sell_img
        self.shop_region = shop_region
        self.hand_region = hand_region
        self.sell_pos = sell_pos
        self.refresh_key = refresh_key
        self.threshold = threshold
        self.click_interval = click_interval
        self.refresh_delay = refresh_delay
        self.after_purchase_wait = after_purchase_wait
        self.after_sell_wait = after_sell_wait
        self.synthesis_wait = synthesis_wait
        
        # 加载策略表
        print(f"加载策略表: {strategy_table_path}")
        if not os.path.exists(strategy_table_path):
            raise FileNotFoundError(f"策略表文件不存在: {strategy_table_path}")
        
        self.strategy_df = pd.read_excel(strategy_table_path, sheet_name='Strategy')
        print(f"策略表加载成功，共 {len(self.strategy_df)} 个状态")
        
        # 当前状态ID（从策略表中查找）
        self.current_state_id = 1  # 默认从ID 1（空手牌）开始
        
        # 运行状态控制
        self.is_running = False
        self.should_exit = False
        
        # 统计信息
        self.total_rounds = 0
        self.total_purchases = 0
        self.total_sells = 0
        self.total_refreshes = 0
    
    def get_state_string(self, state_id: int) -> str:
        """根据状态ID获取状态字符串描述"""
        if state_id < 1 or state_id > len(self.strategy_df):
            return "Unknown"
        state_idx = state_id - 1  # ID从1开始，索引从0开始
        return self.strategy_df.iloc[state_idx]['State']
    
    def parse_state_string(self, state_str: str) -> Tuple[int, int, int]:
        """
        解析状态字符串，提取1星、2星、3星数量
        
        Args:
            state_str: 状态字符串，如 "Empty", "2×2★", "1×2★ 1×1★", "1×3★" 等
        
        Returns:
            (1星数量, 2星数量, 3星数量)
        """
        if state_str == "Empty" or not state_str:
            return (0, 0, 0)
        
        one_star = 0
        two_star = 0
        three_star = 0
        
        # 解析格式：如 "2×2★", "1×2★ 1×1★", "1×3★" 等
        parts = state_str.split()
        for part in parts:
            if '×' in part and '★' in part:
                try:
                    # 提取数量和星级
                    count_str, star_str = part.split('×')
                    count = int(count_str)
                    
                    if '3★' in star_str:
                        three_star = count
                    elif '2★' in star_str:
                        two_star = count
                    elif '1★' in star_str:
                        one_star = count
                except (ValueError, IndexError):
                    continue
        
        return (one_star, two_star, three_star)
    
    def sync_hand_state(self):
        """
        零卡牌时的状态校准功能
        扫描手牌区域，统计当前手牌中1星、2星、3星的实际数量，并更新状态ID
        """
        print("\n[状态校准] 开始扫描手牌区域...")
        
        # 统计手牌中各种星级的数量
        c1 = 0  # 1星数量
        c2 = 0  # 2星数量
        c3 = 0  # 3星数量
        
        # 识别1星
        if os.path.exists(self.hand_1star_img):
            matches_1 = self.automation.find_image_multiple(
                self.hand_1star_img,
                threshold=self.threshold,
                region=self.hand_region
            )
            c1 = len(matches_1)
            print(f"  识别到 {c1} 个1星")
        
        # 识别2星
        if os.path.exists(self.hand_2star_img):
            matches_2 = self.automation.find_image_multiple(
                self.hand_2star_img,
                threshold=self.threshold,
                region=self.hand_region
            )
            c2 = len(matches_2)
            print(f"  识别到 {c2} 个2星")
        
        # 识别3星
        if os.path.exists(self.hand_3star_img):
            matches_3 = self.automation.find_image_multiple(
                self.hand_3star_img,
                threshold=self.threshold,
                region=self.hand_region
            )
            c3 = len(matches_3)
            print(f"  识别到 {c3} 个3星")
        
        # 三星优先处理：如果检测到3星，先售卖
        if c3 > 0:
            print(f"\n  检测到 {c3} 个3星，先执行售卖...")
            self.perform_sell()
            time.sleep(self.after_sell_wait)
            # 售卖后重新扫描（简单处理：将c3归零）
            c3 = 0
            print("  售卖完成，重新校准状态（3星已归零）")
        
        # 根据统计到的 (c1, c2, 0) 查找对应的状态
        print(f"\n  实际手牌统计: 1★: {c1}, 2★: {c2}, 3★: {c3}")
        
        # 遍历策略表查找匹配的状态
        found_id = None
        for idx, row in self.strategy_df.iterrows():
            state_str = row['State']
            parsed = self.parse_state_string(state_str)
            
            # 匹配1星和2星数量（忽略3星，因为已经售卖）
            if parsed[0] == c1 and parsed[1] == c2 and parsed[2] == 0:
                found_id = row['ID']
                break
        
        if found_id is not None:
            self.current_state_id = found_id
            print(f"  状态校准完成：实际手牌 (1★: {c1}, 2★: {c2}) -> 更新为 ID {found_id} ({self.get_state_string(found_id)})")
        else:
            print(f"  ⚠ 警告: 未找到匹配的状态，保持当前状态ID {self.current_state_id}")
    
    def lookup_decision(self, shop_count: int) -> Optional[Tuple[str, int]]:
        """
        查表获取决策和跳转ID
        
        Args:
            shop_count: 商店刷出的1星牌数量 (0-5)
        
        Returns:
            (决策字符串, 跳转ID) 或 None
            决策字符串: 'Buy', 'Buy & Sell', 'Refresh', 'Sell'
            跳转ID: 执行动作后会跳转到的状态ID
        """
        if self.current_state_id < 1 or self.current_state_id > len(self.strategy_df):
            print(f"警告: 当前状态ID {self.current_state_id} 超出范围")
            return None
        
        state_idx = self.current_state_id - 1  # ID从1开始，索引从0开始
        col_name = f'Shop_{shop_count}'
        
        if col_name not in self.strategy_df.columns:
            print(f"警告: 策略表中没有列 {col_name}")
            return None
        
        cell_value = self.strategy_df.iloc[state_idx][col_name]
        
        # 解析格式: "Action, Target_ID"
        if isinstance(cell_value, str) and ', ' in cell_value:
            parts = cell_value.split(', ', 1)
            if len(parts) == 2:
                decision = parts[0]
                try:
                    target_id = int(parts[1])
                    return (decision, target_id)
                except ValueError:
                    print(f"警告: 无法解析跳转ID: {parts[1]}")
                    return (decision, self.current_state_id)  # 默认使用当前ID
            else:
                # 旧格式兼容：只有Action
                return (cell_value, self.current_state_id)
        else:
            # 旧格式兼容：只有Action
            return (str(cell_value), self.current_state_id)
    
    def count_shop_cards(self) -> int:
        """
        识别商店中有几张目标卡牌（1星牌）
        
        Returns:
            商店中目标卡牌的数量 (0-5)
        """
        total_count = 0
        for template_path in self.buy_list:
            if not os.path.exists(template_path):
                continue
            
            matches = self.automation.find_image_multiple(
                template_path,
                threshold=self.threshold,
                region=self.shop_region
            )
            total_count += len(matches)
        
        # 限制在0-5之间
        return min(total_count, 5)
    
    def purchase_all_cards(self) -> int:
        """
        购买商店中所有目标卡牌
        
        Returns:
            成功购买的数量
        """
        purchased = 0
        for template_path in self.buy_list:
            if not os.path.exists(template_path):
                continue
            
            matches = self.automation.find_image_multiple(
                template_path,
                threshold=self.threshold,
                region=self.shop_region
            )
            
            for x, y, confidence in matches:
                print(f"  点击购买: ({x}, {y}), 置信度: {confidence:.2f}")
                self.automation.click(x, y)
                purchased += 1
                time.sleep(self.click_interval)
        
        return purchased
    
    def perform_sell(self) -> bool:
        """
        执行售卖流程：查找手牌中的三星棋子并拖拽售卖
        
        Returns:
            是否成功售卖
        """
        print("\n[售卖流程] 在手牌区查找三星棋子...")
        
        result = self.automation.find_image(
            self.hand_sell_img,
            threshold=self.threshold,
            region=self.hand_region
        )
        
        if result:
            x, y, confidence = result
            print(f"  找到三星棋子! 位置: ({x}, {y}), 置信度: {confidence:.2f}")
            print(f"  拖拽到售卖位置: {self.sell_pos}")
            self.automation.drag(x, y, self.sell_pos[0], self.sell_pos[1], duration=0.5)
            time.sleep(0.5)
            
            # 确认售卖：循环检测直到图像消失
            print("  确认售卖中...")
            confirm_attempts = 0
            max_confirm = 2
            
            while confirm_attempts < max_confirm and self.is_running:
                confirm_attempts += 1
                check_result = self.automation.find_image(
                    self.hand_sell_img,
                    threshold=self.threshold,
                    region=self.hand_region
                )
                
                if not check_result:
                    print(f"  ✓ 售卖确认成功! (检测 {confirm_attempts} 次)")
                    self.total_sells += 1
                    return True
                else:
                    print(f"    等待中... ({confirm_attempts}/{max_confirm})")
                    time.sleep(0.3)
            
            print("  ⚠ 售卖确认超时，但继续执行")
            self.total_sells += 1
            return True
        else:
            print("  ⚠ 未找到手牌中的三星棋子")
            return False
    
    def refresh_shop(self):
        """刷新商店"""
        print(f"\n按 {self.refresh_key.upper()} 键刷新商店...")
        pyautogui.press(self.refresh_key)
        time.sleep(self.refresh_delay)
        self.total_refreshes += 1
    
    
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
        print(f"  总售卖: {self.total_sells}")
        print(f"  总刷新: {self.total_refreshes}")
        print(f"  当前状态ID: {self.current_state_id} ({self.get_state_string(self.current_state_id)})")
    
    def get_initial_state_id(self) -> int:
        """
        获取用户输入的初始状态ID
        
        Returns:
            初始状态ID
        """
        print("\n" + "=" * 60)
        print("初始状态ID录入")
        print("=" * 60)
        print("请输入当前手牌对应的状态ID（从策略表中查找）")
        print("例如: 1 表示空手牌")
        print("提示: 可以在策略表中查找对应的状态描述")
        print("-" * 60)
        
        while True:
            try:
                user_input = input("请输入状态ID: ").strip()
                state_id = int(user_input)
                
                if state_id < 1 or state_id > len(self.strategy_df):
                    print(f"错误: 状态ID必须在 1-{len(self.strategy_df)} 之间")
                    continue
                
                state_str = self.get_state_string(state_id)
                print(f"✓ 初始状态: ID {state_id} - {state_str}")
                return state_id
                
            except ValueError:
                print("错误: 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n用户取消")
                sys.exit(0)
    
    def run(self):
        """运行基于策略表的自动化循环"""
        print("=" * 60)
        print("基于策略表的购买自动化")
        print("=" * 60)
        print(f"策略表路径: H:\\starrail\\strategy_table.xlsx")
        print(f"目标卡牌数量: {len(self.buy_list)}")
        print(f"商店区域: {self.shop_region}")
        print(f"手牌区域: {self.hand_region}")
        print(f"售卖位置: {self.sell_pos}")
        print("-" * 60)
        print("\n控制说明:")
        print("  F10 - 启动脚本")
        print("  F11 - 暂停脚本")
        print("  F12 - 退出程序")
        print("=" * 60)
        
        # 获取初始状态ID
        self.current_state_id = self.get_initial_state_id()
        print(f"\n当前状态: ID {self.current_state_id} - {self.get_state_string(self.current_state_id)}")
        print("\n等待按 F10 启动...")
        
        # 设置热键
        self._setup_hotkeys()
        
        try:
            while not self.should_exit:
                if self.is_running:
                    # 执行一轮循环
                    self.total_rounds += 1
                    print(f"\n{'='*60}")
                    print(f"第 {self.total_rounds} 轮循环")
                    print(f"当前状态: ID {self.current_state_id} - {self.get_state_string(self.current_state_id)}")
                    print(f"{'='*60}")
                    
                    # 1. 先刷新商店
                    print("\n[刷新阶段] 刷新商店...")
                    if self.is_running:
                        self.refresh_shop()
                    
                    # 2. 识别并购买商店中的卡牌
                    print("\n[购买阶段] 扫描并购买商店中的目标卡牌...")
                    # 执行购买
                    purchased = self.purchase_all_cards()
                    
                    if purchased == 0:
                        # 识别到0张购买卡牌，执行手牌状态校准
                        print("  识别到 0 张购买卡牌，执行手牌状态校准...")
                        self.sync_hand_state()
                        # 校准完成后直接进入下一轮循环
                        continue
                    
                    if purchased > 0:
                        self.total_purchases += purchased
                        print(f"  ✓ 成功购买 {purchased} 张卡牌")
                    
                    # 3. 先更新状态（按照成功购买数量，不等待）
                    print(f"\n[状态更新] 根据成功购买数量 {purchased} 张更新状态...")
                    result = self.lookup_decision(purchased)
                    
                    if result is None:
                        print("  ⚠ 无法获取决策，跳过状态更新")
                        time.sleep(1)
                        continue
                    
                    decision, target_id = result
                    print(f"  决策结果: {decision}, 跳转ID: {target_id}")
                    
                    # 更新状态ID（按照成功购买数量对应的跳转ID）
                    self.current_state_id = target_id
                    print(f"  状态更新: ID {self.current_state_id} - {self.get_state_string(self.current_state_id)}")
                    
                    # 4. 判断新状态是否需要进入售卖阶段（状态ID >= 9）
                    if self.current_state_id >= 9:
                        # 新状态是三星，需要等待合成动画（合成动画时间较长）
                        print(f"\n[售卖阶段] 检测到三星状态（ID >= 9），等待合成动画完成（{self.synthesis_wait}秒）...")
                        time.sleep(self.synthesis_wait)
                        print("  进入售卖模式")
                        # 进入售卖流程（不刷新）
                        if self.is_running:
                            self.perform_sell()
                            # 等待售卖完成
                            print(f"  等待 {self.after_sell_wait} 秒后继续...")
                            time.sleep(self.after_sell_wait)
                        # 售卖后根据 Shop_0 更新状态
                        sell_result = self.lookup_decision(0)  # Shop_0
                        if sell_result:
                            sell_decision, sell_target_id = sell_result
                            self.current_state_id = sell_target_id
                            print(f"  售卖后状态更新: ID {self.current_state_id} - {self.get_state_string(self.current_state_id)}")
                    else:
                        # 新状态不是三星，无需等待，直接进入下一轮
                        print(f"\n  状态ID < 9，无需售卖，直接进入下一轮循环")
                    
                    # 5. 进入下一个循环（无论是否售卖，都继续下一轮）
                
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
    
    # ============================================================================
    # ============================ 所有可调参数配置区域 ============================
    # ============================================================================
    
    # ========== 一、文件路径配置 ==========
    # 1. 策略表路径
    STRATEGY_TABLE_PATH = "H:\\starrail\\strategy_table.xlsx"
    
    # 2. 目标卡牌图像列表（用于识别商店中的1星牌，三张都是可能出现的一星图片）
    BUY_LIST = [
        "H:\\starrail\\images\\shajin1.png",
        "H:\\starrail\\images\\shajin2.png",
        "H:\\starrail\\images\\shajin3.png"
    ]
    
    # 3. 手牌图像路径
    HAND_SELL_IMG = "H:\\starrail\\images\\starshajin.png"  # 手牌里的三星棋子图片（用于售卖检测）
    HAND_1STAR_IMG = "H:\\starrail\\images\\hand_1star.png"  # 手牌中的1星棋子图片（用于状态校准）
    HAND_2STAR_IMG = "H:\\starrail\\images\\hand_2star.png"  # 手牌中的2星棋子图片（用于状态校准）
    # 注意：3星图片使用 HAND_SELL_IMG
    
    # ========== 二、屏幕区域配置 ==========
    # 4. 商店区域 (x, y, width, height) - 商店所在的屏幕区域，用于限制搜索范围
    SHOP_REGION = (473, 45, 1801, 409)
    
    # 5. 手牌区域 (x, y, width, height) - 手牌所在的屏幕区域，用于限制搜索范围
    HAND_REGION = (499, 1115, 501, 210)
    
    # 6. 售卖位置坐标 (x, y) - 拖拽售卖的目标坐标（通常是垃圾桶或售卖区域）
    SELL_POS = (132, 1213)
    
    # ========== 三、操作配置 ==========
    # 7. 刷新按键 - 刷新商店的按键
    REFRESH_KEY = 'd'
    
    # ========== 四、图像识别配置 ==========
    # 8. 匹配阈值（0-1之间，越高越严格） - 图像匹配的置信度阈值
    #    如果找不到图像，可以降低到 0.7 或 0.6
    THRESHOLD = 0.8
    
    # ========== 五、时间等待配置（单位：秒） ==========
    # 9. 点击间隔 - 连续点击之间的等待时间
    CLICK_INTERVAL = 0.2
    
    # 10. 刷新后等待时间 - 刷新商店后等待的时间
    REFRESH_DELAY = 0.5
    
    # 11. 购买后等待时间 - 购买完成后等待动画的时间
    AFTER_PURCHASE_WAIT = 0.3
    
    # 12. 售卖后等待时间 - 售卖完成后等待的时间
    AFTER_SELL_WAIT = 0.5


    SYNTHESIS_WAIT= 3.5
    
    # 13. 合成三星动画等待时间 - 当购买后状态ID >= 9（出现三星）时，需要等待的合成动画时间3

    # ============================================================================
    # ============================ 配置区域结束 ============================
    # ============================================================================
    
    # 检查策略表是否存在
    if not os.path.exists(STRATEGY_TABLE_PATH):
        print("=" * 60)
        print("错误: 策略表文件不存在!")
        print("=" * 60)
        print(f"请先运行 strategy_generator.py 生成策略表:")
        print(f"  python strategy_generator.py")
        print("=" * 60)
        return
    
    # 检查关键图像文件
    critical_files = {
        "手牌售卖图": HAND_SELL_IMG
    }
    
    missing_critical = []
    for name, path in critical_files.items():
        if not os.path.exists(path):
            missing_critical.append(f"{name}: {path}")
    
    if missing_critical:
        print("=" * 60)
        print("警告: 以下关键图像文件不存在:")
        for item in missing_critical:
            print(f"  ✗ {item}")
        print("=" * 60)
    
    # 检查购买列表
    existing_buy_list = [f for f in BUY_LIST if os.path.exists(f)]
    if not existing_buy_list:
        print("=" * 60)
        print("警告: 购买列表中没有有效的图像文件!")
        print("=" * 60)
        print("将无法识别商店中的卡牌")
        print()
    else:
        if len(existing_buy_list) < len(BUY_LIST):
            print("=" * 60)
            print("警告: 部分购买列表图像不存在，将使用以下有效图像:")
            for path in existing_buy_list:
                print(f"  ✓ {path}")
            print("=" * 60)
            print()
    
    # 创建自动化对象并运行
    automation = StrategyBasedAutomation(
        strategy_table_path=STRATEGY_TABLE_PATH,
        buy_list=existing_buy_list if existing_buy_list else BUY_LIST,
        hand_sell_img=HAND_SELL_IMG,
        hand_1star_img=HAND_1STAR_IMG,
        hand_2star_img=HAND_2STAR_IMG,
        shop_region=SHOP_REGION,
        hand_region=HAND_REGION,
        sell_pos=SELL_POS,
        refresh_key=REFRESH_KEY,
        threshold=THRESHOLD,
        click_interval=CLICK_INTERVAL,
        refresh_delay=REFRESH_DELAY,
        after_purchase_wait=AFTER_PURCHASE_WAIT,
        after_sell_wait=AFTER_SELL_WAIT,
        synthesis_wait=SYNTHESIS_WAIT
    )
    
    automation.run()


if __name__ == "__main__":
    main()

