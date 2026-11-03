# TeachCL lesson-plan co-design assistant

TeachCL 是一个 Streamlit 原型，帮助教师与 AI 共同设计 lesson plan。聊天使用 OpenAI Responses API（默认模型 `gpt-5.4`），指令来自 `prompts/System_Prompt.txt`。完成协作后，应用生成互动编码、互动模式分析、反思反馈和雷达图。参与者能看到雷达图和反馈；编码、模式、证据及研究记录只归档到研究者的 Google Drive。

## 项目结构

```text
app.py                         Streamlit 页面和流程
llm_client.py                  OpenAI API 客户端
interaction_tracker.py         教师发言编码和频次统计
pattern_detector.py            会话互动模式识别
feedback_generator.py          反思反馈生成与格式校验
scaffold_selector.py            生成反馈特征
conversation_export.py         组装 JSON 记录，不写本地文件
google_drive_store.py          调用 Drive 桥接服务
google_drive_bridge.gs         研究者 Google Apps Script 桥接
prompts/                       助手、编码、模式识别和反馈 prompts
outputs/                       不用于保存运行记录
```

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

在侧边栏输入 OpenAI API key。密钥只用于当前 Streamlit 会话。部署到 Streamlit Cloud 时，可在应用的 Secrets 中设置 `OPENAI_API_KEY`，或者在侧边栏输入。

## 将记录归档到 Google Drive

应用把实时对话记录上传到研究者 Google Drive 中的 `chat log output/conversations/`。协作结束后，分析记录写入 `chat log output/analyses/`。Apps Script 会自动创建这两个子文件夹，并按 session ID 更新同一 JSON 文件。应用不会把研究记录、雷达图图片或 API 密钥写入本地文件；云端未配置或暂时不可用时，当前浏览器会话会保留待上传记录并在后续交互时重试。浏览器关闭后仍未上传的记录无法保证保留，因此研究部署前请先完成云端设置并做端到端验证。

记录字段包括匿名 participant ID、session ID、时间、消息角色/文本/轮次；分析记录包括编码、模式、证据、反馈文本和反馈特征。参与者界面不提供记录下载或 Drive 文件链接，也不显示模式标签、证据和编码明细。

### 一次性 Google 设置

1. 使用研究者 Google 账号打开 [Google Apps Script](https://script.google.com/) 并新建项目。
2. 将仓库 `google_drive_bridge.gs` 的完整内容复制到脚本编辑器并保存。
3. 从 Google Drive 的 `chat log output` 文件夹网址复制 `/folders/` 后的 ID。
4. 在 Apps Script **Project Settings → Script Properties** 新增 `ROOT_FOLDER_ID` 和 `ARCHIVE_TOKEN`。令牌应为高强度随机字符串，不要提交到 GitHub。
5. 选择 **Deploy → New deployment → Web app**，设置 **Execute as me**。访问权限按部署环境选择；若选择 Anyone，只有持有保密 token 的请求能通过脚本验证。部署后复制 `/exec` URL。
6. 在 Streamlit Cloud 应用的 **Settings → Secrets** 加入：

```toml
[google_drive]
web_app_url = "https://script.google.com/macros/s/部署ID/exec"
archive_token = "与 Apps Script Script Properties 相同的随机字符串"
```

7. 保存后重启应用，进行一次测试协作，确认 Drive 的两个子文件夹中出现对应 JSON。不要在 GitHub、参与者界面或日志中放置 token。代码尚不能替代这项手动部署，也不会声称云端上传成功，直到你在 Drive 中确认文件。

## 会话和分析流程

- 教师每发一条消息、助手每生成一条回复，应用都会更新云端原始对话 JSON。
- 点击 **Finish collaboration and generate reflection** 后才运行编码、模式识别和反馈；普通聊天不会触发这些分析。
- 编码/模式阶段完成后分别更新分析 JSON；生成反馈后再次更新。若上传暂时失败，应用继续聊天/分析，并在后续交互重试。
- 雷达图在内存中生成并显示给参与者，不写入本地。图表展示频次，不代表教师能力评分。

## GitHub Codespaces

`.devcontainer/devcontainer.json` 配置开发容器并转发 Streamlit 的 8501 端口。部署到 Streamlit Community Cloud 时，应选择仓库中实际的 `app.py` 入口和 `requirements.txt`。

## 依赖

`requirements.txt` 列出 Streamlit、OpenAI Python SDK、Matplotlib、NumPy 和 Requests。
