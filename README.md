# AstrBot 阿里云千问TTS语音合成插件

基于阿里云DashScope千问TTS模型的语音合成插件，支持多种音色和指令控制功能。

## 功能特性

- ✅ 支持阿里云千问TTS模型 (qwen3-tts-flash / qwen3-tts-instruct-flash)
- ✅ 支持多种预设音色 (Cherry, Alice, Bob, David等)
- ✅ 支持多语种合成 (中文、英文、日文、韩文等)
- ✅ 支持指令控制 (仅instruct模型)
- ✅ 支持流式输出模式
- ✅ 可配置TTS回复概率
- ✅ 自动清理临时文件
- ✅ 支持保存音频文件

## 安装方法

### 1. 获取API密钥

1. 访问 [阿里云百炼平台](https://help.aliyun.com/zh/model-studio/get-api-key)
2. 登录阿里云账号
3. 创建API密钥
4. 复制API密钥备用

### 2. 安装插件

#### 方法一：通过AstrBot WebUI安装
1. 打开AstrBot WebUI
2. 进入插件管理页面
3. 搜索 "阿里云千问TTS语音合成"
4. 点击安装

#### 方法二：手动安装
```bash
# 进入AstrBot插件目录
cd /path/to/AstrBot/data/plugins

# 克隆插件
git clone https://github.com/yourusername/astrbot_plugin_qwen_tts.git

# 安装依赖
cd astrbot_plugin_qwen_tts
pip install -r requirements.txt
```

### 3. 配置插件

在AstrBot WebUI中配置插件参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| api_key | 阿里云DashScope API密钥 | 空 |
| model | TTS模型名称 | qwen3-tts-flash |
| voice | 音色名称 | Cherry |
| language_type | 语种类型 | Auto |
| instructions | 语音合成指令 | 空 |
| optimize_instructions | 是否优化指令 | false |
| tts_probability | TTS回复概率(0-100) | 50 |
| max_text_length | 最大文本长度 | 512 |
| save_audio | 是否保存音频文件 | false |
| stream_mode | 是否使用流式输出 | false |
| output_both_text_and_audio | 是否同时输出文字和语音 | false |

## 使用方法

### 1. 基本使用

安装并配置插件后，机器人回复时会自动将文本转换为语音。

### 2. 音色选择

支持以下预设音色：
- Cherry: 甜美女性声音
- Alice: 温柔女性声音  
- Bob: 沉稳男性声音
- David: 磁性男性声音
- Emily: 活泼女性声音
- Frank: 成熟男性声音
- Grace: 优雅女性声音
- Henry: 年轻男性声音
- Ivy: 知性女性声音
- Jack: 阳光男性声音

### 3. 语种设置

支持以下语种：
- Auto: 自动检测 (默认)
- Chinese: 中文
- English: 英文
- Japanese: 日文
- Korean: 韩文
- German: 德文
- French: 法文
- Spanish: 西班牙文
- Italian: 意大利文
- Portuguese: 葡萄牙文
- Russian: 俄文

### 4. 指令控制 (仅qwen3-tts-instruct-flash模型)

使用指令控制功能可以更精细地控制语音合成效果：

```text
语速较快，带有明显的上扬语调，适合介绍时尚产品。
```

启用优化指令功能可以提升语音合成的自然度和表现力。

### 5. 输出模式选择

插件支持两种输出模式：

#### 仅语音输出 (默认)
- `output_both_text_and_audio: false`
- 机器人回复时只发送语音消息
- 适用于纯语音交互场景

#### 文字+语音同时输出
- `output_both_text_and_audio: true`
- 机器人回复时同时发送文字和语音消息
- 适用于需要文字记录的场景
- 用户可以看到文字内容并收听语音

## 工具脚本

插件包含一个工具脚本用于测试和音色管理：

```bash
# 列出可用音色
python qwen_tts_tool.py --list-voices

# 测试TTS功能
python qwen_tts_tool.py --test --text "测试文本" --voice Cherry

# 使用自定义API密钥
python qwen_tts_tool.py --api-key your_api_key --test --text "测试文本"
```

## 配置示例

### 基本配置
```json
{
  "api_key": "sk-xxxxxxxxxxxxxxxx",
  "model": "qwen3-tts-flash",
  "voice": "Cherry",
  "language_type": "Chinese",
  "tts_probability": 80,
  "max_text_length": 300
}
```

### 高级配置 (指令控制)
```json
{
  "api_key": "sk-xxxxxxxxxxxxxxxx",
  "model": "qwen3-tts-instruct-flash",
  "voice": "Alice",
  "language_type": "Chinese",
  "instructions": "语速适中，语气温柔，适合讲故事",
  "optimize_instructions": true,
  "tts_probability": 100,
  "save_audio": true
}
```

### 文字+语音同时输出配置
```json
{
  "api_key": "sk-xxxxxxxxxxxxxxxx",
  "model": "qwen3-tts-flash",
  "voice": "Cherry",
  "language_type": "Chinese",
  "tts_probability": 80,
  "output_both_text_and_audio": true,
  "save_audio": false
}
```

## 常见问题

### 1. 插件无法加载
- 检查API密钥是否正确
- 检查网络连接是否正常
- 查看AstrBot日志获取详细错误信息

### 2. 语音合成失败
- 确认API密钥有足够的余额
- 检查文本长度是否超过限制
- 尝试更换音色或语种

### 3. 音频文件无法播放
- 确保系统已安装音频播放器
- 检查文件权限
- 尝试使用其他播放器

### 4. 流式模式无法使用
- 确认已安装ffmpeg
- 检查网络连接稳定性
- 尝试使用普通模式

## 依赖说明

- dashscope>=1.20.0: 阿里云DashScope SDK
- aiohttp>=3.9.0: 异步HTTP客户端
- asyncio>=3.4.3: 异步IO支持

## 许可证

MIT License

## 支持与反馈

如有问题或建议，请提交Issue或联系开发者。