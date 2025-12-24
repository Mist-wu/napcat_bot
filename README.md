# NapCat Bot 使用指南

## 一、运行环境准备

1. **安装 NapCat 主程序（Linux 环境）**

   推荐一键脚本安装（适用于 Ubuntu 20+/Debian 10+/CentOS 9）：

   ```bash
   curl -o napcat.sh https://nclatest.znin.net/NapNeko/NapCat-Installer/main/script/install.sh && bash napcat.sh --tui
   ```

   按提示完成 NapCat 主控端与 QQ 账号的连接配置。

2. **Python 依赖安装**

   确保主机已安装 python3（建议3.8及以上），并且已安装 pip。
   进入本项目目录，执行：

   ```bash
   pip install -r requirements.txt
   ```

3. **环境变量配置**

   项目部分功能需配置 API key，编辑 `.env` 文件（可复制 `.env.example`，填入内容）：

   ```ini
   WEATHER_API_KEY=你的天气接口APIKEY
   DEEPSEEK_API_KEY=你的深析AI接口APIKEY
   NAPCAT_TOKEN=你的NapCatToken
   ```

   NapCat Token 获取方式详见 NapCat 官方文档（如有疑问请访问 NapCat 社区）。

---

## 二、启动机器人

在项目根目录执行：

```bash
python main.py
```

启动后，NapCat Bot 会自动连接 NapCatQQ 服务并监听消息。

---

## 三、主要功能说明

### 私聊功能

- 支持多轮对话AI助手（DeepSeek，支持图片内容识别）
- BUPT学生认证：`/认证` 按提示完成校园统一认证
- 宿舍电费查询与多步电费绑定、预警（首次需认证并绑定）
- 天气查询与自动播报订阅
- 其他娱乐/实用指令

### 群聊功能

- 启用[AI聊天/指令]需好友拉入白名单群组（在 config/config.py 里配置）
- `/指令` 查看全部命令（只列出部分核心命令示例）：
    - `/天气 [城市名]`
    - `/龙` `/猫` `/图` `/图图`
    - `/查玩家 [tag]` `/查战队 [tag]`
    - `/快递 [单号]`
    - `/启用/禁用天气播报`
    - `/启用/禁用电费预警`
    - `/咬 @xxx` `/玩 @xxx` `/丢 @xxx` `/撕 @xxx`
- 群AI图片识别与应答（支持发图，AI自动文字识别与回复）

### 电费与校园认证

- 首次 `/认证` 按步骤输入学号与统一身份认证密码
- `/查询电费` 查询当前绑定宿舍电费
- 换宿舍时 `/查询电费 换宿舍` 按引导重新绑定宿舍
- 电费预警每日自动推送（若设置）

---

## 四、图片智能识别

- 私聊或群聊发送图片时，可自动识别内容并AI生成相关回复，支持多张图片批量处理。
- 动图暂不支持，会有提示。

---

## 五、常见问题

1. **Token/密钥未设置或错误**
   - 如果反馈 "未配置XX密钥"，请检查 `.env` 文件及环境变量是否正确设置。
2. **部分群组无法使用AI或指令**
   - 请确认已将对应群号加入 config/config.py 的白名单集合。
3. **认证失败或电费查询异常**
   - 检查输入账号/密码是否正确，或校园统一认证服务状态。

---

## 六、参考文档

NapCat API/接口文档：[NapCat官方Apifox接口文档](https://napcat.apifox.cn/llms.txt)

---

## 七、项目维护与反馈

如遇到bug或建议，请通过GitHub Issues提交，或联系项目维护者。

```
本项目仅供校园学习&娱乐使用，请勿用于商业用途或泄漏个人隐私信息。
```