# TeachCL lesson-plan co-design assistant

TeachCL 是一个 Streamlit 原型，帮助教师与 AI 共同设计 lesson plan。聊天使用 OpenAI Responses API（默认模型 `gpt-5.4`），回复会边生成边显示；指令来自 `prompts/System_Prompt.txt`。完成协作后，应用生成互动编码、互动模式分析、反思反馈和雷达图，并向参与者浏览器提供 TXT/JSON 下载，同时将完整会话写入 Google Sheets。

## 项目结构

```text
app.py                         Streamlit 页面和流程
llm_client.py                  OpenAI API 客户端
interaction_tracker.py         教师发言编码和频次统计
pattern_detector.py            会话互动模式识别
feedback_generator.py          反思反馈生成与格式校验
scaffold_selector.py            整理雷达图所需的互动代码频次
conversation_export.py         组装会话 JSON 和 TXT 记录
google_drive_store.py          调用 Drive 桥接服务
google_drive_bridge.gs         研究者 Google Apps Script 桥接
prompts/                       助手、编码、模式识别和反馈 prompts
outputs/                       保留的空目录；参与者文件由浏览器下载
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

Apps Script 会在 Drive 根目录下自动创建三个文件夹：`content/` 保存对话 `.txt`，`analysis/` 保存分析 `.txt`，`feedback/` 保存反馈 `.txt` 和雷达图 `.png`。被试点击 **Finish collaboration and generate reflection** 且分析成功后，浏览器会尝试自动下载 `participant_<ID>_<session_id>.txt` 与 `.json`；若浏览器拦截自动下载，完成页提供两个下载按钮。下载文件通常进入浏览器默认的 Downloads 文件夹，具体位置取决于浏览器设置。每条消息也会写入 Google Sheets 的一行。云端暂时不可用时，待上传记录会在当前 Streamlit 会话后续交互时重试。

记录字段包括匿名 participant ID、session ID、时间、消息角色/文本/轮次；分析记录包括编码、模式、证据、反馈文本和反馈特征。参与者界面不提供记录下载或 Drive 文件链接，也不显示模式标签、证据和编码明细。

### 一次性 Google 设置

1. 使用研究者 Google 账号打开 [Google Apps Script](https://script.google.com/) 并新建项目。
2. 将仓库 `google_drive_bridge.gs` 的完整内容复制到脚本编辑器并保存。
3. 从 Google Drive 的 `chat log output` 文件夹网址复制 `/folders/` 后的 ID。
4. 创建一个 Google Sheet，并在 Apps Script **Project Settings → Script Properties** 新增 `ROOT_FOLDER_ID`、`ARCHIVE_TOKEN`、`SPREADSHEET_ID`。可选新增 `SHEET_NAME`（默认 `Experiment Data`）。表格首行由脚本创建，列为 `ID, role, messages, timestamp, coding, pattern, visualized feedback, session_id`。令牌应为高强度随机字符串，不要提交到 GitHub。
5. 选择 **Deploy → New deployment → Web app**，设置 **Execute as me**。访问权限按部署环境选择；若选择 Anyone，只有持有保密 token 的请求能通过脚本验证。部署后复制 `/exec` URL。
6. 在 Streamlit Cloud 应用的 **Settings → Secrets** 加入：

```toml
[google_drive]
web_app_url = "https://script.google.com/macros/s/部署ID/exec"
archive_token = "与 Apps Script Script Properties 相同的随机字符串"
```

7. 将 `SPREADSHEET_ID` 设为所建 Google Sheet 的 ID；URL 和 token 沿用 Streamlit Secrets 中的 Drive 桥接配置。部署或更新 Apps Script 后，重启应用并完成一次协作，确认 Drive 文件和 Sheet 数据均已生成。不要在 GitHub、参与者界面或日志中放置 token。

## 会话和分析流程

- 教师每发一条消息、助手每生成一条回复，应用都会更新 Drive 中的对话 TXT。
- 点击 **Finish collaboration and generate reflection** 后才运行编码、模式识别和反馈；全部成功后应用会自动触发浏览器 TXT/JSON 下载并同步 Google Sheets。普通聊天不会触发这些归档。
- 编码/模式阶段完成后分别更新分析 TXT；生成反馈后保存反馈 TXT 和雷达图 PNG。若上传暂时失败，应用继续聊天/分析，并在后续交互重试。
- 雷达图在内存中生成并显示给参与者，同时归档 PNG 到 Drive。图表展示频次，不代表教师能力评分。

## GitHub Codespaces

`.devcontainer/devcontainer.json` 配置开发容器并转发 Streamlit 的 8501 端口。部署到 Streamlit Community Cloud 时，应选择仓库中实际的 `app.py` 入口和 `requirements.txt`。

## 依赖

`requirements.txt` 列出 Streamlit、OpenAI Python SDK、Matplotlib、NumPy 和 Requests。
