const App = {
    currentRole: null,
    isLoggedIn: false,

    init() {
        if (!MockData.currentUser) {
            this.showLogin();
        } else {
            this.renderMainApp();
        }
    },

    showLogin() {
        this.isLoggedIn = false;
        document.getElementById('app').innerHTML = LoginPage.render();
    },

    loginSuccess(role) {
        this.isLoggedIn = true;
        this.currentRole = role;
        this.renderMainApp();
    },

    logout() {
        MockData.currentUser = null;
        MockData.currentClass = null;
        this.isLoggedIn = false;
        this.currentRole = null;
        this.showLogin();
    },

    renderMainApp() {
        const role = this.currentRole;
        const app = document.getElementById('app');
        app.innerHTML = '<div id="role-content"></div>';

        const content = document.getElementById('role-content');
        const renderMap = {
            student: () => {
                content.innerHTML = StudentPage.render();
                StudentPage.navigate('home');
            },
            teacher: async () => {
                content.innerHTML = TeacherPage.render();
                await TeacherPage.init();
                TeacherPage.navigate('dashboard');
            },
            admin: () => {
                content.innerHTML = AdminPage.render();
                AdminPage.navigate('overview');
            }
        };

        if (renderMap[role]) {
            renderMap[role]();
        } else {
            this.showLogin();
        }
    },

    showModal(title, content) {
        const modalHtml = `
            <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onclick="if(event.target === this) App.closeModal()">
                <div class="bg-white rounded-2xl w-full max-w-sm overflow-hidden">
                    <div class="p-4 border-b flex items-center justify-between">
                        <div class="font-bold">${title}</div>
                        <button onclick="App.closeModal()" class="text-gray-400 hover:text-gray-600">✕</button>
                    </div>
                    <div class="p-4">${content}</div>
                </div>
            </div>
        `;
        const modal = document.createElement('div');
        modal.id = 'app-modal';
        modal.innerHTML = modalHtml;
        document.body.appendChild(modal);
    },

    closeModal() {
        const modal = document.getElementById('app-modal');
        if (modal) modal.remove();
    },

    showLoading(message = '加载中...') {
        const loadingHtml = `
            <div id="app-loading" class="fixed inset-0 bg-black/30 z-50 flex items-center justify-center">
                <div class="bg-white rounded-2xl px-6 py-4 flex items-center gap-3 shadow-lg">
                    <div class="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
                    <span class="text-sm font-medium text-gray-700">${message}</span>
                </div>
            </div>
        `;
        const loading = document.createElement('div');
        loading.innerHTML = loadingHtml;
        document.body.appendChild(loading.firstElementChild);
    },

    hideLoading() {
        const loading = document.getElementById('app-loading');
        if (loading) loading.remove();
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
document.addEventListener('click', (e) => {
    const menu = document.getElementById('user-menu');
    if (menu && !menu.contains(e.target) && !e.target.closest('[onclick*="toggleUserMenu"]')) {
        menu.classList.add('hidden');
    }
});