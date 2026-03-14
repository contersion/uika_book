import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
import { useAuthStore } from "./stores/auth";
import { pinia } from "./stores";
import "./styles/index.css";

async function bootstrap() {
  const app = createApp(App);

  app.use(pinia);

  const authStore = useAuthStore(pinia);
  await authStore.ensureReady();

  app.use(router);
  await router.isReady();

  app.mount("#app");
}

bootstrap();
