//import Vue from 'vue';
import App from './App.vue';
import JSONView from 'vue-json-viewer';
import VueClipboard from 'vue-clipboard2';
import router from './router';

Vue.use(JSONView);
Vue.use(VueClipboard);

Vue.config.productionTip = false;

new Vue({
    render: h => h(App),
    router,
}).$mount('#app');
