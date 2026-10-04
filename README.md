# 五运六气体质分析 · 免登录独立版

从医疗数据平台（v2.5-final）page06/part01 提出的单页应用。
**无需注册登录**，打开即用：输入出生时间 → 排四柱 → 五运六气体质分析报告（AI 解读 + HTML 下载）。

## 启动（三步）

```powershell
cd fortune-app
uv sync                # 首次：按 uv.lock 精确安装依赖（自动准备 Python 3.13）
uv run streamlit run fortune.py
```

浏览器自动打开（默认 http://localhost:8501）。

## 目录结构

```
fortune-app/
├── fortune.py                     # 唯一入口（免登录，直调 part01 界面）
├── pyproject.toml                 # 依赖清单（比主平台精简得多）
├── uv.lock                        # 版本锁（uv sync 自动生成/使用）
└── my_page/page06/part01/         # 算法与界面（与主平台完全一致，零改动）
    ├── analyze.py                 #   界面：表单 + 缓存 + LLM + 展示 + 下载
    ├── engine.py                  #   排盘引擎（lunar-python 四柱八字）
    ├── yunqi.py                   #   五运六气推算
    ├── solartime.py               #   平/真太阳时校正
    ├── prompt.py                  #   LLM Prompt 组装
    ├── mdhtml.py                  #   报告 HTML 导出
    └── test_core.py               #   排盘/运气回归测试（可跑可不跑）
my_data/data06/numerology.py       # 神煞综合表（排盘引擎依赖）
my_model/open_ai/deepseek.py       # DeepSeek API 调用（API key 在此文件内）
```

> 保留 `my_page/page06/part01/` 三层路径的原因：**与主平台零 diff**。
> 主平台升级 part01 后，把整个目录覆盖过来即完成同步，无需改任何 import。

## 与主平台同步

```powershell
# 主平台 part01 更新后：
Copy-Item -Recurse -Force <主平台>/my_page/page06/part01/* my_page/page06/part01/
```

## 测试（可选）

```powershell
uv run pytest my_page/page06/part01/test_core.py -q -k "not e2e"
```

> `-k "not e2e"` 排除 4 个 e2e 用例——它们测的是主平台的整页挂载（`pages/06_…` 脚本），
> 独立版没有该文件，不适用。核心 32 项（排盘/运气/太阳时/prompt）与主平台同源同绿。
> `test_part01_core.py` 为旧版测试副本，保留仅为与主平台零 diff，可无视。

## 注意事项

- **API 计费**：本版免登录 = 任何人都能用，每次"开始分析"调用一次 DeepSeek。
  内网小范围使用没问题；若放到公网，建议加访问频率限制或换低配额 key。
- 排盘/运气计算完全本地（lunar-python），不联网；仅 AI 解读走 DeepSeek API。
