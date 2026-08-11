const MockData = {
    users: {
        students: [
            { id: 'S001', name: '许嘉豪', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S002', name: '何浩宇', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S003', name: '萧诗涵', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👧' },
            { id: 'S004', name: '张小明', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S005', name: '刘思琪', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👧' },
            { id: 'S006', name: '陈志远', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S007', name: '王雨桐', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👧' },
            { id: 'S008', name: '赵子豪', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S009', name: '孙雅婷', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👧' },
            { id: 'S010', name: '周子墨', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S011', name: '吴欣怡', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👧' },
            { id: 'S012', name: '郑浩然', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S013', name: '冯雨萱', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👧' },
            { id: 'S014', name: '黄俊杰', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S015', name: '朱梦瑶', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👧' },
            { id: 'S016', name: '秦宇航', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S017', name: '许雅琪', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👧' },
            { id: 'S018', name: '邓子轩', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S019', name: '韩诗雨', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👧' },
            { id: 'S020', name: '唐睿泽', grade: 1, class: '一(1)班', classId: 1, password: '123456', avatar: '👦' },
            { id: 'S021', name: '蔡雨涵', grade: 1, class: '一(2)班', classId: 2, password: '123456', avatar: '👧' },
            { id: 'S022', name: '许佳怡', grade: 1, class: '一(2)班', classId: 2, password: '123456', avatar: '👧' },
            { id: 'S023', name: '李易峰', grade: 1, class: '一(2)班', classId: 2, password: '123456', avatar: '👦' },
            { id: 'S024', name: '王梓萱', grade: 1, class: '一(2)班', classId: 2, password: '123456', avatar: '👧' },
            { id: 'S025', name: '张天宇', grade: 1, class: '一(2)班', classId: 2, password: '123456', avatar: '👦' },
            { id: 'S026', name: '刘馨月', grade: 1, class: '一(2)班', classId: 2, password: '123456', avatar: '👧' },
            { id: 'S027', name: '陈俊熙', grade: 1, class: '一(2)班', classId: 2, password: '123456', avatar: '👦' },
            { id: 'S028', name: '杨语桐', grade: 1, class: '一(2)班', classId: 2, password: '123456', avatar: '👧' },
            { id: 'S029', name: '黄奕辰', grade: 1, class: '一(2)班', classId: 2, password: '123456', avatar: '👦' },
            { id: 'S030', name: '赵敏敏', grade: 1, class: '一(2)班', classId: 2, password: '123456', avatar: '👧' },
            { id: 'S031', name: '曹佳怡', grade: 1, class: '一(3)班', classId: 3, password: '123456', avatar: '👧' },
            { id: 'S032', name: '孙浩宇', grade: 1, class: '一(3)班', classId: 3, password: '123456', avatar: '👦' },
            { id: 'S033', name: '周雅琪', grade: 1, class: '一(3)班', classId: 3, password: '123456', avatar: '👧' },
            { id: 'S034', name: '吴彦祖', grade: 1, class: '一(3)班', classId: 3, password: '123456', avatar: '👦' },
            { id: 'S035', name: '郑诗涵', grade: 1, class: '一(3)班', classId: 3, password: '123456', avatar: '👧' },
            { id: 'S036', name: '冯子轩', grade: 1, class: '一(3)班', classId: 3, password: '123456', avatar: '👦' },
            { id: 'S037', name: '黄雨萱', grade: 1, class: '一(3)班', classId: 3, password: '123456', avatar: '👧' },
            { id: 'S038', name: '朱俊熙', grade: 1, class: '一(3)班', classId: 3, password: '123456', avatar: '👦' },
            { id: 'S039', name: '秦梦瑶', grade: 1, class: '一(3)班', classId: 3, password: '123456', avatar: '👧' },
            { id: 'S040', name: '许昊然', grade: 1, class: '一(3)班', classId: 3, password: '123456', avatar: '👦' },
            { id: 'S041', name: '王明轩', grade: 2, class: '二(1)班', classId: 4, password: '123456', avatar: '👦' },
            { id: 'S042', name: '李思雨', grade: 2, class: '二(1)班', classId: 4, password: '123456', avatar: '👧' },
            { id: 'S043', name: '张子涵', grade: 2, class: '二(1)班', classId: 4, password: '123456', avatar: '👦' },
            { id: 'S044', name: '刘梓萱', grade: 2, class: '二(1)班', classId: 4, password: '123456', avatar: '👧' },
            { id: 'S045', name: '陈志豪', grade: 2, class: '二(1)班', classId: 4, password: '123456', avatar: '👦' },
            { id: 'S046', name: '杨思琪', grade: 2, class: '二(1)班', classId: 4, password: '123456', avatar: '👧' },
            { id: 'S047', name: '赵天翊', grade: 2, class: '二(1)班', classId: 4, password: '123456', avatar: '👦' },
            { id: 'S048', name: '孙雨桐', grade: 2, class: '二(1)班', classId: 4, password: '123456', avatar: '👧' },
            { id: 'S049', name: '周俊杰', grade: 2, class: '二(1)班', classId: 4, password: '123456', avatar: '👦' },
            { id: 'S050', name: '吴欣瑶', grade: 2, class: '二(1)班', classId: 4, password: '123456', avatar: '👧' },
        ],
        teachers: [
            { id: 'T001', name: '张老师', subject: '数学', classes: ['一(1)班', '一(2)班', '一(3)班'], classIds: [1, 2, 3], password: '123456', avatar: '👩‍🏫' },
            { id: 'T002', name: '李老师', subject: '数学', classes: ['二(1)班', '二(2)班'], classIds: [4, 5], password: '123456', avatar: '👨‍🏫' },
            { id: 'T003', name: '王老师', subject: '数学', classes: ['三(1)班', '三(2)班'], classIds: [6, 7], password: '123456', avatar: '👩‍🏫' },
        ],
        admins: [
            { id: 'A001', name: '系统管理员', password: 'admin123', avatar: '👨‍💼' },
            { id: 'A002', name: '教务管理员', password: 'admin123', avatar: '👩‍💼' },
        ]
    },
    
    classes: [
        { id: 1, name: '一(1)班', grade: 1, studentCount: 45 },
        { id: 2, name: '一(2)班', grade: 1, studentCount: 42 },
        { id: 3, name: '一(3)班', grade: 1, studentCount: 45 },
        { id: 4, name: '二(1)班', grade: 2, studentCount: 43 },
        { id: 5, name: '二(2)班', grade: 2, studentCount: 40 },
        { id: 6, name: '三(1)班', grade: 3, studentCount: 45 },
        { id: 7, name: '三(2)班', grade: 3, studentCount: 43 },
    ],
    
    currentUser: null,
    currentClass: null,
    
    studentStats: {
        totalQuestions: 45,
        correctRate: 78,
        totalMistakes: 12,
        reviewedMistakes: 8,
        weakPoints: ['K005', 'K006', 'K010'],
        masteredPoints: ['K001', 'K002', 'K003', 'K004', 'K007', 'K008', 'K009']
    },
    
    fiveDimensionScores: {
        dimensions: [
            { dimension: 'operation', score: 85, label: '运算能力' },
            { dimension: 'logic', score: 62, label: '逻辑思维' },
            { dimension: 'spatial', score: 35, label: '空间想象' },
            { dimension: 'language', score: 72, label: '语言推理' },
            { dimension: 'resilience', score: 78, label: '学习韧性' }
        ]
    },
    
    weakKnowledge: [
        { id: 'K005', title: '认识立体图形', mastery_level: 30, mastery_level_str: 'Weak', questions: [
            { id: 'Q0014', text: '正方体有几个面？', difficulty: 2, answer: '6个' },
            { id: 'Q0012', text: '圆柱有几个面？', difficulty: 3, answer: '2个' },
            { id: 'Q0013', text: '球有几个面？', difficulty: 3, answer: '0个' }
        ], error_causes: ['P-008 混淆周长与面积的概念及计算公式']},
        { id: 'K006', title: '6-10的认识', mastery_level: 30, mastery_level_str: 'Weak', questions: [
            { id: 'Q0016', text: '9可以分成几和几？', difficulty: 2, answer: '4和5' },
            { id: 'Q0015', text: '10可以分成几和几？', difficulty: 3, answer: '5和5' }
        ], error_causes: ['I-005 从题目到草稿抄错数字']},
        { id: 'K010', title: '11-20各数的认识', mastery_level: 30, mastery_level_str: 'Weak', questions: [
            { id: 'Q0028', text: '16是由几个十和几个一组成的？', difficulty: 2, answer: '1个十和6个一' },
            { id: 'Q0029', text: '14是由几个十和几个一组成的？', difficulty: 3, answer: '1个十和4个一' }
        ], error_causes: ['P-004 小数位值概念不清']}
    ],
    
    masteredKnowledge: [
        { id: 'K001', title: '数一数（1-10的数数）', mastery_level: 70 },
        { id: 'K002', title: '比多少', mastery_level: 70 },
        { id: 'K003', title: '1-5的认识', mastery_level: 90 },
        { id: 'K004', title: '1-5的加减法', mastery_level: 85 },
        { id: 'K007', title: '6-10的加减法', mastery_level: 90 },
        { id: 'K008', title: '连加连减', mastery_level: 70 },
        { id: 'K009', title: '加减混合运算', mastery_level: 90 }
    ],
    
    mistakes: [
        { id: 'M001', question_id: 'Q0014', question_text: '正方体有几个面？', student_answer: '4', correct_answer: '6', error_type: '概念错误', error_name: '混淆立体图形概念', status: '未订正', date: '2026-07-25' },
        { id: 'M002', question_id: 'Q0016', question_text: '9可以分成几和几？', student_answer: '3和5', correct_answer: '4和5', error_type: '计算错误', error_name: '20以内加减法不熟练', status: '已订正', date: '2026-07-24' },
        { id: 'M003', question_id: 'Q0028', question_text: '16是由几个十和几个一组成的？', student_answer: '6个十和1个一', correct_answer: '1个十和6个一', error_type: '概念错误', error_name: '数位概念不清', status: '未订正', date: '2026-07-26' },
        { id: 'M004', question_id: 'Q0003', question_text: '小明有5个苹果，小红有4个苹果，谁的多？', student_answer: '小红', correct_answer: '小明', error_type: '审题错误', error_name: '漏读题目关键条件', status: '已订正', date: '2026-07-23' },
        { id: 'M005', question_id: 'Q0012', question_text: '圆柱有几个面？', student_answer: '1', correct_answer: '2个', error_type: '概念错误', error_name: '混淆立体图形概念', status: '未订正', date: '2026-07-26' }
    ],
    
    reviewPlan: [
        { id: 'R001', title: '复习：认识立体图形', knowledge_ids: ['K005'], questions: ['Q0014', 'Q0012', 'Q0013'], priority: '高', status: '进行中', due_date: '2026-07-28' },
        { id: 'R002', title: '复习：6-10的认识', knowledge_ids: ['K006'], questions: ['Q0016', 'Q0015'], priority: '中', status: '待开始', due_date: '2026-07-30' }
    ],
    
    learningPath: [
        { order: 1, knowledge_id: 'K005', title: '认识立体图形', mastery_level: 30, type: 'weak', estimated_time: '45分钟',
          prerequisites: ['K001: 数一数（1-10的数数）'],
          questions: [{ id: 'Q0014', text: '正方体有几个面？', difficulty: 2 }, { id: 'Q0012', text: '圆柱有几个面？', difficulty: 3 }, { id: 'Q0013', text: '球有几个面？', difficulty: 3 }],
          suggestions: ['建议从基础概念开始重新学习', '观看立体图形讲解视频', '完成基础难度的练习题', '重点关注: 概念错误']
        },
        { order: 2, knowledge_id: 'K006', title: '6-10的认识', mastery_level: 30, type: 'weak', estimated_time: '45分钟',
          prerequisites: ['K001: 数一数（1-10的数数）'],
          questions: [{ id: 'Q0016', text: '9可以分成几和几？', difficulty: 2 }, { id: 'Q0015', text: '10可以分成几和几？', difficulty: 3 }],
          suggestions: ['建议从基础概念开始重新学习', '练习数数和数的组成']
        },
        { order: 3, knowledge_id: 'K010', title: '11-20各数的认识', mastery_level: 30, type: 'weak', estimated_time: '45分钟',
          prerequisites: ['K006: 6-10的认识'],
          questions: [{ id: 'Q0028', text: '16是由几个十和几个一组成的？', difficulty: 2 }, { id: 'Q0029', text: '14是由几个十和几个一组成的？', difficulty: 3 }],
          suggestions: ['建议从基础概念开始重新学习', '理解数位概念']
        },
        { order: 4, knowledge_id: 'K003', title: '1-5的认识', mastery_level: 90, type: 'review', estimated_time: '30分钟',
          prerequisites: [],
          questions: [],
          suggestions: ['复习巩固已学知识', '做几道练习题保持熟练度']
        },
        { order: 5, knowledge_id: 'K007', title: '6-10的加减法', mastery_level: 90, type: 'review', estimated_time: '30分钟',
          prerequisites: ['K006: 6-10的认识'],
          questions: [],
          suggestions: ['复习巩固已学知识', '尝试变式题和综合题']
        }
    ],
    
    getClassStudents(classId) {
        return this.users.students.filter(s => s.classId === classId);
    },
    
    getTeacherDashboard(classId) {
        const cls = this.classes.find(c => c.id === classId);
        const students = this.getClassStudents(classId);
        return {
            classId: classId,
            className: cls ? cls.name : '未知班级',
            totalStudents: students.length,
            todayAssignments: students.length,
            submittedCount: Math.floor(students.length * 0.85),
            correctedCount: Math.floor(students.length * 0.78),
            pendingCount: Math.floor(students.length * 0.15),
            highFrequencyMistakes: [
                { knowledge_id: 'K005', knowledge_title: '认识立体图形', error_count: 25, error_type: '概念错误', error_name: '混淆立体图形概念' },
                { knowledge_id: 'K010', knowledge_title: '11-20各数的认识', error_count: 18, error_type: '概念错误', error_name: '数位概念不清' },
                { knowledge_id: 'K008', knowledge_title: '连加连减', error_count: 15, error_type: '计算错误', error_name: '20以内加减法不熟练' },
                { knowledge_id: 'K009', knowledge_title: '加减混合运算', error_count: 12, error_type: '审题错误', error_name: '漏读运算符号' },
                { knowledge_id: 'K004', knowledge_title: '1-5的加减法', error_count: 10, error_type: '计算错误', error_name: '进位加法漏加进位1' }
            ],
            knowledgeMastery: [
                { knowledge_id: 'K001', knowledge_title: '数一数', avg_mastery: 85 },
                { knowledge_id: 'K002', knowledge_title: '比多少', avg_mastery: 78 },
                { knowledge_id: 'K003', knowledge_title: '1-5的认识', avg_mastery: 92 },
                { knowledge_id: 'K004', knowledge_title: '1-5的加减法', avg_mastery: 76 },
                { knowledge_id: 'K005', knowledge_title: '认识立体图形', avg_mastery: 45 },
                { knowledge_id: 'K006', knowledge_title: '6-10的认识', avg_mastery: 52 },
                { knowledge_id: 'K007', knowledge_title: '6-10的加减法', avg_mastery: 88 },
                { knowledge_id: 'K008', knowledge_title: '连加连减', avg_mastery: 68 },
                { knowledge_id: 'K009', knowledge_title: '加减混合运算', avg_mastery: 65 },
                { knowledge_id: 'K010', knowledge_title: '11-20各数的认识', avg_mastery: 48 }
            ],
            recentAssignments: [
                { id: 'HW001', title: '第7课时作业', knowledge: 'K008-连加连减', submit_count: Math.floor(students.length * 0.85), correct_rate: 72, date: '2026-07-27' },
                { id: 'HW002', title: '第6课时作业', knowledge: 'K007-6-10的加减法', submit_count: Math.floor(students.length * 0.93), correct_rate: 85, date: '2026-07-26' },
                { id: 'HW003', title: '第5课时作业', knowledge: 'K005-认识立体图形', submit_count: Math.floor(students.length * 0.89), correct_rate: 45, date: '2026-07-25' }
            ],
            students: students
        };
    },
    
    adminDashboard: {
        systemOverview: {
            totalUsers: 1256,
            totalStudents: 1200,
            totalTeachers: 50,
            totalClasses: 30,
            totalQuestions: 1257,
            totalKnowledgePoints: 255,
            totalMistakes: 490,
            todayActiveUsers: 856
        },
        knowledgeStats: {
            byGrade: [
                { grade: 1, count: 45 },
                { grade: 2, count: 42 },
                { grade: 3, count: 45 },
                { grade: 4, count: 43 },
                { grade: 5, count: 40 },
                { grade: 6, count: 40 }
            ],
            byDifficulty: [
                { difficulty: 1, count: 378 },
                { difficulty: 2, count: 362 },
                { difficulty: 3, count: 67 },
                { difficulty: 4, count: 0 },
                { difficulty: 5, count: 0 }
            ],
            recentAdded: [
                { id: 'Q1257', title: '应用题：行程问题', knowledge: 'K120-行程问题', difficulty: 3, date: '2026-07-27' },
                { id: 'Q1256', title: '计算题：分数除法', knowledge: 'K115-分数除法', difficulty: 2, date: '2026-07-26' }
            ]
        },
        userManagement: {
            students: [
                { id: 'S001', name: '许嘉豪', class: '一(1)班', status: '活跃', lastLogin: '2026-07-27 10:30' },
                { id: 'S002', name: '蔡雨涵', class: '一(2)班', status: '活跃', lastLogin: '2026-07-27 09:15' },
                { id: 'S003', name: '何浩宇', class: '一(1)班', status: '活跃', lastLogin: '2026-07-26 16:45' },
                { id: 'S004', name: '曹佳怡', class: '一(3)班', status: '活跃', lastLogin: '2026-07-27 11:20' },
                { id: 'S005', name: '许佳怡', class: '一(2)班', status: '冻结', lastLogin: '2026-07-20 14:00' }
            ],
            teachers: [
                { id: 'T001', name: '张老师', subject: '数学', classes: 3, status: '活跃' },
                { id: 'T002', name: '李老师', subject: '数学', classes: 2, status: '活跃' }
            ]
        }
    },
    
    errorAnalysis: {
        errorCategories: [
            { name: '计算错误', count: 156, percentage: 32 },
            { name: '概念错误', count: 134, percentage: 27 },
            { name: '审题错误', count: 89, percentage: 18 },
            { name: '抄写错误', count: 67, percentage: 14 },
            { name: '逻辑错误', count: 45, percentage: 9 }
        ],
        knowledgeErrorRanking: [
            { knowledge_id: 'K005', knowledge_title: '认识立体图形', error_count: 156, mastery: 45 },
            { knowledge_id: 'K010', knowledge_title: '11-20各数的认识', error_count: 134, mastery: 48 },
            { knowledge_id: 'K008', knowledge_title: '连加连减', error_count: 98, mastery: 68 },
            { knowledge_id: 'K009', knowledge_title: '加减混合运算', error_count: 87, mastery: 65 },
            { knowledge_id: 'K004', knowledge_title: '1-5的加减法', error_count: 76, mastery: 76 }
        ]
    },
    
    pendingInterfaces: {
        reviewPlan: {
            status: 'pending',
            owner: '同事A',
            description: '复习计划生成接口',
            input: ['student_id', 'weak_knowledge_ids', 'learning_path'],
            output: ['review_plan_id', 'plan_items', 'priority', 'due_date'],
            api: 'POST /api/review_plan/generate'
        },
        errorAnalysis: {
            status: 'pending',
            owner: '同事B',
            description: '错因分析接口',
            input: ['student_id', 'question_id', 'student_answer', 'correct_answer'],
            output: ['error_type', 'error_detail', 'suggestions'],
            api: 'POST /api/error/analyze'
        }
    }
};