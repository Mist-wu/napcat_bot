napcat_bot/                        # 项目根目录
├── src/                           # 核心源代码
│   ├── ai/                        # AI相关代码（大模型、图片识别、上下文管理等）
│   │   ├── ai_deepseek.py         # DeepSeek大模型API封装
│   │   ├── context_memory.py      # 上下文历史数据库管理（核心：用SQLite）
│   │   ├── img_recog.py           # 图片识别相关
│   │   └── llm_client.py          # LLM（大模型）客户端基类
│   ├── tools/                     # 工具与业务模块
│   │   ├── command.py             # 指令处理
│   │   ├── weather.py             # 天气查询
│   │   ├── check_student.py       # 学生身份认证
│   │   └── brawl.py               # Brawl Stars查询等
│   ├── utils/                     # 工具代码
│   │   ├── extract.py             # 消息内容提取
│   │   ├── output.py              # 消息发送接口
│   │   ├── state_manager.py       # 状态机（多轮对话等）
│   │   └── user_db.py             # 用户状态/数据管理
├── config/                        # 配置相关
│   └── config.py                  # 各类配置（如API Token、数据库路径、白名单等）
├── data/                          # 持久化数据
│   └── context_memory.db          # SQLite数据库上下文历史（自动生成）
├── requirements.txt               # Python依赖包列表
├── README.md                      # 项目说明文档
└── main.py                        # 启动入口，消息主循环、AI与指令集成

