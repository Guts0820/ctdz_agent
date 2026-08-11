const AdminPage = {
    render() {
        return `
        <div class="min-h-screen bg-gray-50">
            ${this.renderHeader()}
            <div class="p-4">
                <div id="admin-content"></div>
            </div>
            ${this.renderTabBar()}
        </div>`;
    },
    
    renderHeader() {
        const s = MockData.adminDashboard.systemOverview;
        const user = MockData.currentUser;

        return `
        <div class="gradient-warning text-white p-4">
            <div class="flex items-center justify-between">
                <div>
                    <div class="text-sm opacity-90">管理后台</div>
                    <div class="text-xl font-bold">系统控制台</div>
                </div>
                <div class="relative">
                    <button onclick="AdminPage.toggleUserMenu()" class="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center text-2xl hover:bg-white/30 transition">
                        ${user ? user.avatar : '⚙️'}
                    </button>
                    <div id="user-menu" class="hidden absolute right-0 top-full mt-2 bg-white rounded-xl shadow-lg border py-2 w-48 z-50">
                        <div class="px-4 py-2 border-b">
                            <div class="text-sm font-medium text-gray-800">${user.name}</div>
                            <div class="text-xs text-gray-500">${user.id}</div>
                        </div>
                        <button onclick="AdminPage.showAccountInfo()" class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2">
                            👤 账号信息
                        </button>
                        <button onclick="AdminPage.showSettings()" class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2">
                            ⚙️ 设置
                        </button>
                        <div class="border-t my-1"></div>
                        <button onclick="App.logout()" class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2">
                            🚪 退出登录
                        </button>
                    </div>
                </div>
            </div>
            <div class="mt-4 grid grid-cols-4 gap-2 text-center text-xs">
                <div class="bg-white/20 rounded-lg p-2">
                    <div class="font-bold text-lg">${s.totalUsers}</div>
                    <div>总用户</div>
                </div>
                <div class="bg-white/20 rounded-lg p-2">
                    <div class="font-bold text-lg">${s.totalQuestions}</div>
                    <div>题库</div>
                </div>
                <div class="bg-white/20 rounded-lg p-2">
                    <div class="font-bold text-lg">${s.totalKnowledgePoints}</div>
                    <div>知识点</div>
                </div>
                <div class="bg-white/20 rounded-lg p-2">
                    <div class="font-bold text-lg">${s.todayActiveUsers}</div>
                    <div>今日活跃</div>
                </div>
            </div>
        </div>`;
    },

    toggleUserMenu() {
        const menu = document.getElementById('user-menu');
        if (menu) {
            menu.classList.toggle('hidden');
        }
    },

    showAccountInfo() {
        this.toggleUserMenu();
        const user = MockData.currentUser;
        App.showModal('👤 账号信息', `
            <div class="text-center mb-4">
                <div class="text-5xl mb-2">${user.avatar}</div>
                <div class="font-bold text-lg">${user.name}</div>
                <div class="text-sm text-gray-500">${user.id}</div>
            </div>
            <div class="space-y-2">
                <div class="flex justify-between p-2 bg-gray-50 rounded-lg">
                    <span class="text-gray-600">角色</span>
                    <span class="font-medium">管理员</span>
                </div>
            </div>
        `);
    },

    showSettings() {
        this.toggleUserMenu();
        App.showModal('⚙️ 设置', `
            <div class="space-y-3">
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span>消息通知</span>
                    <input type="checkbox" checked class="w-5 h-5">
                </div>
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span>声音提示</span>
                    <input type="checkbox" checked class="w-5 h-5">
                </div>
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span>自动播放动画</span>
                    <input type="checkbox" class="w-5 h-5">
                </div>
            </div>
            <p class="text-xs text-gray-500 mt-4 text-center">更多设置功能正在开发中...</p>
        `);
    },

    renderTabBar() {
        return `
        <div class="fixed bottom-0 left-0 right-0 bg-white shadow-lg border-t">
            <div class="flex justify-around py-2">
                <button onclick="AdminPage.navigate('overview')" id="a-overview" class="a-nav flex flex-col items-center px-3 py-2 rounded-lg transition">
                    <span class="text-xl">📊</span><span class="text-xs">概览</span>
                </button>
                <button onclick="AdminPage.navigate('questions')" id="a-questions" class="a-nav flex flex-col items-center px-3 py-2 rounded-lg transition">
                    <span class="text-xl">📚</span><span class="text-xs">题库</span>
                </button>
                <button onclick="AdminPage.navigate('kg')" id="a-kg" class="a-nav flex flex-col items-center px-3 py-2 rounded-lg transition">
                    <span class="text-xl">🕸️</span><span class="text-xs">知识图谱</span>
                </button>
                <button onclick="AdminPage.navigate('users')" id="a-users" class="a-nav flex flex-col items-center px-3 py-2 rounded-lg transition">
                    <span class="text-xl">👥</span><span class="text-xs">用户</span>
                </button>
            </div>
        </div>`;
    },
    
    navigate(page) {
        document.querySelectorAll('.a-nav').forEach(btn => btn.classList.remove('tab-active'));
        const navMap = { overview: 'a-overview', questions: 'a-questions', kg: 'a-kg', users: 'a-users' };
        const activeBtn = document.getElementById(navMap[page]);
        if (activeBtn) activeBtn.classList.add('tab-active');
        
        const content = document.getElementById('admin-content');
        const renderMap = {
            overview: this.renderOverview,
            questions: this.renderQuestions,
            kg: this.renderKG,
            users: this.renderUsers
        };
        content.innerHTML = renderMap[page]();
        if (page === 'overview') this.initOverviewCharts();
        if (page === 'questions') this.initQuestionsCharts();
    },
    
    renderOverview() {
        const s = MockData.adminDashboard.systemOverview;
        return `
        <div class="space-y-4">
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">📊 系统概览</div>
                <div class="grid grid-cols-2 gap-3">
                    <div class="p-4 bg-blue-50 rounded-xl text-center">
                        <div class="text-3xl font-bold text-blue-600">${s.totalStudents}</div>
                        <div class="text-sm text-gray-600">学生用户</div>
                    </div>
                    <div class="p-4 bg-green-50 rounded-xl text-center">
                        <div class="text-3xl font-bold text-green-600">${s.totalTeachers}</div>
                        <div class="text-sm text-gray-600">教师用户</div>
                    </div>
                    <div class="p-4 bg-purple-50 rounded-xl text-center">
                        <div class="text-3xl font-bold text-purple-600">${s.totalClasses}</div>
                        <div class="text-sm text-gray-600">班级数</div>
                    </div>
                    <div class="p-4 bg-orange-50 rounded-xl text-center">
                        <div class="text-3xl font-bold text-orange-600">${s.todayActiveUsers}</div>
                        <div class="text-sm text-gray-600">今日活跃</div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">📈 用户活跃趋势</div>
                <canvas id="activeChart" height="150"></canvas>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">⚠️ 关键指标</div>
                <div class="space-y-2">
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                        <div>
                            <div class="text-sm font-medium">题库使用率</div>
                            <div class="text-xs text-gray-500">已使用题目 / 总题目</div>
                        </div>
                        <div class="text-right">
                            <div class="text-xl font-bold text-green-600">78%</div>
                        </div>
                    </div>
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                        <div>
                            <div class="text-sm font-medium">知识点覆盖率</div>
                            <div class="text-xs text-gray-500">已掌握 / 总知识点</div>
                        </div>
                        <div class="text-right">
                            <div class="text-xl font-bold text-orange-600">65%</div>
                        </div>
                    </div>
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                        <div>
                            <div class="text-sm font-medium">错题订正率</div>
                            <div class="text-xs text-gray-500">已订正 / 总错题</div>
                        </div>
                        <div class="text-right">
                            <div class="text-xl font-bold text-red-600">45%</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;
    },
    
    initOverviewCharts() {
        setTimeout(() => {
            const ctx = document.getElementById('activeChart');
            if (ctx) {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: ['7/21', '7/22', '7/23', '7/24', '7/25', '7/26', '7/27'],
                        datasets: [{
                            label: '活跃用户',
                            data: [650, 720, 800, 780, 850, 920, 856],
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.3,
                            fill: true
                        }]
                    },
                    options: { scales: { y: { beginAtZero: true } } }
                });
            }
        }, 100);
    },
    
    renderQuestions() {
        const k = MockData.adminDashboard.knowledgeStats;
        return `
        <div class="space-y-4">
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="flex items-center justify-between mb-3">
                    <div class="font-bold">📚 题库管理</div>
                    <button onclick="AdminPage.addQuestion()" class="bg-purple-600 text-white text-sm px-3 py-1 rounded-lg">+ 新增题目</button>
                </div>
                <div class="grid grid-cols-3 gap-2 text-center">
                    <div class="p-3 bg-gray-50 rounded-xl">
                        <div class="text-2xl font-bold">${MockData.adminDashboard.systemOverview.totalQuestions}</div>
                        <div class="text-xs text-gray-500">总题数</div>
                    </div>
                    <div class="p-3 bg-green-50 rounded-xl">
                        <div class="text-2xl font-bold text-green-600">${k.byDifficulty.reduce((s, d) => s + d.count, 0)}</div>
                        <div class="text-xs text-gray-500">已审核</div>
                    </div>
                    <div class="p-3 bg-orange-50 rounded-xl">
                        <div class="text-2xl font-bold text-orange-600">12</div>
                        <div class="text-xs text-gray-500">待审核</div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">📊 题目分布</div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <div class="text-sm text-gray-600 mb-2">按年级</div>
                        <canvas id="gradeChart" height="150"></canvas>
                    </div>
                    <div>
                        <div class="text-sm text-gray-600 mb-2">按难度</div>
                        <canvas id="diffChart" height="150"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">📋 最近新增题目</div>
                <div class="space-y-2">
                    ${k.recentAdded.map(q => `
                        <div class="p-3 border rounded-xl">
                            <div class="flex items-center justify-between mb-1">
                                <div class="font-medium text-sm">${q.title}</div>
                                <span class="badge bg-blue-100 text-blue-600">难度${q.difficulty}</span>
                            </div>
                            <div class="text-xs text-gray-500">
                                ID: ${q.id} | 知识点: ${q.knowledge} | 添加时间: ${q.date}
                            </div>
                            <div class="flex gap-2 mt-2">
                                <button onclick="AdminPage.editQuestion('${q.id}')" class="text-xs bg-gray-100 px-2 py-1 rounded">编辑</button>
                                <button onclick="AdminPage.deleteQuestion('${q.id}')" class="text-xs bg-red-100 text-red-600 px-2 py-1 rounded">删除</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>`;
    },
    
    initQuestionsCharts() {
        setTimeout(() => {
            const k = MockData.adminDashboard.knowledgeStats;
            
            const gradeCtx = document.getElementById('gradeChart');
            if (gradeCtx) {
                new Chart(gradeCtx, {
                    type: 'bar',
                    data: {
                        labels: k.byGrade.map(g => `${g.grade}年级`),
                        datasets: [{
                            label: '题目数',
                            data: k.byGrade.map(g => g.count),
                            backgroundColor: 'rgba(102, 126, 234, 0.7)'
                        }]
                    }
                });
            }
            
            const diffCtx = document.getElementById('diffChart');
            if (diffCtx) {
                new Chart(diffCtx, {
                    type: 'doughnut',
                    data: {
                        labels: k.byDifficulty.map(d => `难度${d.difficulty}`),
                        datasets: [{
                            data: k.byDifficulty.map(d => d.count),
                            backgroundColor: ['#4facfe', '#43e97b', '#fa709a', '#f5576c', '#f093fb']
                        }]
                    }
                });
            }
        }, 100);
    },
    
    addQuestion() {
        alert('新增题目功能\n\n可以：\n1. 手动创建题目\n2. 批量导入\n3. AI智能生成\n\n（需对接题库管理模块）');
    },
    
    editQuestion(id) {
        alert(`编辑题目 ${id}\n\n（需对接题库管理模块）`);
    },
    
    deleteQuestion(id) {
        if (confirm(`确定删除题目 ${id} 吗？`)) {
            alert('题目已删除');
        }
    },
    
    renderKG() {
        const s = MockData.adminDashboard.systemOverview;
        return `
        <div class="space-y-4">
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">🕸️ 知识图谱管理</div>
                <div class="grid grid-cols-2 gap-3">
                    <div class="p-4 bg-blue-50 rounded-xl text-center">
                        <div class="text-3xl font-bold text-blue-600">${s.totalKnowledgePoints}</div>
                        <div class="text-sm text-gray-600">知识点</div>
                    </div>
                    <div class="p-4 bg-purple-50 rounded-xl text-center">
                        <div class="text-3xl font-bold text-purple-600">101</div>
                        <div class="text-sm text-gray-600">知识点关系</div>
                    </div>
                    <div class="p-4 bg-green-50 rounded-xl text-center">
                        <div class="text-3xl font-bold text-green-600">1257</div>
                        <div class="text-sm text-gray-600">题目</div>
                    </div>
                    <div class="p-4 bg-orange-50 rounded-xl text-center">
                        <div class="text-3xl font-bold text-orange-600">76</div>
                        <div class="text-sm text-gray-600">错误原因</div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">📋 知识点操作</div>
                <div class="grid grid-cols-2 gap-2">
                    <button onclick="AdminPage.addKnowledge()" class="p-3 bg-blue-50 rounded-xl text-sm font-medium">
                        ➕ 添加知识点
                    </button>
                    <button onclick="AdminPage.addRelation()" class="p-3 bg-purple-50 rounded-xl text-sm font-medium">
                        🔗 添加关系
                    </button>
                    <button onclick="AdminPage.importData()" class="p-3 bg-green-50 rounded-xl text-sm font-medium">
                        📥 批量导入
                    </button>
                    <button onclick="AdminPage.exportData()" class="p-3 bg-orange-50 rounded-xl text-sm font-medium">
                        📤 导出数据
                    </button>
                </div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">🔍 数据浏览</div>
                <div class="space-y-2">
                    <button onclick="AdminPage.browseKnowledge()" class="w-full p-3 border rounded-xl text-left flex items-center justify-between">
                        <span>📚 浏览所有知识点</span>
                        <span class="text-gray-400">→</span>
                    </button>
                    <button onclick="AdminPage.browseQuestions()" class="w-full p-3 border rounded-xl text-left flex items-center justify-between">
                        <span>❓ 浏览所有题目</span>
                        <span class="text-gray-400">→</span>
                    </button>
                    <button onclick="AdminPage.browseRelations()" class="w-full p-3 border rounded-xl text-left flex items-center justify-between">
                        <span>🔗 浏览知识点关系</span>
                        <span class="text-gray-400">→</span>
                    </button>
                </div>
            </div>
            
            <div class="bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-2xl p-4">
                <div class="font-bold">🔗 API对接状态</div>
                <div class="text-sm opacity-90 mt-1">
                    DataHub数据分析Agent已接入知识图谱
                </div>
                <div class="text-xs opacity-80 mt-2">
                    已实现: 学习路径推荐、知识点查询、错题分析
                </div>
                <div class="text-xs opacity-80">
                    待接入: 复习计划生成、错因深度分析
                </div>
            </div>
        </div>`;
    },
    
    addKnowledge() {
        alert('添加知识点\n\n可以：\n1. 手动输入\n2. AI自动提取\n3. 从现有知识点扩展\n\n（需对接知识图谱管理模块）');
    },
    
    addRelation() {
        alert('添加知识点关系\n\n支持的关系类型：\n• 前置基础\n• 递进拓展\n• 应用支撑\n• 易混辨析\n\n（需对接知识图谱管理模块）');
    },
    
    importData() {
        alert('批量导入数据\n\n支持格式：\n• CSV文件\n• Excel文件\n• JSON格式\n\n（需对接数据导入模块）');
    },
    
    exportData() {
        alert('导出数据\n\n可以导出：\n• 知识点列表\n• 题目列表\n• 关系图数据\n• 统计报表\n\n（需对接数据导出模块）');
    },
    
    browseKnowledge() {
        alert('浏览所有知识点\n\n共255个知识点，覆盖1-6年级\n\n（需对接知识图谱浏览模块）');
    },
    
    browseQuestions() {
        alert('浏览所有题目\n\n共1257道题目\n\n（需对接题库浏览模块）');
    },
    
    browseRelations() {
        alert('浏览知识点关系\n\n共101条关系\n类型包括：前置基础、递进拓展、应用支撑等\n\n（需对接关系浏览模块）');
    },
    
    renderUsers() {
        const u = MockData.adminDashboard.userManagement;
        return `
        <div class="space-y-4">
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="flex items-center justify-between mb-3">
                    <div class="font-bold">👥 用户管理</div>
                    <div class="flex gap-2">
                        <button class="text-xs bg-blue-50 text-blue-600 px-3 py-1 rounded">学生</button>
                        <button class="text-xs bg-gray-100 px-3 py-1 rounded">教师</button>
                    </div>
                </div>
                
                <div class="space-y-2">
                    ${u.students.map(s => `
                        <div class="p-3 border rounded-xl">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-3">
                                    <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                                        👨‍🎓
                                    </div>
                                    <div>
                                        <div class="font-medium">${s.name}</div>
                                        <div class="text-xs text-gray-500">${s.id} · ${s.class}</div>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="badge ${s.status === '活跃' ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-500'}">
                                        ${s.status}
                                    </div>
                                    <div class="text-xs text-gray-400 mt-1">${s.lastLogin}</div>
                                </div>
                            </div>
                            <div class="flex gap-2 mt-2">
                                <button onclick="AdminPage.viewStudent('${s.id}')" class="text-xs bg-gray-100 px-2 py-1 rounded">查看详情</button>
                                <button onclick="AdminPage.resetPassword('${s.id}')" class="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded">重置密码</button>
                                ${s.status === '活跃' 
                                    ? `<button onclick="AdminPage.freezeUser('${s.id}')" class="text-xs bg-red-50 text-red-600 px-2 py-1 rounded">冻结</button>`
                                    : `<button onclick="AdminPage.activateUser('${s.id}')" class="text-xs bg-green-50 text-green-600 px-2 py-1 rounded">激活</button>`
                                }
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">👩‍🏫 教师管理</div>
                <div class="space-y-2">
                    ${u.teachers.map(t => `
                        <div class="p-3 border rounded-xl">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-3">
                                    <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                                        👩‍🏫
                                    </div>
                                    <div>
                                        <div class="font-medium">${t.name}</div>
                                        <div class="text-xs text-gray-500">${t.id} · ${t.subject} · 管理${t.classes}个班级</div>
                                    </div>
                                </div>
                                <div class="badge ${t.status === '活跃' ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-500'}">
                                    ${t.status}
                                </div>
                            </div>
                            <div class="flex gap-2 mt-2">
                                <button onclick="AdminPage.viewTeacher('${t.id}')" class="text-xs bg-gray-100 px-2 py-1 rounded">查看详情</button>
                                <button onclick="AdminPage.editTeacher('${t.id}')" class="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded">编辑</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>`;
    },
    
    viewStudent(id) {
        alert(`查看学生 ${id} 详情\n\n将展示：\n1. 基本信息\n2. 学习记录\n3. 错题历史\n4. 掌握度变化\n5. 登录日志\n\n（需对接用户管理模块）`);
    },
    
    resetPassword(id) {
        if (confirm(`确定重置用户 ${id} 的密码吗？`)) {
            alert('密码已重置为默认密码');
        }
    },
    
    freezeUser(id) {
        if (confirm(`确定冻结用户 ${id} 的账号吗？`)) {
            alert('账号已冻结');
        }
    },
    
    activateUser(id) {
        alert(`已激活用户 ${id} 的账号`);
    },
    
    viewTeacher(id) {
        alert(`查看教师 ${id} 详情\n\n将展示：\n1. 基本信息\n2. 管理的班级\n3. 布置的作业\n4. 批改记录\n\n（需对接用户管理模块）`);
    },
    
    editTeacher(id) {
        alert(`编辑教师 ${id}\n\n（需对接用户管理模块）`);
    }
};
