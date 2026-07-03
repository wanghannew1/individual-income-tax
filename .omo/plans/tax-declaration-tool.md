# 个税申报数据整理工具 - 工作计划

## TL;DR

> 新建一个面向人力资源劳务派遣公司的个税申报数据整理 Web 工具，替代原累计预扣计算器。
>
> **核心目标**：读取各甲方单位工资表，自动生成当月个税系统导入所需的人员信息采集表、综合所得申报表、甲方单位汇总表；不计算个税，由税务局端自动累计计算。
>
> **Deliverables**:
> - SQLite 数据库及数据模型
> - FastAPI Web 应用（仪表盘、员工库、月度申报、历史记录）
> - 工资表自动识别 + 手动列映射配置
> - 零申报自动带出与取消勾选
> - 三方 Excel 导出
> - pytest 测试覆盖
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Phase 1 scaffolding → database models → single-format parser → web UI → multi-format parser → zero-report logic → export → tests

---

## Context

### Original Request
用户希望将原个税累计预扣计算器改造为面向人力资源劳务派遣公司的个税申报数据整理工具。核心变化：不再累计计算个税，只整理当月收入和扣除；增加员工库、零申报自动带出、按甲方单位汇总；使用数据库存储历史；适配所有工资表格式。

### Interview Summary
**Key Decisions**:
- 新建项目，清空原代码
- 数据库：SQLite（轻量本地，随项目迁移）
- 不保留累计预扣计算功能
- 专项附加扣除不报送（个人端申报）
- 零申报自动带出，允许取消勾选
- 甲方单位从工资表文件名/表头自动提取
- 员工库优先导入税局人员信息表
- 跨单位流动：劳动关系在人力公司，备注甲方单位变化
- 工资表解析：自动识别 + 手动校正列映射

### Research Findings
- 已分析 `东北师范大学人事处202606（系统）.xls` 结构
- 已分析 `王文昭个税-5月.xlsx` 个税申报表格式
- 已确认税局端模板字段

---

## Work Objectives

### Core Objective
构建一个 Web 工具，让人力资源公司能够为派驻各甲方的派遣员工整理和导出个税系统导入数据。

### Concrete Deliverables
1. SQLite 数据库 schema 及初始化脚本
2. SQLModel/SQLAlchemy 数据模型
3. FastAPI 后端路由
4. Jinja2 Web 页面
5. 税局人员信息表导入功能
6. 工资表解析器（东北师范大学格式硬编码 + 通用自动识别）
7. 列映射配置保存与加载
8. 月度申报记录生成逻辑（含零申报自动带出）
9. 人员信息采集表 Excel 导出
10. 综合所得申报表 Excel 导出
11. 甲方单位汇总表 Excel 导出
12. pytest 测试套件
13. 更新 README.md

### Definition of Done
- [ ] 员工库可通过税局人员信息表导入
- [ ] 单个月份可上传多个工资表文件
- [ ] 系统自动识别单位名称、月份、列映射
- [ ] 识别失败时提供 Web 列映射校正界面
- [ ] 零申报员工自动带出在岗人员
- [ ] 可导出三个标准 Excel 申报表
- [ ] pytest 全部通过
- [ ] README 包含安装、使用、配置说明

### Must Have
- SQLite 数据库
- Web 界面
- 员工库导入
- 工资表解析
- 申报表导出
- 零申报逻辑
- 单位汇总

### Must NOT Have (Guardrails)
- 不计算累计应纳税额和个税
- 不报送专项附加扣除
- 不引入外部 API 或数据库服务
- 不做复杂的权限管理（单机使用）

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest)
- **Automated tests**: Tests-after
- **Framework**: pytest
- **Agent-Executed QA**: YES - every task includes browser/curl verification

### QA Policy
Every task MUST include agent-executed QA scenarios. Evidence saved to `.omo/evidence/`.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation):
├── Task 1: 项目脚手架 + SQLite 数据库初始化
├── Task 2: SQLModel 数据模型定义
├── Task 3: 基础 Web 框架和页面布局
└── Task 4: 税局人员信息表导入功能

Wave 2 (Core Logic):
├── Task 5: 工资表解析器（东北师范大学格式 + 通用自动识别）
├── Task 6: 列映射配置持久化
├── Task 7: 月度申报记录生成（含零申报自动带出）
└── Task 8: 员工库 Web 管理页面

Wave 3 (Export + UI + Polish):
├── Task 9: 综合所得申报表 Excel 导出
├── Task 10: 人员信息采集表 Excel 导出
├── Task 11: 甲方单位汇总表 Excel 导出
├── Task 12: 月度申报流程页面
├── Task 13: 历史记录查询页面
└── Task 14: 测试覆盖 + README

Wave FINAL (Verification):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)
```

---

## TODOs

- [ ] 1. 项目脚手架 + SQLite 数据库初始化

  **What to do**:
  - 新建项目结构，清空原代码
  - 创建 `pyproject.toml`、`requirements.txt`
  - 添加依赖：fastapi, uvicorn, jinja2, sqlmodel, pydantic, pandas, openpyxl, xlrd, pytest
  - 创建 SQLite 数据库初始化脚本 `db/database.py`
  - 创建 `data/` 目录存放 SQLite 文件
  - 初始化空数据库

  **Must NOT do**:
  - 不保留原累计预扣计算代码
  - 不引入 PostgreSQL/MySQL

  **Recommended Agent Profile**:
  - **Category**: quick
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocks**: Tasks 2, 3, 4

  **Acceptance Criteria**:
  - [ ] `python -c "from db.database import init_db; init_db()"` 成功创建 SQLite 文件
  - [ ] `pytest` 命令可运行

  **QA Scenarios**:
  ```
  Scenario: 数据库初始化
    Tool: Bash
    Steps:
      1. python -c "from db.database import init_db; init_db()"
      2. ls data/tax_declaration.db
    Expected Result: SQLite 文件存在
    Evidence: .omo/evidence/task-1-db-init.txt
  ```

  **Commit**: YES
  - Message: `chore: scaffold new project and SQLite database`

- [ ] 2. SQLModel 数据模型定义

  **What to do**:
  - 定义 `Employee` 模型：id_card, name, employee_no, status, hire_date, leave_date, latest_unit, latest_pay_month, phone, bank_name, bank_account, memo
  - 定义 `Unit` 模型：name, aliases, first_seen_month, record_count
  - 定义 `MonthlyRecord` 模型：id, employee_id, unit_id, year_month, income, tax_exempt_income, pension, unemployment, medical, housing_fund, is_zero_report, memo
  - 定义 `PayrollFile` 模型：filename, unit_id, year_month, upload_path, record_count, parsed_at
  - 定义 `ParserConfig` 模型：unit_id, header_row, name_col, id_card_col, income_col, pension_col, unemployment_col, medical_col, housing_fund_col, data_start_row

  **Must NOT do**:
  - 不添加累计预扣相关字段

  **Recommended Agent Profile**:
  - **Category**: quick
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Task 1
  - **Blocks**: Tasks 4, 5, 7, 8

  **Acceptance Criteria**:
  - [ ] 所有模型可通过 SQLModel 创建对应表
  - [ ] `pytest tests/test_models.py` 通过

  **QA Scenarios**:
  ```
  Scenario: 创建测试记录
    Tool: Bash
    Steps:
      1. python -c "from db.models import Employee; from sqlmodel import Session; ... create and query"
    Expected Result: 记录成功创建并查询
    Evidence: .omo/evidence/task-2-models.txt
  ```

  **Commit**: YES
  - Message: `feat: define SQLModel entities`

- [ ] 3. 基础 Web 框架和页面布局

  **What to do**:
  - 创建 FastAPI 主应用 `app/main.py`
  - 配置 Jinja2 模板和静态文件
  - 创建基础模板 `base.html`（导航栏、页脚）
  - 创建首页/仪表盘页面
  - 创建路由：`/`、`/employees`、`/monthly`、`/history`

  **Must NOT do**:
  - 不实现具体业务逻辑，只做框架

  **Recommended Agent Profile**:
  - **Category**: visual-engineering
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Task 1
  - **Blocks**: Tasks 8, 12, 13

  **Acceptance Criteria**:
  - [ ] `python -m app.main` 启动服务
  - [ ] `curl http://localhost:8000` 返回 200
  - [ ] 页面包含导航链接

  **QA Scenarios**:
  ```
  Scenario: 首页可访问
    Tool: Bash (curl)
    Steps:
      1. python -m app.main &
      2. curl -s http://localhost:8000 | grep -q "仪表盘"
    Expected Result: 返回 200 且包含仪表盘
    Evidence: .omo/evidence/task-3-homepage.txt
  ```

  **Commit**: YES
  - Message: `feat: setup FastAPI app and base templates`

- [ ] 4. 税局人员信息表导入功能

  **What to do**:
  - 实现 `services/personnel_import.py`
  - 解析税局导出的人员信息 Excel：姓名、证件类型、证件号码、人员状态、任职受雇从业类型、任职受雇从业日期、离职日期、手机号码、户籍所在地
  - 身份证自动提取性别、出生日期
  - 导入到 `Employee` 表，身份证号去重
  - Web 页面上传导入

  **Must NOT do**:
  - 不处理证件类型非居民身份证的情况

  **Recommended Agent Profile**:
  - **Category**: unspecified-high
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Tasks 1, 2
  - **Blocks**: Task 8

  **Acceptance Criteria**:
  - [ ] 上传税局人员表后员工库中有记录
  - [ ] 重复导入不会重复创建
  - [ ] 身份证性别、出生日期自动填充

  **QA Scenarios**:
  ```
  Scenario: 导入税局人员表
    Tool: Bash
    Steps:
      1. 上传模拟税局人员表
      2. 查询数据库 Employee 表
    Expected Result: 记录数正确，性别出生日期正确
    Evidence: .omo/evidence/task-4-import.txt
  ```

  **Commit**: YES
  - Message: `feat: import tax bureau personnel info`

- [ ] 5. 工资表解析器（东北师范大学格式 + 通用自动识别）

  **What to do**:
  - 实现 `services/payroll_parser.py`
  - 文件名解析：提取单位名称和月份（YYYYMM）
  - 东北师范大学格式硬编码解析
  - 通用表头识别：通过关键词匹配姓名、身份证、应发工资、养老、失业、医疗、公积金列
  - 返回解析结果和置信度

  **Must NOT do**:
  - 不写入数据库，只返回解析结果

  **Recommended Agent Profile**:
  - **Category**: deep
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Tasks 1, 2
  - **Blocks**: Task 6

  **Acceptance Criteria**:
  - [ ] 东北师范大学工资表解析成功
  - [ ] 通用表头识别成功率 > 70%
  - [ ] 解析结果包含每行员工的收入、扣除

  **QA Scenarios**:
  ```
  Scenario: 解析东北师范大学工资表
    Tool: Bash
    Steps:
      1. python -c "from services.payroll_parser import parse_payroll; result = parse_payroll('东北师范大学人事处202606（系统）.xls')"
    Expected Result: 解析 25 条记录，单位名正确
    Evidence: .omo/evidence/task-5-parser.txt
  ```

  **Commit**: YES
  - Message: `feat: add payroll parser with auto header detection`

- [ ] 6. 列映射配置持久化

  **What to do**:
  - 实现 `services/parser_config.py`
  - 自动识别失败时，Web 界面展示列映射表单
  - 用户手动指定每列含义后保存到 `ParserConfig` 表
  - 下次同一单位文件自动使用保存的配置

  **Must NOT do**:
  - 不保存原始上传文件到数据库

  **Recommended Agent Profile**:
  - **Category**: unspecified-high
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Tasks 2, 5
  - **Blocks**: Task 12

  **Acceptance Criteria**:
  - [ ] 新单位上传后提示配置列映射
  - [ ] 保存后再次上传同一单位自动使用配置
  - [ ] 配置可修改

  **QA Scenarios**:
  ```
  Scenario: 保存列映射配置
    Tool: Bash + curl
    Steps:
      1. 上传新单位工资表
      2. POST 列映射配置
      3. 查询 ParserConfig 表
    Expected Result: 配置保存成功
    Evidence: .omo/evidence/task-6-config.txt
  ```

  **Commit**: YES
  - Message: `feat: manual column mapping and config persistence`

- [ ] 7. 月度申报记录生成（含零申报自动带出）

  **What to do**:
  - 实现 `services/monthly_record.py`
  - 根据当月工资表解析结果创建 `MonthlyRecord`
  - 自动带出在岗但无工资员工：
    - 遍历员工库 `status = 在岗`
    - 未出现在当月工资表 → 按 `latest_unit` 生成零申报记录
    - 如 `latest_unit` 已离职或为空，则跳过
  - 允许标记某些员工为"本月不申报"
  - 写入 SQLite

  **Must NOT do**:
  - 不计算个税

  **Recommended Agent Profile**:
  - **Category**: deep
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Tasks 2, 4, 5
  - **Blocks**: Tasks 9, 10, 11

  **Acceptance Criteria**:
  - [ ] 上传工资表后生成有收入记录
  - [ ] 在岗无工资员工自动生成零申报记录
  - [ ] 离职员工不生成零申报
  - [ ] 可取消勾选零申报员工

  **QA Scenarios**:
  ```
  Scenario: 零申报自动带出
    Tool: Bash
    Steps:
      1. 导入员工库（10人在岗）
      2. 上传仅含 3 人的工资表
      3. 生成 2026-06 申报记录
      4. 查询 MonthlyRecord
    Expected Result: 3 条有收入 + 7 条零申报（按规则）
    Evidence: .omo/evidence/task-7-zero-report.txt
  ```

  **Commit**: YES
  - Message: `feat: generate monthly records with zero-report auto-fill`

- [ ] 8. 员工库 Web 管理页面

  **What to do**:
  - 创建 `/employees` 页面
  - 显示员工列表（搜索、分页）
  - 支持编辑员工信息（手机、银行、状态、离职日期）
  - 支持单条新增员工
  - 支持导出员工库

  **Must NOT do**:
  - 不做复杂权限

  **Recommended Agent Profile**:
  - **Category**: visual-engineering
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 5)
  - **Blocked By**: Tasks 3, 4
  - **Blocks**: Task 13

  **Acceptance Criteria**:
  - [ ] 页面显示员工列表
  - [ ] 可编辑员工状态
  - [ ] 搜索功能正常

  **QA Scenarios**:
  ```
  Scenario: 编辑员工状态
    Tool: Playwright / curl
    Steps:
      1. GET /employees
      2. POST /employees/{id} update status=离职
      3. GET /employees/{id}
    Expected Result: 状态更新为离职
    Evidence: .omo/evidence/task-8-employee-crud.txt
  ```

  **Commit**: YES
  - Message: `feat: employee management web UI`

- [ ] 9. 综合所得申报表 Excel 导出

  **What to do**:
  - 实现 `services/export_tax_report.py`
  - 导出字段：工号、姓名、证件类型、证件号码、本期收入、本期免税收入、四金、专项附加扣除（填0）、其他扣除、减免税额、备注
  - 有收入和零申报员工全部包含
  - Web 页面提供下载按钮

  **Must NOT do**:
  - 不包含累计应纳税额或个税字段

  **Recommended Agent Profile**:
  - **Category**: quick
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Task 7
  - **Blocks**: Task 12

  **Acceptance Criteria**:
  - [ ] 导出 Excel 文件可打开
  - [ ] 字段顺序和名称符合税局模板
  - [ ] 零申报员工收入为 0

  **QA Scenarios**:
  ```
  Scenario: 导出综合所得申报表
    Tool: Bash
    Steps:
      1. curl -o report.xlsx /monthly/2026-06/export/tax-report
      2. python -c "import pandas as pd; df = pd.read_excel('report.xlsx'); print(df.shape)"
    Expected Result: 文件格式正确，记录完整
    Evidence: .omo/evidence/task-9-export-tax.txt
  ```

  **Commit**: YES
  - Message: `feat: export comprehensive income declaration table`

- [ ] 10. 人员信息采集表 Excel 导出

  **What to do**:
  - 实现 `services/export_personnel.py`
  - 导出字段：工号、姓名、证件类型、证件号码、国籍、性别、出生日期、人员状态、任职受雇从业类型、手机、任职受雇从业日期、离职日期、户籍、开户银行、银行账号、备注
  - 只导出当月新增或状态变化的员工

  **Must NOT do**:
  - 不导出全部历史员工

  **Recommended Agent Profile**:
  - **Category**: quick
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 9)
  - **Blocked By**: Task 7
  - **Blocks**: Task 12

  **Acceptance Criteria**:
  - [ ] 只导出新增/状态变化员工
  - [ ] 字段符合税局人员信息采集模板

  **QA Scenarios**:
  ```
  Scenario: 导出人员信息采集表
    Tool: Bash
    Steps:
      1. curl -o personnel.xlsx /monthly/2026-06/export/personnel
      2. python -c "import pandas as pd; df = pd.read_excel('personnel.xlsx'); print(df.columns.tolist())"
    Expected Result: 字段正确
    Evidence: .omo/evidence/task-10-export-personnel.txt
  ```

  **Commit**: YES
  - Message: `feat: export personnel information collection table`

- [ ] 11. 甲方单位汇总表 Excel 导出

  **What to do**:
  - 实现 `services/export_unit_summary.py`
  - 按单位统计：申报人数、有收入人数、零申报人数、收入合计、四金合计
  - Web 页面展示和下载

  **Must NOT do**:
  - 不计算个税合计

  **Recommended Agent Profile**:
  - **Category**: quick
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 9, 10)
  - **Blocked By**: Task 7
  - **Blocks**: Task 12

  **Acceptance Criteria**:
  - [ ] 汇总表数据与明细一致
  - [ ] 有收入 + 零申报 = 申报人数

  **QA Scenarios**:
  ```
  Scenario: 单位汇总统计
    Tool: Bash
    Steps:
      1. curl -o summary.xlsx /monthly/2026-06/export/summary
      2. python -c "verify sum of income equals total of detail records"
    Expected Result: 汇总数据准确
    Evidence: .omo/evidence/task-11-unit-summary.txt
  ```

  **Commit**: YES
  - Message: `feat: export unit summary table`

- [ ] 12. 月度申报流程页面

  **What to do**:
  - 创建 `/monthly` 页面
  - 步骤式流程：选择月份 → 上传工资表 → 确认列映射 → 确认零申报 → 导出
  - 展示解析结果预览
  - 提供三个导出按钮

  **Must NOT do**:
  - 不做复杂的状态机

  **Recommended Agent Profile**:
  - **Category**: visual-engineering
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Tasks 3, 6, 7, 9, 10, 11
  - **Blocks**: Task 13

  **Acceptance Criteria**:
  - [ ] 完整流程页面可用
  - [ ] 上传、预览、导出可点击
  - [ ] 零申报可取消勾选

  **QA Scenarios**:
  ```
  Scenario: 月度申报流程
    Tool: Playwright
    Steps:
      1. 打开 /monthly
      2. 输入 2026-06
      3. 上传工资表
      4. 确认列映射
      5. 取消部分零申报
      6. 点击导出
    Expected Result: 下载三个 Excel 文件
    Evidence: .omo/evidence/task-12-monthly-flow.txt
  ```

  **Commit**: YES
  - Message: `feat: monthly declaration workflow page`

- [ ] 13. 历史记录查询页面

  **What to do**:
  - 创建 `/history` 页面
  - 按月份列出已生成的申报
  - 可查看每月明细、重新导出

  **Must NOT do**:
  - 不做数据修改功能

  **Recommended Agent Profile**:
  - **Category**: visual-engineering
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Tasks 3, 8, 12
  - **Blocks**: Task 14

  **Acceptance Criteria**:
  - [ ] 历史月份列表正确
  - [ ] 可查看每月明细
  - [ ] 可重新导出

  **QA Scenarios**:
  ```
  Scenario: 查看历史记录
    Tool: Playwright / curl
    Steps:
      1. GET /history
      2. 点击 2026-06
      3. 查看明细
    Expected Result: 显示当月申报记录
    Evidence: .omo/evidence/task-13-history.txt
  ```

  **Commit**: YES
  - Message: `feat: history records page`

- [ ] 14. 测试覆盖 + README

  **What to do**:
  - 编写 pytest 测试：模型、导入、解析、月度记录生成、导出
  - 更新 README.md：安装、使用、工资表格式要求、配置说明
  - 添加示例数据文件（模拟税局人员表、工资表）

  **Must NOT do**:
  - 不写无关文档

  **Recommended Agent Profile**:
  - **Category**: writing
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Tasks 1-13
  - **Blocks**: Wave FINAL

  **Acceptance Criteria**:
  - [ ] pytest 全部通过
  - [ ] README 包含完整使用说明
  - [ ] 示例数据可运行

  **QA Scenarios**:
  ```
  Scenario: 运行测试
    Tool: Bash
    Steps:
      1. pytest tests/ -v
    Expected Result: 所有测试通过
    Evidence: .omo/evidence/task-14-tests.txt
  ```

  **Commit**: YES
  - Message: `test: add tests and update README`

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Verify all Must Have items exist in codebase, all Must NOT Have absent. Check evidence files.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | VERDICT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `pytest`, `ruff`/`flake8`, check for type suppression, unused imports, AI slop.
  Output: `Build [PASS/FAIL] | Tests [N/N] | Quality [VERDICT]`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright`)
  Execute full monthly workflow with sample data. Verify exported Excel files open correctly.
  Output: `Workflow [PASS/FAIL] | Exports [PASS/FAIL] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  Verify no cumulative tax calculation, no special additional deduction reporting, zero-report logic correct.
  Output: `Scope [COMPLIANT/ISSUES] | VERDICT`

---

## Commit Strategy

- Task 1: `chore: scaffold new project and SQLite database`
- Task 2: `feat: define SQLModel entities`
- Task 3: `feat: setup FastAPI app and base templates`
- Task 4: `feat: import tax bureau personnel info`
- Task 5: `feat: add payroll parser with auto header detection`
- Task 6: `feat: manual column mapping and config persistence`
- Task 7: `feat: generate monthly records with zero-report auto-fill`
- Task 8: `feat: employee management web UI`
- Task 9: `feat: export comprehensive income declaration table`
- Task 10: `feat: export personnel information collection table`
- Task 11: `feat: export unit summary table`
- Task 12: `feat: monthly declaration workflow page`
- Task 13: `feat: history records page`
- Task 14: `test: add tests and update README`

---

## Success Criteria

### Verification Commands
```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -c "from db.database import init_db; init_db()"

# 运行测试
pytest tests/ -v

# 启动服务
python -m app.main

# 访问
open http://localhost:8000
```

### Final Checklist
- [ ] 员工库可通过税局人员信息表导入
- [ ] 工资表自动解析成功，失败时可手动映射
- [ ] 零申报员工自动带出
- [ ] 三个 Excel 导出文件格式正确
- [ ] 单位汇总统计准确
- [ ] 历史记录可查询
- [ ] pytest 全部通过
- [ ] README 完整
