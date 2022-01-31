import Vue from 'vue';
import Router from 'vue-router';
import HttpAccessLog from "./components/HttpAccessLog";
import Login from "./components/Login";
import HttpRule from "./components/HttpRule";
import UploadFile from "./components/UploadFile";
import Config from "./components/Config";
import SystemLog from "./components/SystemLog";
import User from "./components/User";
import DNSLog from "@/components/DNSLog";

const original_push = Router.prototype.push;
Router.prototype.push = function push(location) {
    return original_push.call(this, location).catch(err => err);
};

Vue.use(Router);

export default new Router({
    routes: [
        {
            path: '/HttpAccessLog',
            name: 'HttpAccessLog',
            component: HttpAccessLog
        },
        {
            path: '/Login',
            name: 'Login',
            component: Login
        },
        {
            path: '/HttpRule',
            name: 'HttpRule',
            component: HttpRule
        },
        {
            path: '/UploadFile',
            name: 'UploadFile',
            component: UploadFile
        },
        {
            path: '/DNSLog',
            name: 'DNSLog',
            component: DNSLog
        },
        {
            path: '/Config',
            name: 'Config',
            component: Config
        },
        {
            path: '/SystemLog',
            name: 'SystemLog',
            component: SystemLog
        },
        {
            path: '/User',
            name: 'User',
            component: User
        },
    ]
});
