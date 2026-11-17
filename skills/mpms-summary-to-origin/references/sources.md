# Public sources / 公开来源

Independently authored from the sources below, accessed **2026-11-18**. The repository includes no instrument measurements, sample fixtures, vendor documents or copied column tables. Version 0.1.1 is this package's version, not a Quantum Design or Origin version.

本仓库仅据下列公开资料独立编写，未分发仪器测量数据、样本测试答案或厂商原文。访问日期为 **2026-11-18**。

| Source | Version/date visible | Use / 用途 |
| --- | --- | --- |
| [Quantum Design 1500-008](https://qdusa.com/siteDocs/appNotes/1500-008.pdf) | Rev. A0, 2010-05-04 | SVSM summary-column meanings; inspect actual headers / 汇总列语义 |
| [Quantum Design 1500-022](https://qdusa.com/siteDocs/appNotes/1500-022.pdf) | Rev. A0, 2019-12-16 | Raw `.rw.dat` has voltage-scan blocks; scope exclusion / 原始扫描边界 |
| [Quantum Design 1500-031](https://qdusa.com/siteDocs/appNotes/1500-031.pdf) | Rev. A1, 09/2026 | Complementary DC-Scan and SQUID-VSM protocols; avoid universal mode ranking / 模式选择依据 |
| [Origin LabTalk: From Files](https://docs.originlab.com/labtalk/guide/from-files/) | Live documentation, retrieved 2026-11-18 | OGS sections and `run.section` handoff / OGS 运行方式 |
| [Origin LabTalk: Importing Data](https://docs.originlab.com/labtalk/guide/importing-data) | Live documentation, retrieved 2026-11-18 | CSV Data Connector sequence / CSV 导入 |
| [OpenAI: Package your plugin](https://developers.openai.com/plugins/build/plugins) | Live documentation, retrieved 2026-11-18 | Root Agent Plugins 1.0 manifest; skills directory discovery / 插件结构 |
| [ChatGPT: Build skills](https://learn.chatgpt.com/docs/build-skills) | Live documentation, retrieved 2026-11-18 | Skill entrypoint and plugin distribution / 技能入口与分发 |

Library documentation was resolved and queried through Context7 before implementation:

| Library | Context7 ID / documentation | Query concept |
| --- | --- | --- |
| openpyxl | `/websites/openpyxl_readthedocs_io_en_stable`; [official tutorial](https://openpyxl.readthedocs.io/en/stable/tutorial.html), [cell implementation](https://openpyxl.readthedocs.io/en/stable/_modules/openpyxl/cell/cell.html) | Workbook writing; literal strings instead of formulas |
| Matplotlib | `/matplotlib/matplotlib/v3.10.8`; [official source FAQ](https://github.com/matplotlib/matplotlib/blob/v3.10.8/doc/users/faq.rst) | Headless PNG creation and figure lifecycle |
| OriginLab | `/websites/originlab`; [official graph guide](https://docs.originlab.com/labtalk/guide/creating-graphs/de) | `plotxy iy:=(1,2) plot:=200`; axis captions |

The general local skill-creation guide was used only for authoring structure. No pre-existing MPMS conversion code, project data or other local skill was read. No instrument data are sent by these scripts to external services; dependency installation is a separate environment operation.
