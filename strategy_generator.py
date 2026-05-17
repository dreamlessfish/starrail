"""
策略表生成器
生成Excel策略表，用于离线决策购买行为
"""

import os
import pandas as pd
from typing import Tuple, List

def generate_all_states() -> List[Tuple[int, int, int]]:
    """
    生成所有可能的稳定手牌状态
    状态格式: (1星数量, 2星数量, 3星数量)
    约束: 
    1. 总数 <= 3
    2. 必须是稳定状态（不会立即合成）：
       - 1星数量 < 3（3个1星会立即合成）
       - 2星数量 < 3（3个2星会立即合成）
    
    排序优先级：
    1. 按3星数量升序
    2. 按2星数量升序
    3. 按1星数量升序
    """
    states = []
    # 穷举所有可能的组合，但排除不稳定状态
    for one_star in range(3):  # 0-2（不能有3个，会立即合成）
        for two_star in range(3):  # 0-2（不能有3个，会立即合成）
            for three_star in range(4):  # 0-3
                total = one_star + two_star + three_star
                if total <= 3:
                    # 验证这是稳定状态（应用合成规则后不变）
                    normalized = apply_synthesis(one_star, two_star, three_star)
                    if normalized == (one_star, two_star, three_star):
                        states.append((one_star, two_star, three_star))
    
    # 去重并排序：优先按3星数量升序，次按2星数量升序，最后按1星数量升序
    states = sorted(set(states), key=lambda x: (x[2], x[1], x[0]))
    return states

def state_to_string(state: Tuple[int, int, int]) -> str:
    """将状态转换为字符串描述"""
    one, two, three = state
    parts = []
    if three > 0:
        parts.append(f"{three}×3★")
    if two > 0:
        parts.append(f"{two}×2★")
    if one > 0:
        parts.append(f"{one}×1★")
    return " ".join(parts) if parts else "Empty"

def apply_synthesis(one_star: int, two_star: int, three_star: int) -> Tuple[int, int, int]:
    """
    应用合成规则：
    3个1星 -> 1个2星 + 1个1星(Buff)
    3个2星 -> 1个3星
    
    Returns:
        合成后的状态 (1星, 2星, 3星)
    """
    # 先处理2星合成（优先级更高）
    while two_star >= 3:
        two_star -= 3
        three_star += 1
    
    # 再处理1星合成
    while one_star >= 3:
        one_star -= 3
        two_star += 1
        one_star += 1  # Buff: 合成后保留1个1星
    
    return (one_star, two_star, three_star)

def simulate_purchase(state: Tuple[int, int, int], shop_count: int) -> Tuple[Tuple[int, int, int], str]:
    """
    模拟购买行为
    
    Args:
        state: 当前手牌状态 (1星, 2星, 3星)
        shop_count: 商店刷出的1星牌数量 (0-5)
    
    Returns:
        (新状态, 决策)
        决策: 'Buy', 'Buy & Sell', 'Refresh', 'Sell'
    """
    one_star, two_star, three_star = state
    
    # 如果商店刷出0张牌
    if shop_count == 0:
        # 如果手牌已有3星，标记为售卖
        if three_star > 0:
            # 售卖后移除1个3星
            new_three = max(0, three_star - 1)
            new_state = apply_synthesis(one_star, two_star, new_three)
            return new_state, 'Sell'
        else:
            return state, 'Refresh'
    
    # 购买shop_count张1星牌
    new_one_star = one_star + shop_count
    new_two_star = two_star
    new_three_star = three_star
    
    # 应用合成规则
    final_one, final_two, final_three = apply_synthesis(new_one_star, new_two_star, new_three_star)
    
    # 计算总占用格子数
    total_slots = final_one + final_two + final_three
    
    # 判断决策
    if final_three > 0:
        # 合成后出现了3星
        return (final_one, final_two, final_three), 'Buy & Sell'
    elif total_slots <= 3:
        # 合成后总占用<=3格，可以购买
        return (final_one, final_two, final_three), 'Buy'
    else:
        # 合成后占用>3格（卡格子），不买
        return state, 'Refresh'

def generate_strategy_table(output_path: str = "H:\\starrail\\strategy_table.xlsx"):
    """
    生成策略表Excel文件
    
    Args:
        output_path: 输出Excel文件路径
    """
    print("=" * 60)
    print("策略表生成器")
    print("=" * 60)
    
    # 生成所有状态
    print("生成所有可能的手牌状态...")
    states = generate_all_states()
    print(f"共生成 {len(states)} 个状态")
    
    # 建立状态到ID的映射（状态 -> ID）
    state_to_id = {}
    for idx, state in enumerate(states, 1):
        state_to_id[state] = idx
    
    # 准备数据
    data = {
        'ID': [],
        'State': [],
        'Shop_0': [],
        'Shop_1': [],
        'Shop_2': [],
        'Shop_3': [],
        'Shop_4': [],
        'Shop_5': []
    }
    
    print("\n计算每个状态的决策和跳转ID...")
    for idx, state in enumerate(states, 1):
        state_str = state_to_string(state)
        data['ID'].append(idx)
        data['State'].append(state_str)
        
        # 对每个商店刷出数量（0-5）计算决策和跳转ID
        for shop_count in range(6):
            new_state, decision = simulate_purchase(state, shop_count)
            
            # 查找新状态对应的ID
            if new_state in state_to_id:
                target_id = state_to_id[new_state]
            else:
                # 如果找不到，可能是状态异常，使用当前ID
                print(f"  警告: 状态 {new_state} 不在状态列表中，使用当前ID {idx}")
                target_id = idx
            
            # 根据决策类型确定目标ID
            if decision == 'Refresh':
                # Refresh: 状态不变，使用当前行的ID
                target_id = idx
            elif decision == 'Sell':
                # Sell: 使用售卖后的新状态ID（已经在simulate_purchase中计算）
                pass  # target_id已经设置
            elif decision == 'Buy':
                # Buy: 使用购买合成后的新状态ID
                pass  # target_id已经设置
            elif decision == 'Buy & Sell':
                # Buy & Sell: 使用购买合成后的新状态ID
                pass  # target_id已经设置
            
            # 格式：Action, Target_ID
            cell_value = f"{decision}, {target_id}"
            col_name = f'Shop_{shop_count}'
            data[col_name].append(cell_value)
        
        if idx % 10 == 0:
            print(f"  已处理 {idx}/{len(states)} 个状态...")
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 保存为Excel
    print(f"\n保存策略表到: {output_path}")
    df.to_excel(output_path, index=False, sheet_name='Strategy')
    
    print("=" * 60)
    print("策略表生成完成！")
    print(f"文件路径: {output_path}")
    print(f"总状态数: {len(states)}")
    print("=" * 60)
    
    # 打印一些示例
    print("\n示例状态（前10个）:")
    for i in range(min(10, len(states))):
        state = states[i]
        state_str = state_to_string(state)
        print(f"  ID {i+1}: {state_str}")
    
    return df

if __name__ == "__main__":
    # 确保输出目录存在
    output_dir = os.path.dirname("H:\\starrail\\strategy_table.xlsx")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成策略表
    df = generate_strategy_table()
    
    print("\n策略表预览（前5行）:")
    print(df.head())

