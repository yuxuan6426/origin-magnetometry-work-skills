# Work 工作流与命令

需要 Python 3.10+。`inspect` 仅用标准库；`convert` 另需 openpyxl 3.1+（<4）与 Matplotlib 3.8+（<4）。已测版本见[验证记录](../verification.md)。执行环境允许安装依赖时，在插件根目录运行 `python -m pip install -r requirements.txt`。Work 中应先定位上传文件、执行环境和技能目录，不假定本机 Windows 路径或固定云端挂载点。

## 先检查

```sh
python skills/mpms-summary-to-origin/scripts/mpms.py inspect /path/to/upload.dat --output /path/to/inspection.json
```

检查结果包含实际表头、末尾括号中的单位、从 1 开始的列序号、有限数值数量/范围、角色候选、歧义、字段数异常及方向诊断。方向变化记录是完成相邻非零 X 差分符号改变的记录；重复 X 不改变方向，缺失 X 会重置诊断。它只是描述性线索，不能直接识别实验或充当分段结论。

默认先尝试带 BOM 的 UTF-8，再尝试 cp1252；后者会记录警告。可用 `--encoding NAME` 指定编码，用 `--delimiter comma|tab` 指定分隔符。缺少或重复 `[Data]` 块会报错。检查 JSON 路径必须尚不存在。

## 列、单位与质量

`--moment-column` 必须使用检查结果中的完整实际表头或从 1 开始的列序号。若 VSM、DC 自由中心、固定中心等多列均可用，向用户展示候选并由用户选定。程序不设置模式优先级。误差列单独报告，不能作为磁矩列。

用户要求决定横轴：`--x temperature`、`--x field` 只接受唯一可用候选；有歧义时用 `--x-column` 完整表头或序号。X 保留源单位，不自动将 Oe 改成 T；单位缺失会在元数据中明确记录。

必须明确提供用户给出的样品质量 `--mass-mg`，或明确选择 `--raw` 原始未归一化磁矩。二者必选其一，没有默认质量。质量必须是有限正数。归一化公式：`M(emu/g) = moment_emu / (mass_mg / 1000)`。质量归一化支持源单位 emu 与 A m²，换算为 `1 A m² = 1000 emu`。确认真实源单位后，可用 `--moment-unit emu` 或 `--moment-unit 'A*m^2'` 显式覆盖；覆盖值会进入 manifest。单位不明时停止归一化；raw 保留源数值并报告源单位或“未指定”。

## 段界覆盖

默认一段覆盖全部非空数据记录。需要覆盖时，将检查 JSON 中的 `segment_template` 复制到临时 JSON。顶层仅含 `segments` 数组，每段有整数 `start`、整数 `end` 和可选字符串 `label`。根据用户确认的测量流程拆分，必须按源顺序、连续、无重叠地完整覆盖记录 1 到 N；两端均包含。缺失或非有限测量记录也计入范围。空段、跳过记录、重复记录和重排都会报错。

标签来自用户；不凭温度走向、名义磁场、文件名或曲线形状推断 ZFC、FC、升降温、磁滞支路等实验身份。程序不使用任意容差聚类或普遍适用的拟合质量阈值。

## 转换

将占位符替换为检查结果和用户质量：

```sh
python skills/mpms-summary-to-origin/scripts/mpms.py convert /path/to/upload.dat --output /path/to/new-output --moment-column 'ACTUAL HEADER' --x temperature --mass-mg USER_MASS_MG --segments /path/to/confirmed-segments.json
```

raw 模式将 `--mass-mg USER_MASS_MG` 替换为 `--raw`。确认单段时省略 `--segments`；显式横轴则用 `--x-column 'ACTUAL X HEADER'` 替换 `--x temperature`。输出目录必须全新。成功退出码为 0，预期的输入/配置错误为 2；已有输出不会覆盖。

| 产物 | 内容 |
| --- | --- |
| `magnetometry.xlsx` | 元数据、按文本原样保存的源字段、曲线索引、逐曲线工作表和独立 XY 对的宽表 |
| `curve_*.csv` | X、Y、原始磁矩、源记录和物理源行；保留采集顺序 |
| `source_rows.csv` | 全部非空源记录对应曲线行、CSV 行、有效状态及原始字段 JSON |
| `manifest.json` | 源 SHA-256、实际列、选择、段界、换算、运行版本与产物哈希 |
| `preview.png` | Matplotlib 无界面预览；无效数值对产生断点 |
| `import_origin.ogs` | Origin CSV 导入和逐曲线折线图脚本 |
| `READ_ME.txt` | 随包交接说明 |

打开 PNG，核对 manifest 的列、质量、单位和记录数，并独立手算一个归一化点。通过 Work 的附件机制交付 XLSX 和包含**完整目录**的 ZIP；ZIP 可用 Python 标准库创建。生成数据放在源码目录外。

## 交接 Origin

下载并解压完整目录，在 Origin 的 Script Window 中替换真实路径后运行：

```text
run.section("C:\data\import_origin.ogs", Main, "C:\data\");
```

唯一参数是解压目录，**包含末尾反斜杠**。脚本使用 Origin 的 CSV Data Connector，为每条曲线创建工作簿和折线图，取前两列作为 X/Y，后续列用于追溯。收件人在自己的 Origin 版本中核对表头、数字导入、缺失点连线行为、坐标轴及 manifest/预览；需要时自行保存 Origin 项目。本技能无桌面连接或 `.opju` 生成。

ChatGPT Work 接收端导入/启用与 Origin 本机运行均为 **pending**；运行源码不代表插件已安装。
