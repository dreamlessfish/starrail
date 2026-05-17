# StarRail Automation

这是一个基于图像识别和策略表的自动化项目，主要包含两套工作流：

1. `main.py`
   基于 Excel 策略表驱动购买、刷新、卖出循环。
2. `purchase_automation.py`
   基于图像触发器执行购买和卖出流程。

项目当前面向 Windows 环境，依赖屏幕截图、鼠标键盘控制和本地图像模板匹配。

## Repository

GitHub 仓库：

- [dreamlessfish/starrail](https://github.com/dreamlessfish/starrail)

## Files

- `main.py`：策略表版本主入口
- `strategy_generator.py`：生成 `strategy_table.xlsx`
- `purchase_automation.py`：图像触发版本主入口
- `image_recognition_automation.py`：图像识别、点击、拖拽基础能力
- `get_coordinates.py`：坐标采集工具
- `images/`：模板图像
- `strategy_table.xlsx`：策略表

## Requirements

- Windows
- Python 3.10+
- 可见且固定布局的目标窗口
- 已准备好的图像模板

Python 依赖：

- `opencv-python`
- `numpy`
- `pandas`
- `openpyxl`
- `pyautogui`
- `keyboard`

## Install

推荐直接创建虚拟环境后安装：

```powershell
cd H:\starrail
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

也可以直接运行：

```powershell
H:\starrail\install_dependencies.bat
```

## Usage

### 1. 生成策略表

```powershell
cd H:\starrail
python strategy_generator.py
```

这会生成或覆盖：

- `H:\starrail\strategy_table.xlsx`

### 2. 运行策略表自动化

```powershell
cd H:\starrail
python main.py
```

`main.py` 里当前硬编码了以下配置项，运行前应按你的机器重新校准：

- `STRATEGY_TABLE_PATH`
- `BUY_LIST`
- `HAND_SELL_IMG`
- `HAND_1STAR_IMG`
- `HAND_2STAR_IMG`
- `SHOP_REGION`
- `HAND_REGION`
- `SELL_POS`
- `REFRESH_KEY`
- `THRESHOLD`
- 各类等待时间

### 3. 运行图像触发版本

```powershell
cd H:\starrail
python purchase_automation.py
```

适用于你更想依赖图像触发逻辑，而不是策略表状态机的场景。

### 4. 获取坐标

```powershell
cd H:\starrail
python get_coordinates.py
```

热键：

- `F1`：读取当前鼠标坐标
- `F2`：记录区域左上角和右下角
- `ESC`：退出

## Hotkeys

脚本中已有的全局热键以代码为准，当前文档只保留高频控制：

- `F10`：启动
- `F11`：暂停
- `F12`：退出

## Notes

- 这些脚本会真实控制鼠标和键盘，运行前不要把焦点停在无关窗口。
- `pyautogui.FAILSAFE = True`，鼠标快速移到屏幕左上角可触发安全停止。
- 目前多个路径和坐标写死在代码里，换机器或换分辨率必须重新校准。
- `install_dependencies.bat` 依赖 `requirements.txt`，仓库中现已补齐。

## Codex Skills / MCP

我已经补了对这个仓库有实际价值的 Codex 环境能力：

- 已启用 GitHub 插件
- 已启用浏览器插件 `browser-use`
- 已安装技能：`screenshot`

说明：

- 这些能力主要用于后续调试、截图核验、GitHub 发布和浏览器侧验证。
- 新安装的技能通常需要重启 Codex 才会在新会话中完整可用。

## Known Gaps

- 源文件里有明显的编码问题，中文注释和字符串存在乱码。
- 仓库里还没有自动化测试。
- 目前配置主要靠直接改 Python 文件，不适合多人协作或多环境切换。
