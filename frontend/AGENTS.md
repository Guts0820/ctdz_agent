# 前端模块维护说明

## 模块定位

本模块是“小学生数学知识图谱”系统的静态浏览器前端。它不含构建工具或服务端逻辑，通过原生 Fetch 调用后端 API 网关；教师和管理员部分功能仍可使用本地 Mock 数据展示。

## 架构

`index.html` 载入 Tailwind CSS、Chart.js 与 `js/` 下的脚本。`app.js` 负责应用入口、页面路由和弹窗；`login.js` 管理登录；`student.js`、`teacher.js`、`admin.js` 管理各角色页面；`api.js` 集中封装 HTTP 请求；`mock-data.js` 提供尚未实现接口的演示数据。拍照作业流由 `StudentPage.pickImage()` 读取图片并调用 `Api.submitHomework()`。

## 目录结构

- `index.html`：页面入口、公共样式和脚本加载顺序。
- `js/api.js`：网关地址与 API 请求封装。
- `js/student.js`：学生端页面与拍照录入、展示结果流程。
- `js/teacher.js`、`js/admin.js`：教师端、管理员端页面。
- `js/login.js`、`js/app.js`：登录与全局页面状态。
- `js/mock-data.js`：前端展示用 Mock 数据。
- `启动Demo.bat`：启动本地静态服务。

## 开发规范

使用 ES5/ES6 兼容的原生 JavaScript、四空格缩进和 camelCase 命名。请求统一经 `Api.fetch()`，异步调用必须提供加载、成功和失败反馈；图片上传不得写入本地存储或日志。交互元素应使用可聚焦的语义化控件，保留可见文案，避免仅用颜色表达状态。继续沿用现有 Tailwind 工具类和页面视觉语言。

## 常用命令

在本目录执行 `python -m http.server 3000`，浏览器访问 `http://127.0.0.1:3000`。当前未发现前端测试、构建或格式化配置，待确认后再补充。

## 修改指南

后端请求路径以 `js/api.js` 的 `API_BASE` 为准；响应字段变动时同步修改学生端结果展示和 README。拍照流需要验证图片选择、请求中、成功结果和服务不可用提示，且不应回退为虚构的识别结果。
