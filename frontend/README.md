# 小学生数学知识图谱 - 前端

## 1. 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 页面结构 | HTML5 | 语义化标签 |
| 样式 | Tailwind CSS | 通过 CDN 引入，无需编译 |
| 图表 | Chart.js | 雷达图、柱状图等 |
| 后端 API | 原生 Fetch API | 调用后端 FastAPI 接口 |
| 构建 | 无需构建 | 纯静态页面 |

## 2. 快速启动

### 前提条件
后端 API 服务已启动并运行在 `http://localhost:8000`，详细说明见后端 README。

### 方式一：直接打开（最简单）

直接用浏览器打开 `app/index.html` 即可使用。

> ⚠️ 注意：直接打开时，部分浏览器的 CORS 策略可能阻止 API 请求。推荐使用方式二启动本地服务。

### 方式二：本地静态服务器（推荐）

```bash
cd app
python -m http.server 3000
```

浏览器访问 http://localhost:3000

### 方式三：一键启动脚本（Windows）

双击 `启动Demo.bat` 即可自动启动本地服务器。

## 3. 功能模块

### 3.1 登录页

- 三种角色切换：学生 / 教师 / 管理员
- 账号密码登录（使用 Mock 数据）
- 登录后跳转到对应角色的主页

**测试账号**：

| 角色 | 账号 | 密码 |
|------|------|------|
| 学生 | S001 | 123456 |
| 教师 | T001 | 123456 |
| 管理员 | A001 | admin123 |

### 3.2 学生端 🎒

| 页面 | 功能 | 数据来源 |
|------|------|----------|
| 首页 | 数据统计卡片、今日推荐、快捷入口 | Mock 数据 |
| 拍照录入 | 拍照/相册选图 → 智能识别 → 批改结果 → 订正 | Mock 演示 |
| 错题本 | 待订正/已订正分类、错题详情、立即订正 | Mock 数据 |
| 学习路径 | 薄弱知识点推荐、前置知识、推荐题目、学习建议 | **后端 API** |
| 复习计划 | 生成计划、选择题量、开始练习 | **后端 API** |
| 练习会话 | 答题流程、提交反馈、订正错题、退出练习 | **后端 API** |
| 成长报告 | 五维能力雷达图、薄弱领域、最近进步 | **后端 API** |

### 3.3 教师端 👩‍🏫

| 页面 | 功能 | 数据来源 |
|------|------|----------|
| 仪表盘 | 班级概况、学生数/作业数统计 | **后端 API** |
| 班级管理 | 班级切换、学生列表、掌握度总览 | **后端 API** |
| 作业管理 | 作业上传、提交状态、批改入口 | Mock 演示 |
| 错题分析 | 错因分布、高频错题排行 | **后端 API** |
| 掌握度监控 | 知识点掌握度列表、薄弱知识点预警 | **后端 API** |

### 3.4 管理员端 ⚙️

| 页面 | 功能 | 数据来源 |
|------|------|----------|
| 系统概览 | 总用户数、题库数、知识点数、日活数 | Mock 数据 |
| 题库管理 | 题目统计、难度分布 | Mock 演示 |
| 知识图谱 | 知识点管理、关系管理 | Mock 演示 |
| 用户管理 | 用户列表、角色管理 | Mock 演示 |

## 4. 项目结构

```
app/
├── index.html              # 主页面入口
├── 启动Demo.bat            # Windows 一键启动脚本
├── README.md               # 本文档
└── js/
    ├── api.js              # ⭐ API 调用封装
    ├── app.js              #   应用主控制（路由、登录、模态框）
    ├── login.js            #   登录页面逻辑
    ├── student.js          #   学生端所有页面逻辑
    ├── teacher.js          #   教师端所有页面逻辑
    ├── admin.js            #   管理员端所有页面逻辑
    └── mock-data.js        #   Mock 数据（学生信息、错题、统计数据）
```

## 5. API 调用说明

### 5.1 API 基础配置

所有 API 封装在 `js/api.js` 中，基础地址为：

```javascript
const API_BASE = 'http://127.0.0.1:8000/api';
```

如需修改后端地址，编辑 `js/api.js` 第一行即可。

### 5.2 已封装的 API 方法

#### 学生相关
```javascript
Api.getStudents(grade, className)        // 获取学生列表
Api.getClasses()                          // 获取班级列表
Api.getStudent(studentId)                // 获取单个学生
Api.getStudentMastery(studentId)          // 获取学生掌握度
Api.getStudentWeakPoints(studentId, 60)  // 获取薄弱知识点
Api.getClassStudents(className)           // 获取班级学生
Api.getClassMastery(className)            // 获取班级掌握度
```

#### 知识点 & 题目
```javascript
Api.getKnowledgePoints(grade, semester)  // 知识点列表
Api.getGrowthReport(studentId)            // 成长报告
Api.getLearningPath(studentId)           // 学习路径
Api.getStatisticsOverview()               // 系统统计
```

#### 复习计划
```javascript
Api.calculatePriority(studentId)         // 计算优先级
Api.createReviewPlan(studentId, mode, count) // 生成计划
Api.getReviewPlan(planId)                 // 获取计划
Api.updateReviewPlanCapacity(planId, n)  // 调整题量
Api.startReviewSession(planId)            // 启动练习
Api.getReviewSession(sessionId)           // 获取会话
Api.submitAttempt(sessionId, qId, opt, time) // 提交答案
Api.submitCorrection(attemptId, opt)      // 错题订正
Api.pauseReviewSession(sessionId)         // 暂停会话
Api.resumeReviewSession(sessionId)        // 恢复会话
```

### 5.3 API 调用示例

```javascript
// 获取班级学生并筛选薄弱知识点
async function loadWeakStudents(className) {
    try {
        // 并行获取班级学生和掌握度
        const [studentsRes, masteryRes] = await Promise.all([
            Api.getClassStudents(className),
            Api.getClassMastery(className)
        ]);
        
        const students = studentsRes.data;
        const weakPoints = masteryRes.mastery_data.filter(m => m.avg_mastery < 60);
        
        return { students, weakPoints };
    } catch (error) {
        console.error('加载失败:', error);
        // 降级使用 Mock 数据
        return MockData.studentStats;
    }
}

// 生成复习计划并开始练习
async function startReviewFlow(studentId) {
    // Step 1: 生成计划
    const plan = await Api.createReviewPlan(studentId, 'question_count', 10);
    
    // Step 2: 启动会话
    const session = await Api.startReviewSession(plan.id);
    
    // Step 3: 循环答题
    let currentSession = session;
    while (!currentSession.session_completed) {
        const result = await Api.submitAttempt(
            currentSession.session_id,
            currentSession.current_question.id,
            0, // 选择第一个选项
            30
        );
        
        if (result.is_correct) {
            // 显示正确反馈
        } else {
            // 显示错误反馈，允许订正
        }
        
        // 获取下一题
        currentSession = await Api.getReviewSession(currentSession.session_id);
    }
    
    console.log('练习完成！');
}
```

### 5.4 错误处理

前端已统一处理 API 错误：

```javascript
try {
    const result = await Api.someMethod();
    // 处理成功
} catch (error) {
    if (error.message.includes('404')) {
        console.warn('资源不存在');
    } else if (error.message.includes('500')) {
        console.error('服务器错误');
    } else {
        console.error('未知错误:', error);
    }
    // 降级使用 Mock 数据
}
```

## 6. 数据说明

### 接入真实数据的模块

以下功能已对接后端 API，需要后端服务运行才能正常使用：

- 学习路径推荐
- 成长报告（五维雷达图）
- 复习计划生成
- 练习会话（答题/订正）
- 错题本（真实错题数据）
- 教师端：班级管理、掌握度监控、错题分析
- 管理员端：系统统计

### 使用 Mock 数据的模块

以下功能使用前端 Mock 数据，无需后端即可演示：

- 登录验证
- 拍照录入流程（演示版）
- 作业管理（演示版）
- 用户管理（演示版）
- 部分统计数据展示

## 7. 页面导航结构

```
┌─────────────────────────────────────────────────┐
│                    登录页                        │
└────────────┬────────────┬───────────────────────┘
             │            │
    ┌────────┴──┐    ┌────┴────┐    ┌────────────┐
    │  学生端    │    │ 教师端   │    │  管理员端   │
    ├───────────┤    ├─────────┤    ├────────────┤
    │ 🏠 首页    │    │ 📊 仪表盘│    │ 📊 概览    │
    │ 📷 拍照    │    │ 👥 班级  │    │ 📚 题库    │
    │ 📝 错题本  │    │ 📝 错题  │    │ 🕸️ 图谱   │
    │ 🛤️ 路径    │    │ 📋 作业  │    │ 👥 用户    │
    │ 📊 报告    │    │ 🎯 掌握度│    │            │
    └───────────┘    └─────────┘    └────────────┘
```

## 8. 注意事项

1. **Tailwind CSS 通过 CDN 加载**：首次加载需要网络环境，如果需要离线使用，需将 Tailwind CSS 下载到本地并修改 `index.html` 引用路径。

2. **Chart.js 通过 CDN 加载**：同上，雷达图和图表功能需要网络加载。

3. **后端 API 地址**：在 `js/api.js` 第一行修改，如果后端部署在其他端口或 IP。

4. **CORS 跨域**：后端已配置允许所有来源跨域，直接打开 HTML 文件也能正常调用 API。

5. **Mock 数据 vs 真实数据**：学习路径、成长报告、复习计划等功能已对接后端；拍照录入、作业批改等功能为演示版。

6. **浏览器兼容性**：推荐使用 Chrome / Edge / Firefox 最新版本。

## 9. 常见问题

**Q: 页面打开后空白或一直加载中？**
A: 检查浏览器控制台（F12）是否有 JavaScript 错误。常见原因：CDN 资源加载失败（Tailwind/Chart.js）。

**Q: 学习路径/成长报告显示"加载失败"？**
A: 后端服务未启动或地址不对。检查 `js/api.js` 中的 `API_BASE` 是否正确，确认后端在 `http://localhost:8000` 运行。

**Q: 复习计划生成后无法开始练习？**
A: 确认后端 Neo4j 中已有知识点和题目数据。如果数据库为空，需要先导入数据。

**Q: 如何修改 UI 配色？**
A: 主要颜色在 `index.html` 的 `<style>` 部分定义：
- `.gradient-primary` 紫色渐变（主色调）
- `.gradient-success` 绿色渐变（教师端）
- `.gradient-warning` 橙红渐变（管理员端）
- 修改这些 CSS 类即可全局换色。