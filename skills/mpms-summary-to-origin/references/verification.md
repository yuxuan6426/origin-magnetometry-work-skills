# Verification / 验证

Package version: **0.1.0**. Validation date: **2026-11-18**.

| Layer / 层级 | Status / 状态 | Evidence and limits / 证据与边界 |
| --- | --- | --- |
| Local Python conversion | Passed / 已通过 | Windows, Python 3.13.9, openpyxl 3.1.5, Matplotlib 3.10.9 |
| Independent synthetic checks | 47 passed / 47 项通过 | Temporary data authored independently for this implementation; no real measurements used |
| PNG visual review | Passed / 已打开检查 | Actual generated PNG opened after conversion; axes, legend, two independent curves readable |
| Static package checks | Passed / 已通过 | 13 local checks: JSON structure, exact allowlist, sizes, syntax, local links, SVG and independent allowlisted extraction; portable-skill-creator structure verify passed |
| ChatGPT Work receiver import | **pending** | No receiving Work session installed or ran this package |
| Origin native execution | **pending** | OGS text generated and inspected; not executed in an Origin instance |
| Real MPMS measurement validation | **pending** | Only synthetic summary tables were used |

Synthetic checks covered actual header/unit discovery; multiple moment candidates; error-column separation; quoted commas and multiline comments; physical line mapping; blank-line accounting; independent curve X arrays; acquisition order and duplicate X; mg/g normalization and SI moment conversion; missing/nonfinite retention; XLSX literal text; CSV row mapping; source/artifact SHA-256; headless PNG decoding; OGS structure; required mass/raw choice; invalid mass; existing output protection; overlapping/incomplete ranges; raw and renamed voltage scans; repeated data blocks; duplicate axis headers; unknown-unit handling; unit override; tab delimiter; Fortran exponent; encoding fallback; extra and short records.

临时合成输入、断言脚本、期望数值和生成结果均不进入分发目录。上述检查证明本机确定性行为，不证明接收端安装、云端依赖可用性、真实实验语义或 Origin 版本兼容。

For receiver testing, follow [receiver-checklist.md](receiver-checklist.md). A successful receiving environment may record its own result separately; the generated manifest deliberately starts both receiver states as pending. Do not change pending to passed based only on a locally generated manifest.

The allowlisted skill folder was copied to a fresh temporary directory and successfully ran `inspect` with Python site-packages disabled, then `convert` using its own scripts and declared dependencies. The static verifier checks structure, not scientific correctness or receiver activation.
