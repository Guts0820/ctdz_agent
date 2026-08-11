const LoginPage = {
    render() {
        return `
        <div class="min-h-screen flex items-center justify-center p-4" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div class="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden">
                <div class="p-8 text-center" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    <div class="text-5xl mb-4">📚</div>
                    <h1 class="text-2xl font-bold text-white">小学生数学知识图谱</h1>
                    <p class="text-white/80 mt-2">智能学习系统</p>
                </div>
                
                <div class="p-6">
                    <div class="mb-6">
                        <label class="block text-sm font-medium text-gray-700 mb-2">选择角色</label>
                        <div class="grid grid-cols-3 gap-2">
                            <button onclick="LoginPage.selectRole('student')" id="role-student" class="role-select-btn p-4 rounded-xl border-2 border-gray-200 hover:border-purple-500 transition flex flex-col items-center">
                                <span class="text-3xl mb-1">🎒</span>
                                <span class="text-sm">学生</span>
                            </button>
                            <button onclick="LoginPage.selectRole('teacher')" id="role-teacher" class="role-select-btn p-4 rounded-xl border-2 border-gray-200 hover:border-purple-500 transition flex flex-col items-center">
                                <span class="text-3xl mb-1">👩‍🏫</span>
                                <span class="text-sm">教师</span>
                            </button>
                            <button onclick="LoginPage.selectRole('admin')" id="role-admin" class="role-select-btn p-4 rounded-xl border-2 border-gray-200 hover:border-purple-500 transition flex flex-col items-center">
                                <span class="text-3xl mb-1">⚙️</span>
                                <span class="text-sm">管理员</span>
                            </button>
                        </div>
                    </div>
                    
                    <div id="account-section" class="hidden">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">选择账号</label>
                            <select id="account-select" class="w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
                                <option value="">请选择账号</option>
                            </select>
                        </div>
                        
                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
                            <input type="password" id="password-input" placeholder="请输入密码" 
                                class="w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
                            <p id="password-hint" class="text-xs text-gray-500 mt-1">学生/教师密码: 123456，管理员密码: admin123</p>
                        </div>
                        
                        <button onclick="LoginPage.login()" class="w-full gradient-primary text-white font-bold py-3 rounded-xl hover:opacity-90 transition">
                            登 录
                        </button>
                        
                        <p id="login-error" class="text-red-500 text-sm text-center mt-2 hidden">账号或密码错误</p>
                    </div>
                </div>
                
                <div class="px-6 pb-6">
                    <div class="bg-gray-50 rounded-xl p-4">
                        <div class="text-xs text-gray-500 mb-2">💡 测试账号</div>
                        <div class="text-xs text-gray-600 space-y-1">
                            <div>学生: S001~S008, 密码: 123456</div>
                            <div>教师: T001~T003, 密码: 123456</div>
                            <div>管理员: A001~A002, 密码: admin123</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;
    },
    
    selectedRole: null,
    
    selectRole(role) {
        this.selectedRole = role;
        
        document.querySelectorAll('.role-select-btn').forEach(btn => {
            btn.classList.remove('border-purple-500', 'bg-purple-50');
            btn.classList.add('border-gray-200');
        });
        const selectedBtn = document.getElementById(`role-${role}`);
        selectedBtn.classList.remove('border-gray-200');
        selectedBtn.classList.add('border-purple-500', 'bg-purple-50');
        
        const accountSection = document.getElementById('account-section');
        accountSection.classList.remove('hidden');
        
        const accountSelect = document.getElementById('account-select');
        accountSelect.innerHTML = '<option value="">请选择账号</option>';
        
        let accounts = [];
        if (role === 'student') {
            accounts = MockData.users.students.map(s => ({
                id: s.id, name: `${s.name} (${s.class})`, avatar: s.avatar
            }));
        } else if (role === 'teacher') {
            accounts = MockData.users.teachers.map(t => ({
                id: t.id, name: `${t.name} (${t.classes.join('、')})`, avatar: t.avatar
            }));
        } else if (role === 'admin') {
            accounts = MockData.users.admins.map(a => ({
                id: a.id, name: a.name, avatar: a.avatar
            }));
        }
        
        accounts.forEach(acc => {
            const option = document.createElement('option');
            option.value = acc.id;
            option.textContent = `${acc.avatar} ${acc.name}`;
            accountSelect.appendChild(option);
        });
        
        document.getElementById('login-error').classList.add('hidden');
    },
    
    login() {
        const accountId = document.getElementById('account-select').value;
        const password = document.getElementById('password-input').value;
        
        if (!accountId || !password) {
            this.showError('请选择账号并输入密码');
            return;
        }
        
        let user = null;
        if (this.selectedRole === 'student') {
            user = MockData.users.students.find(s => s.id === accountId && s.password === password);
        } else if (this.selectedRole === 'teacher') {
            user = MockData.users.teachers.find(t => t.id === accountId && t.password === password);
        } else if (this.selectedRole === 'admin') {
            user = MockData.users.admins.find(a => a.id === accountId && a.password === password);
        }
        
        if (user) {
            MockData.currentUser = { ...user, role: this.selectedRole };
            if (this.selectedRole === 'teacher' && user.classIds && user.classIds.length > 0) {
                MockData.currentClass = user.classIds[0];
            }
            App.loginSuccess(this.selectedRole);
        } else {
            this.showError('账号或密码错误');
        }
    },
    
    showError(msg) {
        const errorEl = document.getElementById('login-error');
        errorEl.textContent = msg;
        errorEl.classList.remove('hidden');
    }
};