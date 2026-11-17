# Receiving environment check / 接收端验证

Current state: **ChatGPT Work pending; Origin pending**. This is a procedure for future receiver evidence, not an installation claim.

## ChatGPT Work

1. Obtain a reviewed plugin source archive. It must contain root `plugin.json`, `skills/mpms-summary-to-origin/SKILL.md`, all scripts and references listed in the skill's `delivery.json`, and the MIT license. Follow the recipient's currently available plugin import flow. A ZIP upload by itself does not prove installation or activation. Public-directory publishing is a separate host process.
2. Open a fresh Work chat and confirm the skill is discoverable. If no plugin import surface is available, upload/extract the reviewed source and invoke the script manually; report this as **manual source use**, not installation. The skill directory also carries its own requirements for standalone use.
3. In the execution environment check Python 3.10+, openpyxl and Matplotlib versions. If missing and permitted, install the provided requirements. These are execution-environment dependencies; the user's local Python/Origin installation cannot satisfy a cloud import.
4. Upload a summary DAT the recipient is authorized to use. Run `inspect` and verify actual header, unit, candidate counts, record count and ambiguity against the file. Confirm that `.rw.dat` is refused. Keep the upload outside the plugin source tree.
5. Supply the user's actual sample mass in mg or explicit raw choice, intended moment column, X and any confirmed segment ranges. Run conversion to a new directory. Verify the manifest selection, coverage, source SHA-256, a hand-calculated normalization value, and each curve's own X sequence. Open the PNG in the receiver environment and download the full bundle.
6. Record host/surface/date, plugin version, invocation type (installed/manual), dependency versions, observed success/failure and relevant artifact hashes. Do not include private measurements in a public report. Mark receiver status passed only after these observations.

## Origin

1. Extract the complete downloaded bundle to a Windows path. Record Origin version/build and locale.
2. Run the OGS `Main` section with the extracted directory including trailing backslash. See the OGS comment for the invocation.
3. Verify one imported workbook and graph per curve; imported X/Y numeric values and row counts; independent X grids; source-unit/scaling metadata; missing-point line behavior; and plotted direction against CSV and the Matplotlib preview.
4. Save the native project if required and record its observed result separately. Mark Origin execution passed only after the real application check; generating OGS or a PNG is insufficient.

## 中文要点

先验证包结构和 delivery 白名单，再在新的 Work 对话确认技能是否可发现；无法导入时可手动运行源码，须明确记录为“源码手动使用”。云端依赖需在云端执行环境检查，不能由本机安装替代。用有权处理的用户汇总 DAT 检查实际表头、源记录、磁矩选择、质量和段界，独立核算一点，打开 PNG 并下载完整产物。

Origin 收件人记录版本/语言区域，解压整包，运行 OGS 后核对逐曲线工作簿、X/Y 数值、记录数、缺失点连线和图形。只有真实观察才将相应 pending 项改为 passed；不能仅凭本机报告、ZIP 或 manifest 宣称已安装和验证。
