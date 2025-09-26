import { createRouter, createWebHistory } from "vue-router"
import login from "../views/login/login.vue"

const routes = [
  {
    path: "/",
    redirect: "/login",
    meta: { public: true },
  },
  {
    path: "/login",
    component: login,
    meta: { public: true }
  }
];

const router = createRouter({
  history: createWebHistory('/project_vue/'),
  routes,
});

export default router;