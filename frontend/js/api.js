const API_BASE = 'http://127.0.0.1:8000/api';

const Api = {
    async fetch(endpoint, options = {}) {
        try {
            const url = API_BASE + endpoint;
            const withCredentials = {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...(options.headers || {})
                }
            };
            const response = await fetch(url, withCredentials);
            if (!response.ok) {
                let detail = 'API请求失败: ' + response.status;
                try {
                    const body = await response.json();
                    if (body && body.detail) {
                        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
                    }
                } catch (e) { /* 非 JSON 响应，保留默认信息 */ }
                throw new Error(detail);
            }
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // ============ 账号 API（走网关 8000 统一入口） ============

    async login(username, password) {
        return this.fetch('/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    },

    async register(username, password, grade = null, semester = null) {
        return this.fetch('/register', {
            method: 'POST',
            body: JSON.stringify({ username, password, grade, semester })
        });
    },

    // ============ 错题提交 API（网关本地处理：OCR + 判题） ============

    async submitHomework(studentId, imageDataUrl) {
        return this.fetch('/v1/submit', {
            method: 'POST',
            body: JSON.stringify({
                student_id: studentId,
                image: imageDataUrl
            })
        });
    },

    async getStudents(grade, className) {
        let params = [];
        if (grade) params.push('grade=' + grade);
        if (className) params.push('class_name=' + encodeURIComponent(className));
        const query = params.length > 0 ? '?' + params.join('&') : '';
        return this.fetch('/students/' + query);
    },

    async getClasses() {
        return this.fetch('/students/classes');
    },

    async getStudent(studentId) {
        return this.fetch('/students/' + studentId);
    },

    async getStudentMastery(studentId) {
        return this.fetch('/v1/student/' + studentId + '/mastery');
    },

    async getStudentWeakPoints(studentId, threshold = 60) {
        return this.fetch('/students/' + studentId + '/weak?threshold=' + threshold);
    },

    async getClassStudents(className) {
        const encoded = encodeURIComponent(className);
        return this.fetch('/students/class/' + encoded);
    },

    async getClassMastery(className) {
        const encoded = encodeURIComponent(className);
        return this.fetch('/students/class/' + encoded + '/mastery');
    },

    async getClassMistakeStats(className) {
        const encoded = encodeURIComponent(className);
        return this.fetch('/class/' + encoded + '/mistake-stats');
    },

    async getKnowledgePoints(grade, semester) {
        let params = [];
        if (grade) params.push('grade=' + grade);
        if (semester) params.push('semester=' + encodeURIComponent(semester));
        const query = params.length > 0 ? '?' + params.join('&') : '';
        return this.fetch('/knowledge_points' + query);
    },

    async getKnowledgePoint(knowledgeId) {
        return this.fetch('/knowledge_points/' + encodeURIComponent(knowledgeId));
    },

    async getKnowledgeExplanation(knowledgeId) {
        return this.fetch('/knowledge_points/' + encodeURIComponent(knowledgeId) + '/explanation');
    },

    async getKnowledgeDetail(knowledgeId) {
        return this.fetch('/datahub/knowledge/' + encodeURIComponent(knowledgeId));
    },

    async getGrowthReport(studentId) {
        return this.fetch('/growth_report/' + studentId);
    },

    async getLearningPath(studentId) {
        return this.fetch('/learning_path/' + studentId);
    },

    async getStatisticsOverview() {
        return this.fetch('/datahub/statistics/overview');
    },

    // ============ 复习计划 API ============

    async calculatePriority(studentId) {
        return this.fetch('/v1/priority-runs', {
            method: 'POST',
            body: JSON.stringify({ student_id: studentId })
        });
    },

    async createReviewPlan(studentId, mode = 'question_count', questionCount = 10, timeLimitMinutes = null) {
        const body = {
            student_id: studentId,
            mode: mode
        };
        if (mode === 'question_count') {
            body.question_count = questionCount;
        } else if (mode === 'time_limit') {
            body.time_limit_minutes = timeLimitMinutes || 30;
        }
        return this.fetch('/v1/review-plans', {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    async getReviewPlan(planId) {
        return this.fetch('/v1/review-plans/' + planId);
    },

    async updateReviewPlanCapacity(planId, questionCount) {
        return this.fetch('/v1/review-plans/' + planId + '/capacity', {
            method: 'PATCH',
            body: JSON.stringify({ question_count: questionCount })
        });
    },

    async startReviewSession(planId) {
        return this.fetch('/v1/review-plans/' + planId + '/start', {
            method: 'POST'
        });
    },

    async getReviewSession(sessionId) {
        return this.fetch('/v1/review-sessions/' + sessionId);
    },

    async pauseReviewSession(sessionId) {
        return this.fetch('/v1/review-sessions/' + sessionId + '/pause', {
            method: 'POST'
        });
    },

    async resumeReviewSession(sessionId) {
        return this.fetch('/v1/review-sessions/' + sessionId + '/resume', {
            method: 'POST'
        });
    },

    async submitAttempt(sessionId, questionId, selectedOption, timeSpentSeconds) {
        return this.fetch('/v1/review-sessions/' + sessionId + '/attempts', {
            method: 'POST',
            body: JSON.stringify({
                question_id: questionId,
                selected_option: selectedOption,
                time_spent_seconds: timeSpentSeconds
            })
        });
    },

    async submitCorrection(attemptId, selectedOption) {
        return this.fetch('/v1/attempts/' + attemptId + '/correction', {
            method: 'POST',
            body: JSON.stringify({
                selected_option: selectedOption
            })
        });
    },

    // ============ 错题本 API ============

    async addWrongQuestion(userId, questionId, wrongAnswer = null, errorCauseId = null) {
        return this.fetch('/wrong_questions', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                question_id: questionId,
                wrong_answer: wrongAnswer,
                error_cause_id: errorCauseId
            })
        });
    },

    async getWrongQuestions(userId) {
        return this.fetch('/wrong_questions/' + userId);
    },

    async markWrongReviewed(userId, questionId) {
        return this.fetch('/wrong_questions/' + userId + '/' + questionId, {
            method: 'PUT'
        });
    },

    // ============ 学习进度 API ============

    async updateLearningProgress(userId, knowledgeId, isCorrect) {
        return this.fetch('/learning_progress', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                knowledge_id: knowledgeId,
                is_correct: isCorrect
            })
        });
    },

    async getLearningProgress(userId) {
        return this.fetch('/learning_progress/' + userId);
    },

    async getWeakPoints(userId, threshold = 60) {
        return this.fetch('/weak_points/' + userId + '?threshold=' + threshold);
    },

    // ============ 答题记录 API ============

    async addAnswerRecord(userId, questionId, answer, isCorrect, timeSpent = null) {
        return this.fetch('/answer_records', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                question_id: questionId,
                answer: answer,
                is_correct: isCorrect,
                time_spent: timeSpent
            })
        });
    },

    async getAnswerRecords(userId, limit = 100) {
        return this.fetch('/answer_records/' + userId + '?limit=' + limit);
    },

    // ============ 复习计划 API（用户维度） ============

    async addUserReviewPlan(userId, questionId, reviewTime, priority = 1) {
        return this.fetch('/review_plans', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                question_id: questionId,
                review_time: reviewTime,
                priority: priority
            })
        });
    },

    async getPendingReviews(userId) {
        return this.fetch('/review_plans/' + userId + '/pending');
    },

    async completeReview(reviewId) {
        return this.fetch('/review_plans/' + reviewId + '/complete', {
            method: 'PUT'
        });
    },

    // ============ 作业批次管理 API（教师端） ============

    async createHomeworkBatch(classId, teacherId, batchDate, questionIds) {
        return this.fetch('/v1/teacher/homework_batch', {
            method: 'POST',
            body: JSON.stringify({
                class_id: classId,
                teacher_id: teacherId,
                batch_date: batchDate,
                question_ids: questionIds
            })
        });
    },

    async getHomeworkBatches(classId, teacherId) {
        let params = [];
        if (classId) params.push('class_id=' + encodeURIComponent(classId));
        if (teacherId) params.push('teacher_id=' + encodeURIComponent(teacherId));
        const query = params.length > 0 ? '?' + params.join('&') : '';
        return this.fetch('/v1/teacher/homework_batch' + query);
    },

    async releaseHomeworkBatch(batchId) {
        return this.fetch('/v1/teacher/homework_batch/' + batchId + '/release', {
            method: 'POST'
        });
    },

    async releaseHomeworkBatchPartial(batchId, questionIds) {
        return this.fetch('/v1/teacher/homework_batch/' + batchId + '/release_partial', {
            method: 'POST',
            body: JSON.stringify({ question_ids: questionIds })
        });
    },

    // 获取题目列表（用于批次选题）
    async getQuestionsForBatch(grade, knowledgeId, page, pageSize) {
        return this.fetch('/questions?grade=' + (grade || '') + '&knowledge_id=' + (knowledgeId || '') + '&page=' + (page || 1) + '&page_size=' + (pageSize || 50));
    },

    // 学生首页统计与错题本（真实数据，SQLite 聚合）
    async getStudentStats(studentId) {
        return this.fetch('/student/' + studentId + '/stats');
    },

    async getStudentWrongAnswers(studentId) {
        return this.fetch('/student/' + studentId + '/wrong-answers');
    }
};
