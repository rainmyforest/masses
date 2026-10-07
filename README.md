# 五运六气体质分析 · 免登录独立版

从医疗数据平台（v2.5-final）page06/part01 提出的单页应用。
**无需注册登录**，打开即用：输入出生时间 → 排四柱 → 五运六气体质分析报告（AI 解读 + HTML 下载）。

## 启动（四步）

```powershell
cd fortune-app
uv sync                # 首次：按 uv.lock 精确安装依赖（自动准备 Python 3.13）
# 配置 API key（二选一，详见下节）
notepad .streamlit\secrets.toml    # 方式 A：复制 secrets.toml.example 填入 key
$env:DEEPSEEK_API_KEY = "sk-..."   # 方式 B：环境变量（PowerShell）
uv run streamlit run fortune.py
```

浏览器自动打开（默认 http://localhost:8501）。

## 配置 API key（2026-10-07 起）

DeepSeek API key **不再写进源码**，二选一配置（环境变量优先）：

| 方式 | 位置 | 写法 |
|---|---|---|
| A（推荐） | `.streamlit/secrets.toml`（从 `secrets.toml.example` 复制） | `DEEPSEEK_API_KEY = "sk-xxxx"` |
| B | 环境变量 `DEEPSEEK_API_KEY` | 启动前 `set`/`export` 均可 |

未配置时点"开始分析"会收到带指引的错误提示（排盘/大运等本地计算不受影响），
按提示配置后重试即可。`secrets.toml` 含真实 key，**勿提交/同步/分享**。

## 目录结构与配置文件

```
fortune-app/
├── fortune.py                     # 唯一入口（免登录，直调 part01 界面）
├── pyproject.toml                 # 依赖清单（比主平台精简得多）
├── uv.lock                        # 版本锁（uv sync 自动生成/使用）
├── .gitignore                     # 忽略规则（secrets / 缓存 / 虚拟环境）
├── .streamlit/
│   ├── config.toml                # 全站配置：主题 + 运行行为（见下表）
│   ├── secrets.toml.example       # secrets 模板（无敏感信息，可提交）
│   └── secrets.toml               # 真实 key（本地自建，勿提交/分享）
├── my_data/data06/numerology.py   # 神煞综合表（排盘引擎依赖）
├── my_model/open_ai/deepseek.py   # DeepSeek API 调用（key 走 secrets/环境变量）
└── my_page/page06/part01/         # 算法与界面
    ├── analyze.py                 #   界面：表单 + 缓存 + LLM + 展示 + 下载
    ├── engine.py                  #   排盘引擎（lunar-python 四柱八字）
    ├── yunqi.py                   #   五运六气推算
    ├── dayun.py                   #   大运流年推算（数据层）
    ├── solartime.py               #   平/真太阳时校正
    ├── prompt.py                  #   LLM Prompt 组装
    ├── mdhtml.py                  #   报告 HTML 导出
    ├── test_core.py               #   单元/回归测试（排盘/运气/太阳时/prompt）
    └── test_s6_integration.py     #   页面级联调测试（AppTest 走 fortune.py）
```

> 保留 `my_page/page06/part01/` 三层路径的原因：**产品代码与主平台零 diff**，
> 升级时整目录覆盖产品文件即可（测试文件除外，见「与主平台同步」）。

### 配置文件分工

| 文件 | 作用 | 说明 |
|---|---|---|
| `.streamlit/config.toml` | 全站视觉主题（`[theme]`）+ 运行行为（`[browser]`/`[client]`） | 改后需重启应用；调主题色只动这里 |
| `.streamlit/secrets.toml` | 真实 API key + `DEEPSEEK_ALLOW_PRO` 开关 | 本地私有，已列入 `.gitignore` |
| `.streamlit/secrets.toml.example` | 上述 secrets 的模板（含逐键注释） | 新机器复制为 `secrets.toml` 填 key |
| `fortune.py` 内 `st.set_page_config` | 页面级属性：标题/图标/宽布局/侧栏初始态 | 这四项只能代码设置，一般不动 |
| `.gitignore` | 忽略 `secrets.toml`、`__pycache__/`、`.pytest_cache/`、`.ruff_cache/`、`.venv/` | 一般不动 |

## 与主平台同步

```powershell
# 主平台 part01 更新后（覆盖产品文件）：
Copy-Item -Recurse -Force <主平台>/my_page/page06/part01/* my_page/page06/part01/
```

> ⚠️ 2026-10-07 清理后，**测试文件与主平台已有差异**（独立版删除了主平台
> 专用 e2e 用例与旧副本 `test_part01_core.py`，并同步了独立版行为断言）。
> 覆盖同步后请恢复独立版的 `test_core.py` / `test_s6_integration.py`。

## 测试（可选）

```powershell
uv run pytest my_page -q
```

> 共 63 项：`test_core.py` 53 项（排盘/运气/太阳时/prompt/key 管理）+
> `test_s6_integration.py` 10 项（真实入口联调、防爬闸门、缓存命中）。
> 在已配置 API key 的机器上会显示 1 项 skip 属正常——「key 缺失提示」
> 用例仅在未配置 key 的环境运行。

## 注意事项

- **API 计费**：本版免登录 = 任何人都能用，每次"开始分析"调用一次 DeepSeek。
  内网小范围使用没问题；若放到公网，建议加访问频率限制或换低配额 key。
- 排盘/运气计算完全本地（lunar-python），不联网；仅 AI 解读走 DeepSeek API。
