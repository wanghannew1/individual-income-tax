# 个税申报数据整理工具

面向人力资源劳务派遣公司的个税申报数据整理 Web 工具。

## 核心功能

- **员工库管理**：导入税局人员信息表，管理派遣员工状态
- **工资表解析**：自动识别各甲方单位工资表格式，提取收入和扣除数据
- **零申报自动带出**：在岗但无工资的员工自动生成零申报记录
- **三方 Excel 导出**：综合所得申报表、人员信息采集表、甲方单位汇总表
- **历史记录**：按月份查看已生成的申报数据

## 安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python3 -c "from db.database import init_db; init_db()"
```

## 使用

```bash
# 启动服务
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 访问
open http://localhost:8000
```

### 工作流程

1. **导入员工库**：在「员工库」页面上传税局导出的人员信息表
2. **月度申报**：
   - 选择申报月份
   - 上传各甲方单位工资表（支持 .xls 和 .xlsx）
   - 系统自动识别单位名称、月份、列映射
   - 预览解析结果，确认无误后生成申报数据
   - 零申报员工自动带出，可取消勾选
3. **导出**：下载三个标准 Excel 文件，导入自然人电子税务局扣缴端

### 工资表格式要求

系统自动识别以下列（关键词匹配）：

| 字段 | 识别关键词 |
|------|-----------|
| 姓名 | 姓名、名字 |
| 身份证号 | 身份证、证件号 |
| 本期收入 | 应发、工资、收入、薪金 |
| 养老保险 | 养老 |
| 失业保险 | 失业 |
| 医疗保险 | 医疗 |
| 住房公积金 | 公积金 |

单位名称和月份从文件名自动提取（如 `东北师范大学人事处202606（系统）.xls`）。

## 项目结构

```
├── app/
│   ├── main.py              # FastAPI 主应用
│   ├── routers/             # 路由处理器
│   │   ├── dashboard.py     # 仪表盘
│   │   ├── employees.py     # 员工管理
│   │   ├── monthly.py       # 月度申报
│   │   └── history.py       # 历史记录
│   ├── templates/           # Jinja2 模板
│   └── static/              # CSS 等静态文件
├── db/
│   ├── database.py          # SQLite 数据库初始化
│   └── models.py            # SQLModel 数据模型
├── services/
│   ├── payroll_parser.py    # 工资表解析器
│   ├── personnel_import.py  # 税局人员信息导入
│   ├── monthly_service.py   # 月度记录生成（含零申报）
│   └── export_service.py    # Excel 导出
├── tests/                   # pytest 测试
├── data/                    # SQLite 数据库文件
├── uploads/                 # 上传的工资表文件
├── requirements.txt
└── pyproject.toml
```

## 数据模型

- **Employee**：员工信息（身份证、姓名、状态、所属单位等）
- **Unit**：甲方单位
- **MonthlyRecord**：月度申报记录（收入、社保扣除、零申报标记）
- **PayrollFile**：上传的工资表文件记录
- **ParserConfig**：单位列映射配置

## 测试

```bash
pytest tests/ -v
```

## 注意事项

- 专项附加扣除不通过此工具报送（由个人在个税 APP 端申报）
- 不计算累计应纳税额（由税务局端自动累计计算）
- 离职员工不生成零申报记录
- 支持取消勾选零申报员工（标记为"本月不申报"）
