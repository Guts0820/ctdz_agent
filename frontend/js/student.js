const StudentPage = {
    render() {
        return `
        <div class="min-h-screen pb-20">
            ${this.renderHeader()}
            <div class="p-4">
                <div id="student-content"></div>
            </div>
            ${this.renderBottomNav()}
        </div>`;
    },
    
    renderHeader() {
        const user = MockData.currentUser;
        return `
        <div class="gradient-primary text-white p-4 rounded-b-3xl shadow-lg">
            <div class="flex items-center justify-between">
                <div>
                    <div class="text-sm opacity-80">欢迎回来</div>
                    <div class="text-xl font-bold">${user.name}</div>
                    <div class="text-sm opacity-80">${user.grade}年级 · ${user.class}</div>
                </div>
                <div class="relative">
                    <button onclick="StudentPage.toggleUserMenu()" class="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center text-2xl hover:bg-white/30 transition">
                        ${user.avatar}
                    </button>
                    <div id="user-menu" class="hidden absolute right-0 top-full mt-2 bg-white rounded-xl shadow-lg border py-2 w-48 z-50">
                        <div class="px-4 py-2 border-b">
                            <div class="text-sm font-medium text-gray-800">${user.name}</div>
                            <div class="text-xs text-gray-500">${user.id}</div>
                        </div>
                        <button onclick="StudentPage.showAccountInfo()" class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2">
                            👤 账号信息
                        </button>
                        <button onclick="StudentPage.showSettings()" class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2">
                            ⚙️ 设置
                        </button>
                        <div class="border-t my-1"></div>
                        <button onclick="App.logout()" class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2">
                            🚪 退出登录
                        </button>
                    </div>
                </div>
            </div>
            <div class="mt-4 grid grid-cols-4 gap-2 text-center text-sm">
                <div class="bg-white/20 rounded-lg p-2">
                    <div class="font-bold text-lg">${MockData.studentStats.totalQuestions}</div>
                    <div class="text-xs opacity-80">总题数</div>
                </div>
                <div class="bg-white/20 rounded-lg p-2">
                    <div class="font-bold text-lg">${MockData.studentStats.correctRate}%</div>
                    <div class="text-xs opacity-80">正确率</div>
                </div>
                <div class="bg-white/20 rounded-lg p-2">
                    <div class="font-bold text-lg">${MockData.studentStats.totalMistakes}</div>
                    <div class="text-xs opacity-80">错题数</div>
                </div>
                <div class="bg-white/20 rounded-lg p-2">
                    <div class="font-bold text-lg">${MockData.studentStats.reviewedMistakes}</div>
                    <div class="text-xs opacity-80">已订正</div>
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
                    <span class="text-gray-600">班级</span>
                    <span class="font-medium">${user.class}</span>
                </div>
                <div class="flex justify-between p-2 bg-gray-50 rounded-lg">
                    <span class="text-gray-600">年级</span>
                    <span class="font-medium">${user.grade}年级</span>
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

    renderBottomNav() {
        return `
        <div class="fixed bottom-0 left-0 right-0 bg-white shadow-lg border-t">
            <div class="flex justify-around py-2">
                <button onclick="StudentPage.navigate('home')" id="nav-home" class="nav-btn flex flex-col items-center px-3 py-2 rounded-lg transition">
                    <span class="text-2xl">🏠</span>
                    <span class="text-xs mt-1">首页</span>
                </button>
                <button onclick="StudentPage.navigate('camera')" id="nav-camera" class="nav-btn flex flex-col items-center px-3 py-2 rounded-lg transition">
                    <span class="text-2xl">📷</span>
                    <span class="text-xs mt-1">拍照</span>
                </button>
                <button onclick="StudentPage.navigate('mistakes')" id="nav-mistakes" class="nav-btn flex flex-col items-center px-3 py-2 rounded-lg transition">
                    <span class="text-2xl">📝</span>
                    <span class="text-xs mt-1">错题本</span>
                </button>
                <button onclick="StudentPage.navigate('path')" id="nav-path" class="nav-btn flex flex-col items-center px-3 py-2 rounded-lg transition">
                    <span class="text-2xl">🛤️</span>
                    <span class="text-xs mt-1">学习路径</span>
                </button>
                <button onclick="StudentPage.navigate('report')" id="nav-report" class="nav-btn flex flex-col items-center px-3 py-2 rounded-lg transition">
                    <span class="text-2xl">📊</span>
                    <span class="text-xs mt-1">成长报告</span>
                </button>
            </div>
        </div>`;
    },
    
    navigate(page) {
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('tab-active'));
        const navMap = { home: 'nav-home', camera: 'nav-camera', mistakes: 'nav-mistakes', path: 'nav-path', report: 'nav-report' };
        const activeBtn = document.getElementById(navMap[page]);
        if (activeBtn) activeBtn.classList.add('tab-active');
        
        const content = document.getElementById('student-content');
        const renderMap = {
            home: this.renderHome,
            camera: this.renderCamera,
            mistakes: this.renderMistakes,
            path: this.renderPath,
            report: this.renderReport
        };
        content.innerHTML = renderMap[page]();
        if (page === 'report') this.initReportCharts();
        if (page === 'path') this.initPathCharts();
    },
    
    renderHome() {
        return `
        <div class="space-y-4">
            <div onclick="StudentPage.navigate('camera')" class="card-hover bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-2xl p-5 cursor-pointer shadow-soft">
                <div class="flex items-center gap-4">
                    <div class="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center text-3xl">
                        📷
                    </div>
                    <div>
                        <div class="font-bold text-lg">拍照录入作业</div>
                        <div class="text-sm opacity-90">拍下今日作业，开始学习</div>
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
                <div onclick="StudentPage.navigate('mistakes')" class="card-hover bg-white rounded-2xl p-4 cursor-pointer shadow-soft border border-gray-100">
                    <div class="text-3xl mb-2">📝</div>
                    <div class="font-bold">错题本</div>
                    <div class="text-sm text-gray-500">${MockData.studentStats.totalMistakes}道错题待复习</div>
                </div>
                <div onclick="StudentPage.navigate('path')" class="card-hover bg-white rounded-2xl p-4 cursor-pointer shadow-soft border border-gray-100">
                    <div class="text-3xl mb-2">🛤️</div>
                    <div class="font-bold">学习路径</div>
                    <div class="text-sm text-gray-500">${MockData.learningPath.length}个学习节点</div>
                </div>
                <div onclick="StudentPage.navigate('report')" class="card-hover bg-white rounded-2xl p-4 cursor-pointer shadow-soft border border-gray-100">
                    <div class="text-3xl mb-2">📊</div>
                    <div class="font-bold">成长报告</div>
                    <div class="text-sm text-gray-500">查看能力评估</div>
                </div>
                <div onclick="StudentPage.showReviewPlan()" class="card-hover bg-white rounded-2xl p-4 cursor-pointer shadow-soft border border-gray-100">
                    <div class="text-3xl mb-2">📅</div>
                    <div class="font-bold">复习计划</div>
                    <div class="text-sm text-gray-500">基于掌握度智能推荐</div>
                </div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft border border-gray-100">
                <div class="flex items-center justify-between mb-3">
                    <div class="font-bold">📚 今日推荐</div>
                    <span class="text-xs text-gray-400">基于你的学习情况</span>
                </div>
                <div class="space-y-2">
                    ${MockData.learningPath.slice(0, 3).map(item => `
                        <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                            <div class="w-8 h-8 rounded-full ${item.type === 'weak' ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'} flex items-center justify-center font-bold text-sm">
                                ${item.order}
                            </div>
                            <div class="flex-1">
                                <div class="font-medium text-sm">${item.title}</div>
                                <div class="text-xs text-gray-500">${item.type === 'weak' ? '薄弱知识点' : '复习'} · ${item.estimated_time}</div>
                            </div>
                            <span class="badge ${item.type === 'weak' ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}">
                                ${item.mastery_level}%
                            </span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>`;
    },
    
    renderCamera() {
        return `
        <div class="space-y-4">
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3 text-lg">📷 拍照录入作业</div>
                <div class="text-sm text-gray-500 mb-4">拍下今日的数学作业照片，系统将自动识别题目</div>
                
                <div class="camera-frame h-64 flex items-center justify-center mb-4 bg-gray-50">
                    <div class="text-center text-gray-400">
                        <div class="text-5xl mb-2">📸</div>
                        <div>点击拍照</div>
                        <div class="text-xs mt-1">或从相册选择</div>
                    </div>
                </div>
                
                <div class="flex gap-3">
                    <button onclick="StudentPage.takePhoto()" class="flex-1 bg-purple-600 text-white rounded-xl py-3 font-medium">
                        📸 拍照
                    </button>
                    <button onclick="StudentPage.selectImage()" class="flex-1 bg-gray-100 text-gray-700 rounded-xl py-3 font-medium">
                        🖼️ 相册
                    </button>
                </div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">📋 订正流程说明</div>
                <div class="space-y-3">
                    <div class="flex items-start gap-3">
                        <div class="w-8 h-8 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">1</div>
                        <div>
                            <div class="font-medium text-sm">拍照录入</div>
                            <div class="text-xs text-gray-500">系统自动识别题目内容</div>
                        </div>
                    </div>
                    <div class="flex items-start gap-3">
                        <div class="w-8 h-8 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">2</div>
                        <div>
                            <div class="font-medium text-sm">智能批改</div>
                            <div class="text-xs text-gray-500">自动判对错，标记错题</div>
                        </div>
                    </div>
                    <div class="flex items-start gap-3">
                        <div class="w-8 h-8 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">3</div>
                        <div>
                            <div class="font-medium text-sm">错因分析</div>
                            <div class="text-xs text-gray-500">告知错误原因（预留接口）</div>
                        </div>
                    </div>
                    <div class="flex items-start gap-3">
                        <div class="w-8 h-8 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">4</div>
                        <div>
                            <div class="font-medium text-sm">订正重做</div>
                            <div class="text-xs text-gray-500">做错继续订正，做对进入错题本</div>
                        </div>
                    </div>
                    <div class="flex items-start gap-3">
                        <div class="w-8 h-8 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">5</div>
                        <div>
                            <div class="font-medium text-sm">计入错题本</div>
                            <div class="text-xs text-gray-500">错题自动加入复习计划</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div onclick="StudentPage.showMockResult()" class="bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-2xl p-4 cursor-pointer shadow-soft">
                <div class="font-bold">🎯 体验拍照录入（演示）</div>
                <div class="text-sm opacity-90">查看系统识别和批改示例</div>
            </div>
        </div>`;
    },
    
    takePhoto() {
        this.showMockResult();
    },
    
    selectImage() {
        this.showMockResult();
    },
    
    showMockResult() {
        const result = `
        <div class="bg-white rounded-2xl p-4 shadow-soft">
            <div class="flex items-center gap-2 mb-3">
                <span class="badge bg-green-100 text-green-600">✓ 识别成功</span>
                <span class="text-sm text-gray-500">识别出 3 道题目</span>
            </div>
            
            <div class="space-y-3">
                <div class="p-3 border border-gray-200 rounded-xl">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-medium text-sm">第1题</span>
                        <span class="badge bg-green-100 text-green-600">✓ 正确</span>
                    </div>
                    <div class="text-sm mb-2">6 + 7 + 6 = ?</div>
                    <div class="text-xs text-gray-500">你的答案: 19 ✓ 正确答案: 19</div>
                </div>
                
                <div class="p-3 border border-red-200 bg-red-50 rounded-xl">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-medium text-sm">第2题</span>
                        <span class="badge bg-red-100 text-red-600">✗ 错误</span>
                    </div>
                    <div class="text-sm mb-2">9 + 4 + 5 = ?</div>
                    <div class="text-xs mb-1">你的答案: 17 ✗ 正确答案: 18</div>
                    <div class="text-xs text-orange-600">⚠️ 错因分析：20以内加减法不熟练</div>
                    <button onclick="StudentPage.doCorrection()" class="mt-2 bg-red-500 text-white text-sm px-3 py-1 rounded-lg">立即订正</button>
                </div>
                
                <div class="p-3 border border-green-200 rounded-xl">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-medium text-sm">第3题</span>
                        <span class="badge bg-green-100 text-green-600">✓ 正确</span>
                    </div>
                    <div class="text-sm mb-2">12 - 5 + 8 = ?</div>
                    <div class="text-xs text-gray-500">你的答案: 15 ✓ 正确答案: 15</div>
                </div>
            </div>
            
            <div class="mt-4 p-3 bg-yellow-50 rounded-xl">
                <div class="text-sm font-medium text-yellow-800">📊 本次作业统计</div>
                <div class="text-xs text-yellow-600 mt-1">正确率: 67% | 新增错题: 1 道</div>
            </div>
            
            <button onclick="StudentPage.navigate('mistakes')" class="w-full mt-4 bg-purple-600 text-white rounded-xl py-3 font-medium">
                查看错题本 →
            </button>
        </div>`;
        
        const content = document.getElementById('student-content');
        const existingDiv = document.createElement('div');
        existingDiv.className = 'fixed inset-0 bg-black/50 z-50 flex items-end';
        existingDiv.innerHTML = `
            <div class="bg-white w-full max-h-[80vh] rounded-t-3xl overflow-auto">
                <div class="sticky top-0 bg-white p-4 border-b">
                    <div class="font-bold text-lg">📷 作业识别结果</div>
                </div>
                <div class="p-4">${result}</div>
                <button onclick="this.closest('.fixed').remove()" class="w-full bg-gray-100 py-3 rounded-xl mb-4">关闭</button>
            </div>
        `;
        document.body.appendChild(existingDiv);
    },
    
    doCorrection() {
        const correctionDiv = document.createElement('div');
        correctionDiv.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4';
        correctionDiv.innerHTML = `
            <div class="bg-white rounded-2xl p-5 w-full max-w-sm">
                <div class="text-center mb-4">
                    <div class="text-4xl mb-2">✏️</div>
                    <div class="font-bold text-lg">订正练习</div>
                    <div class="text-sm text-gray-500">下面的题目做对了吗？</div>
                </div>
                <div class="p-4 bg-gray-50 rounded-xl mb-4">
                    <div class="font-medium">9 + 4 + 5 = ?</div>
                </div>
                <input id="correction-answer" type="text" placeholder="输入你的答案" class="w-full border rounded-xl px-4 py-3 mb-4 text-center text-lg">
                <button onclick="StudentPage.checkCorrection()" class="w-full bg-purple-600 text-white rounded-xl py-3 font-medium">提交答案</button>
                <button onclick="this.closest('.fixed').remove()" class="w-full mt-2 text-gray-500 py-2">取消</button>
            </div>
        `;
        document.body.appendChild(correctionDiv);
    },
    
    checkCorrection() {
        const answer = document.getElementById('correction-answer').value;
        if (answer.trim() === '18') {
            alert('✅ 回答正确！已计入错题本，将加入复习计划');
            document.querySelectorAll('.fixed').forEach(el => el.remove());
        } else {
            alert('❌ 回答错误，请再试一次');
        }
    },
    
    showReviewPlan() {
        const user = MockData.currentUser;
        if (!user) return;
        const studentId = user.id;

        const planDiv = document.createElement('div');
        planDiv.className = 'fixed inset-0 bg-black/50 z-50 flex items-end';
        planDiv.id = 'review-plan-modal';
        planDiv.innerHTML = `
            <div class="bg-white w-full max-h-[85vh] rounded-t-3xl overflow-auto">
                <div class="sticky top-0 bg-white p-4 border-b flex items-center justify-between">
                    <div class="font-bold text-lg">📅 我的复习计划</div>
                    <button onclick="document.getElementById('review-plan-modal').remove()" class="text-gray-400 hover:text-gray-600">✕</button>
                </div>
                <div class="p-4">
                    <div id="review-plan-content">
                        <div class="text-center py-8">
                            <div class="text-4xl mb-3">📊</div>
                            <div class="font-medium mb-2">准备生成复习计划</div>
                            <div class="text-sm text-gray-500">基于你的知识图谱掌握度数据</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(planDiv);
        this.loadReviewPlans(studentId);
    },

    async loadReviewPlans(studentId) {
        const content = document.getElementById('review-plan-content');
        if (!content) return;

        content.innerHTML = `
            <div class="space-y-3">
                <div onclick="StudentPage.generateNewPlan('${studentId}')" class="card-hover gradient-primary text-white rounded-2xl p-4 cursor-pointer shadow-soft">
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center text-2xl">✨</div>
                        <div>
                            <div class="font-bold">生成今日复习计划</div>
                            <div class="text-sm opacity-90">基于你的掌握度智能推荐题目</div>
                        </div>
                    </div>
                </div>
                <div class="text-xs text-gray-500 text-center mt-4">
                    💡 系统会根据你在知识图谱中的掌握度数据，为你生成个性化复习计划
                </div>
            </div>
        `;
    },

    async generateNewPlan(studentId) {
        const content = document.getElementById('review-plan-content');
        if (!content) return;

        content.innerHTML = `
            <div class="space-y-3">
                <div class="p-4 bg-purple-50 border border-purple-200 rounded-xl">
                    <div class="font-medium text-sm mb-3">📝 设置复习计划</div>
                    <div class="text-xs text-gray-600 mb-3">请选择题目数量（1-30题）</div>
                    <div class="grid grid-cols-5 gap-2 mb-3" id="plan-count-options">
                        ${[5, 10, 15, 20, 25].map(n => `
                            <button class="plan-count-btn py-2 rounded-lg text-sm border ${n === 10 ? 'bg-purple-600 text-white border-purple-600' : 'bg-white border-gray-200 text-gray-700'}" data-count="${n}">${n}</button>
                        `).join('')}
                    </div>
                    <div class="flex gap-2">
                        <button id="confirm-plan-btn" class="flex-1 bg-purple-600 text-white py-2 rounded-xl text-sm font-medium">
                            生成计划 (10题)
                        </button>
                        <button onclick="StudentPage.loadReviewPlans('${studentId}')" class="px-4 bg-gray-100 text-gray-600 py-2 rounded-xl text-sm">
                            取消
                        </button>
                    </div>
                </div>
            </div>
        `;

        let selectedCount = 10;
        const countBtns = content.querySelectorAll('.plan-count-btn');
        const confirmBtn = document.getElementById('confirm-plan-btn');
        
        countBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                selectedCount = parseInt(btn.dataset.count);
                countBtns.forEach(b => {
                    b.classList.remove('bg-purple-600', 'text-white', 'border-purple-600');
                    b.classList.add('bg-white', 'border-gray-200', 'text-gray-700');
                });
                btn.classList.remove('bg-white', 'border-gray-200', 'text-gray-700');
                btn.classList.add('bg-purple-600', 'text-white', 'border-purple-600');
                confirmBtn.textContent = `生成计划 (${selectedCount}题)`;
            });
        });

        const doGenerate = async () => {
            content.innerHTML = `
                <div class="text-center py-8">
                    <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                    <div class="text-sm text-gray-600">正在计算优先级并生成计划...</div>
                    <div class="text-xs text-gray-400 mt-1">请稍候</div>
                </div>
            `;

            try {
                const plan = await Api.createReviewPlan(studentId, 'question_count', selectedCount);

                content.innerHTML = `
                    <div class="space-y-3">
                        <div class="p-4 bg-green-50 border border-green-200 rounded-xl">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="text-2xl">🎉</span>
                                <span class="font-bold text-green-700">复习计划已生成！</span>
                            </div>
                            <div class="text-sm text-gray-600">
                                共 ${plan.items ? plan.items.length : 0} 道题目
                            </div>
                        </div>
                        ${plan.items && plan.items.length > 0 ? `
                            <div class="bg-white rounded-xl p-3 border">
                                <div class="font-medium text-sm mb-2">📝 推荐题目</div>
                                <div class="space-y-2 max-h-60 overflow-auto">
                                    ${plan.items.map((item, i) => `
                                        <div class="flex items-center gap-2 p-2 bg-gray-50 rounded-lg text-sm">
                                            <span class="w-6 h-6 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">${i + 1}</span>
                                            <div class="flex-1 min-w-0">
                                                <div class="truncate">题目 ${item.question_id}</div>
                                                <div class="text-xs text-gray-500">知识点: ${(item.knowledge_point_ids || []).slice(0, 3).join(', ')}${(item.knowledge_point_ids || []).length > 3 ? '...' : ''}</div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        <button onclick="StudentPage.startReviewPractice('${plan.id}', '${studentId}')" class="w-full gradient-primary text-white py-3 rounded-xl font-medium">
                            🚀 开始练习
                        </button>
                        <button onclick="StudentPage.loadReviewPlans('${studentId}')" class="w-full bg-gray-100 text-gray-600 py-2 rounded-xl text-sm">
                            重新生成
                        </button>
                    </div>
                `;
            } catch (error) {
                console.error('Failed to generate plan:', error);
                content.innerHTML = `
                    <div class="text-center py-8">
                        <div class="text-4xl mb-3">❌</div>
                        <div class="font-medium mb-1">生成失败</div>
                        <div class="text-sm text-gray-500 mb-4">${error.message || '请检查后端服务是否启动'}</div>
                        <button onclick="StudentPage.loadReviewPlans('${studentId}')" class="bg-gray-100 text-gray-600 px-4 py-2 rounded-xl text-sm">重试</button>
                    </div>
                `;
            }
        };

        confirmBtn.addEventListener('click', doGenerate);
    },

    async startReviewPractice(planId, studentId) {
        const content = document.getElementById('review-plan-content');
        if (!content) return;

        content.innerHTML = `
            <div class="text-center py-8">
                <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                <div class="text-sm text-gray-600">正在启动练习会话...</div>
            </div>
        `;

        try {
            const session = await Api.startReviewSession(planId);
            this.currentSession = session;
            this.showPracticeUI(session, planId, studentId);
        } catch (error) {
            console.error('Failed to start session:', error);
            content.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl mb-3">❌</div>
                    <div class="font-medium mb-1">启动失败</div>
                    <div class="text-sm text-gray-500 mb-4">${error.message || '请检查后端服务'}</div>
                    <button onclick="StudentPage.loadReviewPlans('${studentId}')" class="bg-gray-100 text-gray-600 px-4 py-2 rounded-xl text-sm">返回</button>
                </div>
            `;
        }
    },

    showPracticeUI(session, planId, studentId) {
        const content = document.getElementById('review-plan-content');
        if (!content) return;

        const currentQ = session.current_question;
        const options = currentQ && currentQ.options ? currentQ.options : ['A', 'B', 'C', 'D'];

        content.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center justify-between">
                    <div class="font-bold">✏️ 练习中</div>
                    <div class="text-sm text-gray-500">剩余 ${session.remaining_items_count || 0} 题</div>
                </div>
                <div class="bg-white rounded-xl p-4 border">
                    <div class="text-xs text-gray-500 mb-2">题目 ${currentQ ? currentQ.id : '加载中'}</div>
                    <div class="font-medium mb-4">${currentQ ? (currentQ.prompt || '题目内容加载中...') : '加载中...'}</div>
                    <div class="space-y-2">
                        ${options.map((opt, i) => `
                            <label class="quiz-option-label flex items-center gap-3 p-3 border rounded-xl cursor-pointer hover:bg-gray-50 transition" data-idx="${i}">
                                <input type="radio" name="quiz-option" value="${i}" class="w-4 h-4 quiz-radio">
                                <span class="text-sm">${opt}</span>
                            </label>
                        `).join('')}
                    </div>
                    <button id="submit-answer-btn" class="w-full mt-4 bg-purple-600 text-white py-2.5 rounded-xl text-sm font-medium">
                        提交答案
                    </button>
                </div>
                <button onclick="StudentPage.pauseAndExit('${session.session_id}')" class="w-full bg-gray-100 text-gray-600 py-2 rounded-xl text-sm">
                    退出练习
                </button>
            </div>
        `;

        this._selectedOption = null;
        this._quizRadios = content.querySelectorAll('.quiz-radio');
        this._quizLabels = content.querySelectorAll('.quiz-option-label');

        this._quizRadios.forEach((radio, idx) => {
            radio.addEventListener('change', () => {
                this._selectedOption = idx;
                this._quizLabels.forEach(l => {
                    l.classList.remove('border-purple-500', 'bg-purple-50');
                });
                this._quizLabels[idx].classList.add('border-purple-500', 'bg-purple-50');
            });
        });

        const submitBtn = document.getElementById('submit-answer-btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                if (this._selectedOption === null) {
                    alert('请先选择一个选项');
                    return;
                }
                this.submitAnswer(session.session_id, currentQ.id, planId, studentId);
            });
        }
    },

    async submitAnswer(sessionId, questionId, planId, studentId) {
        const btn = document.getElementById('submit-answer-btn');
        btn.disabled = true;
        btn.textContent = '提交中...';

        try {
            const result = await Api.submitAttempt(sessionId, questionId, this._selectedOption, 30);

            const isCorrect = result.is_correct;
            const correctIdx = result.correct_option ?? 0;
            const correctLabel = String.fromCharCode(65 + correctIdx);

            let feedbackHtml = '';
            if (isCorrect) {
                feedbackHtml = `
                    <div class="p-4 bg-green-50 border border-green-200 rounded-xl text-center">
                        <div class="text-3xl mb-2">✅</div>
                        <div class="font-bold text-green-700">回答正确！</div>
                        <button onclick="StudentPage.nextQuestion('${sessionId}', ${result.session_completed}, '${planId}', '${studentId}')" class="w-full mt-4 bg-purple-600 text-white py-2 rounded-xl text-sm">
                            ${result.session_completed ? '查看结果 →' : '下一题 →'}
                        </button>
                    </div>
                `;
            } else {
                feedbackHtml = `
                    <div class="p-4 bg-red-50 border border-red-200 rounded-xl text-center">
                        <div class="text-3xl mb-2">❌</div>
                        <div class="font-bold text-red-700">回答错误</div>
                        <div class="text-sm text-gray-500 mt-1 mb-3">正确答案是 ${correctLabel}</div>
                        <button onclick="StudentPage.showCorrectionModal('${result.attempt_id}', ${correctIdx}, '${sessionId}', '${planId}', '${studentId}')" class="w-full bg-orange-500 text-white py-2 rounded-xl text-sm mb-2">
                            ✏️ 订正
                        </button>
                        <button onclick="StudentPage.nextQuestion('${sessionId}', ${result.session_completed}, '${planId}', '${studentId}')" class="w-full bg-gray-100 text-gray-600 py-2 rounded-xl text-sm">
                            跳过 →
                        </button>
                    </div>
                `;
            }

            const wrapper = document.createElement('div');
            wrapper.id = 'feedback-overlay';
            wrapper.className = 'fixed inset-0 bg-black/30 flex items-end z-50 p-4';
            wrapper.innerHTML = `
                <div class="bg-white w-full rounded-2xl p-4 max-w-sm mx-auto">
                    ${feedbackHtml}
                </div>
            `;
            document.body.appendChild(wrapper);
        } catch (error) {
            console.error('Failed to submit answer:', error);
            alert('提交失败: ' + (error.message || '请重试'));
        } finally {
            btn.disabled = false;
            btn.textContent = '提交答案';
        }
    },

    async nextQuestion(sessionId, sessionCompleted, planId, studentId) {
        const overlay = document.getElementById('feedback-overlay');
        if (overlay) overlay.remove();

        if (sessionCompleted) {
            const content = document.getElementById('review-plan-content');
            content.innerHTML = `
                <div class="text-center py-12">
                    <div class="text-6xl mb-4">🎉</div>
                    <div class="font-bold text-xl mb-2">练习完成！</div>
                    <div class="text-sm text-gray-500 mb-6">你已完成本次复习计划的所有题目</div>
                    <button onclick="document.getElementById('review-plan-modal').remove()" class="gradient-primary text-white px-6 py-2 rounded-xl">
                        返回首页
                    </button>
                </div>
            `;
            return;
        }

        try {
            const session = await Api.getReviewSession(sessionId);
            this.showPracticeUI(session, planId, studentId);
        } catch (error) {
            console.error('Failed to get session:', error);
            alert('获取下一题失败');
        }
    },

    async showCorrectionModal(attemptId, correctOption, sessionId, planId, studentId) {
        const correctLabel = String.fromCharCode(65 + correctOption);
        const note = prompt('订正说明', '正确答案是 ' + correctLabel + '，已理解');

        try {
            await Api.submitCorrection(attemptId, correctOption, note || '');

            const overlay = document.getElementById('feedback-overlay');
            if (overlay) overlay.remove();

            alert('✅ 订正成功！');
            this.nextQuestion(sessionId, false, planId, studentId);
        } catch (error) {
            alert('订正失败: ' + (error.message || '请重试'));
        }
    },

    async pauseAndExit(sessionId) {
        try {
            const result = await Api.pauseReviewSession(sessionId);
            if (confirm('会话已暂停（用时 ' + Math.floor((result.elapsed_seconds || 0) / 60) + ' 分钟）。确定退出吗？')) {
                document.getElementById('review-plan-modal').remove();
            }
        } catch (error) {
            if (confirm('确定退出练习吗？')) {
                document.getElementById('review-plan-modal').remove();
            }
        }
    },
    
    renderMistakes() {
        const uncorrected = MockData.mistakes.filter(m => m.status === '未订正');
        const corrected = MockData.mistakes.filter(m => m.status === '已订正');
        
        return `
        <div class="space-y-4">
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="flex gap-4 mb-4">
                    <div class="flex-1 text-center p-3 bg-red-50 rounded-xl">
                        <div class="text-2xl font-bold text-red-600">${uncorrected.length}</div>
                        <div class="text-xs text-red-500">待订正</div>
                    </div>
                    <div class="flex-1 text-center p-3 bg-green-50 rounded-xl">
                        <div class="text-2xl font-bold text-green-600">${corrected.length}</div>
                        <div class="text-xs text-green-500">已订正</div>
                    </div>
                </div>
            </div>
            
            ${uncorrected.length > 0 ? `
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">📝 待订正错题</div>
                <div class="space-y-3">
                    ${uncorrected.map(m => `
                        <div class="p-3 bg-red-50 rounded-xl border border-red-100">
                            <div class="flex items-start justify-between gap-2 mb-2">
                                <div class="flex-1">
                                    <div class="font-medium text-sm">${m.question_text}</div>
                                    <div class="text-xs text-gray-500 mt-1">错误类型: ${m.error_type}</div>
                                </div>
                                <span class="badge bg-red-200 text-red-700 flex-shrink-0">${m.date}</span>
                            </div>
                            <div class="grid grid-cols-2 gap-2 text-xs mb-2">
                                <div class="bg-white p-2 rounded">
                                    <span class="text-gray-500">你的答案: </span>
                                    <span class="text-red-600 font-medium">${m.student_answer}</span>
                                </div>
                                <div class="bg-white p-2 rounded">
                                    <span class="text-gray-500">正确答案: </span>
                                    <span class="text-green-600 font-medium">${m.correct_answer}</span>
                                </div>
                            </div>
                            <div class="bg-orange-50 p-2 rounded text-xs text-orange-700 mb-2">
                                💡 ${m.error_name}
                            </div>
                            <button onclick="StudentPage.doCorrection()" class="w-full bg-red-500 text-white text-sm py-2 rounded-lg">
                                立即订正
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}
            
            ${corrected.length > 0 ? `
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">✅ 已订正错题</div>
                <div class="space-y-3">
                    ${corrected.map(m => `
                        <div class="p-3 bg-gray-50 rounded-xl">
                            <div class="flex items-center justify-between gap-2 mb-1">
                                <div class="font-medium text-sm">${m.question_text}</div>
                                <span class="badge bg-green-100 text-green-600">已订正</span>
                            </div>
                            <div class="text-xs text-gray-500">${m.error_name} · ${m.date}</div>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}
        </div>`;
    },
    
    renderPath() {
        return `
        <div class="space-y-4">
            <div class="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-2xl p-4">
                <div class="font-bold text-lg">🛤️ 学习路径推荐</div>
                <div class="text-sm opacity-90 mt-1">基于知识图谱和你的掌握度生成</div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">💡 学习路径说明</div>
                <div class="text-sm text-gray-600 space-y-2">
                    <div>• 红色节点：薄弱知识点，需要重点学习</div>
                    <div>• 绿色节点：已掌握知识点，建议复习巩固</div>
                    <div>• 每个知识点都配有推荐题目和学习建议</div>
                </div>
            </div>
            
            <div class="space-y-3">
                ${MockData.learningPath.map(item => `
                    <div class="bg-white rounded-2xl p-4 shadow-soft">
                        <div class="flex items-start gap-3">
                            <div class="w-10 h-10 rounded-full ${item.type === 'weak' ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'} flex items-center justify-center font-bold flex-shrink-0">
                                ${item.order}
                            </div>
                            <div class="flex-1">
                                <div class="flex items-center justify-between">
                                    <div class="font-bold">${item.title}</div>
                                    <span class="badge ${item.type === 'weak' ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}">
                                        ${item.mastery_level}%
                                    </span>
                                </div>
                                <div class="flex gap-2 mt-1 text-xs text-gray-500">
                                    <span>⏱️ ${item.estimated_time}</span>
                                    <span>•</span>
                                    <span>${item.type === 'weak' ? '薄弱知识点' : '复习巩固'}</span>
                                </div>
                                
                                ${item.prerequisites && item.prerequisites.length > 0 ? `
                                    <div class="mt-2 text-xs bg-gray-50 p-2 rounded">
                                        <span class="text-gray-500">前置知识: </span>
                                        ${item.prerequisites.join(', ')}
                                    </div>
                                ` : ''}
                                
                                ${item.questions && item.questions.length > 0 ? `
                                    <div class="mt-3">
                                        <div class="text-xs font-medium text-gray-700 mb-1">📚 推荐题目</div>
                                        <div class="space-y-1">
                                            ${item.questions.map(q => `
                                                <div class="text-xs bg-blue-50 p-2 rounded flex items-center gap-2">
                                                    <span class="badge bg-blue-200 text-blue-700">难度${q.difficulty}</span>
                                                    <span class="text-gray-700">${q.text}</span>
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${item.suggestions && item.suggestions.length > 0 ? `
                                    <div class="mt-3">
                                        <div class="text-xs font-medium text-gray-700 mb-1">💡 学习建议</div>
                                        <div class="space-y-1">
                                            ${item.suggestions.map(s => `
                                                <div class="text-xs text-gray-600 flex items-start gap-1">
                                                    <span class="text-gray-400">•</span>
                                                    <span>${s}</span>
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                ` : ''}
                                
                                <div class="mt-3 flex gap-2">
                                    <button onclick="StudentPage.startLearning('${item.knowledge_id}')" class="flex-1 ${item.type === 'weak' ? 'bg-red-500' : 'bg-green-500'} text-white text-sm py-2 rounded-lg">
                                        开始学习
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <div class="bg-yellow-50 border border-yellow-200 rounded-2xl p-4">
                <div class="font-medium text-yellow-800 mb-2">🔗 与复习计划的对接</div>
                <div class="text-sm text-yellow-700">
                    学习路径推荐结果将传递给复习计划模块，自动生成个性化复习计划。
                </div>
                <div class="text-xs text-yellow-600 mt-2">
                    接口状态: <span class="badge bg-yellow-200 text-yellow-700">已接入</span>
                </div>
            </div>
        </div>`;
    },
    
    startLearning(knowledgeId) {
        alert(`开始学习知识点: ${knowledgeId}\n\n将展示：\n1. 知识点讲解\n2. 推荐题目\n3. 错因解析\n\n（此功能正在开发中）`);
    },
    
    renderReport() {
        return `
        <div class="space-y-4">
            <div class="gradient-primary text-white rounded-2xl p-5 shadow-soft">
                <div class="text-sm opacity-90">📊 成长报告</div>
                <div class="text-xl font-bold mt-1">${MockData.currentUser.name}的学习分析</div>
                <div class="text-sm opacity-80 mt-1">报告时间: 2026-07-27</div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">🎯 五维能力雷达</div>
                <div class="flex justify-center">
                    <canvas id="radarChart" width="300" height="300"></canvas>
                </div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">⚠️ 薄弱知识点</div>
                <div class="space-y-2">
                    ${MockData.weakKnowledge.map(k => `
                        <div class="p-3 bg-red-50 rounded-xl border border-red-100">
                            <div class="flex items-center justify-between mb-1">
                                <span class="font-medium text-sm">${k.title}</span>
                                <span class="badge bg-red-200 text-red-700">${k.mastery_level}%</span>
                            </div>
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div class="bg-red-500 h-2 rounded-full" style="width: ${k.mastery_level}%"></div>
                            </div>
                            ${k.error_causes && k.error_causes.length > 0 ? `
                                <div class="mt-2 text-xs text-orange-600">
                                    💡 常见错因: ${k.error_causes.join(', ')}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">📈 能力分布图</div>
                <canvas id="barChart" height="200"></canvas>
            </div>
            
            <div class="bg-white rounded-2xl p-4 shadow-soft">
                <div class="font-bold mb-3">💪 已掌握知识点</div>
                <div class="grid grid-cols-2 gap-2">
                    ${MockData.masteredKnowledge.map(k => `
                        <div class="p-2 bg-green-50 rounded-lg text-center">
                            <div class="text-sm font-medium">${k.title}</div>
                            <div class="text-xs text-green-600">${k.mastery_level}%</div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-2xl p-4 cursor-pointer" onclick="StudentPage.navigate('path')">
                <div class="flex items-center justify-between">
                    <div>
                        <div class="font-bold">🛤️ 查看学习路径</div>
                        <div class="text-sm opacity-90">获取专属学习建议</div>
                    </div>
                    <span class="text-2xl">→</span>
                </div>
            </div>
        </div>`;
    },
    
    initReportCharts() {
        setTimeout(() => {
            const radarCtx = document.getElementById('radarChart');
            if (radarCtx) {
                new Chart(radarCtx, {
                    type: 'radar',
                    data: {
                        labels: ['运算能力', '逻辑思维', '空间想象', '语言推理', '学习韧性'],
                        datasets: [{
                            label: '能力评分',
                            data: MockData.fiveDimensionScores.dimensions.map(d => d.score),
                            backgroundColor: 'rgba(102, 126, 234, 0.2)',
                            borderColor: 'rgba(102, 126, 234, 1)',
                            borderWidth: 2,
                            pointBackgroundColor: 'rgba(102, 126, 234, 1)'
                        }]
                    },
                    options: {
                        scales: {
                            r: {
                                beginAtZero: true,
                                max: 100
                            }
                        }
                    }
                });
            }
            
            const barCtx = document.getElementById('barChart');
            if (barCtx) {
                new Chart(barCtx, {
                    type: 'bar',
                    data: {
                        labels: MockData.fiveDimensionScores.dimensions.map(d => d.label),
                        datasets: [{
                            label: '当前水平',
                            data: MockData.fiveDimensionScores.dimensions.map(d => d.score),
                            backgroundColor: ['#f5576c', '#ffc107', '#28a745', '#17a2b8', '#6f42c1']
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        scales: { x: { beginAtZero: true, max: 100 } }
                    }
                });
            }
        }, 100);
    },
    
    initPathCharts() {}
};