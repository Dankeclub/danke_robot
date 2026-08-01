import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import TaskListView from '../views/TaskListView.vue'
import ChallengeView from '../views/ChallengeView.vue'
import CelebrateView from '../views/CelebrateView.vue'
import ChatView from '../views/ChatView.vue'
import LearningView from '../views/LearningView.vue'
import ScienceView from '../views/ScienceView.vue'
import MathView from '../views/MathView.vue'
import EnglishView from '../views/EnglishView.vue'
import PoemsView from '../views/PoemsView.vue'
import MusicView from '../views/MusicView.vue'
import QuizView from '../views/QuizView.vue'
import QaBoxView from '../views/QaBoxView.vue'
import MessagesView from '../views/MessagesView.vue'
import IdleView from '../views/IdleView.vue'
import { getToken } from '../utils/api.js'

const routes = [
  { path: '/login', component: LoginView, meta: { scene: 'login' } },
  { path: '/', component: HomeView, meta: { scene: 'home', requiresAuth: true } },
  { path: '/tasks', component: TaskListView, meta: { scene: 'tasks', requiresAuth: true } },
  { path: '/challenge', component: ChallengeView, meta: { scene: 'challenge', requiresAuth: true } },
  { path: '/celebrate', component: CelebrateView, meta: { scene: 'celebrate', requiresAuth: true } },
  { path: '/chat', component: ChatView, meta: { scene: 'chat', requiresAuth: true } },
  { path: '/learning', component: LearningView, meta: { scene: 'learning', requiresAuth: true } },
  { path: '/science', component: ScienceView, meta: { scene: 'science', requiresAuth: true } },
  { path: '/math', component: MathView, meta: { scene: 'math', requiresAuth: true } },
  { path: '/english', component: EnglishView, meta: { scene: 'english', requiresAuth: true } },
  { path: '/poems', component: PoemsView, meta: { scene: 'poems', requiresAuth: true } },
  { path: '/music', component: MusicView, meta: { scene: 'music', requiresAuth: true } },
  { path: '/quiz', component: QuizView, meta: { scene: 'quiz', requiresAuth: true } },
  { path: '/qabox', component: QaBoxView, meta: { scene: 'qabox', requiresAuth: true } },
  { path: '/messages', component: MessagesView, meta: { scene: 'messages', requiresAuth: true } },
  { path: '/idle', component: IdleView, meta: { scene: 'idle', requiresAuth: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// Auth guard
router.beforeEach((to, from, next) => {
  const token = getToken()
  if (to.path === '/login') {
    // Already logged in → go home
    if (token) return next('/')
    return next()
  }
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }
  next()
})

export default router
