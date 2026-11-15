# TeachCL lesson-plan co-design assistant

TeachCL 是一个 Streamlit 原型，帮助教师与 AI 共同设计 lesson plan。聊天使用 OpenAI Responses API（默认模型 `gpt-5.4`）。完成协作后，应用生成互动编码、互动模式分析、反思反馈和雷达图，并提供包含完整实验记录的本地下载包。聊天记录和分析结果不会上传到 Drive 或 Google Sheets。

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

在侧边栏输入 OpenAI API key。密钥只用于当前 Streamlit 会话。聊天与分析内容会发送给 OpenAI API 以提供 AI 功能；应用不会将记录归档到 Drive 或 Google Sheets，也不会把完成记录保存为服务器文件。

## 实验记录下载

- 点击 **Finish collaboration and generate reflection** 后，待编码、互动模式和反馈均成功生成，应用会自动触发 `<ID>_data.zip` 下载；若浏览器拦截自动下载，可点击完成页的下载按钮。
- ZIP 中有 `<ID>_data/` 文件夹，内含 `<ID>.xlsx`、`<ID>.json`、`<ID>.txt` 三个文件。将 ZIP 解压到桌面即可得到该文件夹。
- 浏览器安全机制不允许网页未经用户选择就直接在桌面创建文件夹；下载位置由浏览器设置决定。
- `.xlsx` 是现代 Excel 工作簿格式（用户提到的 `.xsl` 不是 Excel 工作簿扩展名）。表格每条对话消息占一行，列为被试 ID、AI/user、对话内容、对应 code、interaction pattern、feedback 文本和时间戳。会话级 pattern 与 feedback 在每行重复；code 对应教师消息，AI 消息的 code 留空。
- JSON 和 TXT 保存完整对话、角色、时间戳、编码、互动模式、反馈文本以及图表频次数据。
- 每次新对话生成一个新的数字被试 ID。文件在浏览器中下载，不会在 Streamlit 服务器上保存为参与者记录。

## 会话流程

- 普通聊天期间不创建记录文件。
- 点击 **Finish collaboration and generate reflection** 后运行编码、互动模式识别和反馈生成；全部成功后生成三种格式的记录包。
- 雷达图在内存中生成并显示给参与者；频次图不代表教师能力评分。

## GitHub Codespaces

`.devcontainer/devcontainer.json` 配置开发容器并转发 Streamlit 的 8501 端口。部署到 Streamlit Community Cloud 时，应选择仓库中的 `app.py` 入口和 `requirements.txt`。

## 依赖

`requirements.txt` 列出 Streamlit、OpenAI Python SDK、Matplotlib、NumPy、Requests 和 OpenPyXL。
