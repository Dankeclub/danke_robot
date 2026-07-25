import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
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

const routes = [
  { path: '/', component: HomeView, meta: { scene: 'home' } },
  { path: '/tasks', component: TaskListView, meta: { scene: 'tasks' } },
  { path: '/challenge', component: ChallengeView, meta: { scene: 'challenge' } },
  { path: '/celebrate', component: CelebrateView, meta: { scene: 'celebrate' } },
  { path: '/chat', component: ChatView, meta: { scene: 'chat' } },
  { path: '/learning', component: LearningView, meta: { scene: 'learning' } },
  { path: '/science', component: ScienceView, meta: { scene: 'science' } },
  { path: '/math', component: MathView, meta: { scene: 'math' } },
  { path: '/english', component: EnglishView, meta: { scene: 'english' } },
  { path: '/poems', component: PoemsView, meta: { scene: 'poems' } },
  { path: '/music', component: MusicView, meta: { scene: 'music' } },
  { path: '/quiz', component: QuizView, meta: { scene: 'quiz' } },
  { path: '/qabox', component: QaBoxView, meta: { scene: 'qabox' } },
  { path: '/messages', component: MessagesView, meta: { scene: 'messages' } },
  { path: '/idle', component: IdleView, meta: { scene: 'idle' } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
