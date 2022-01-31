<template>
    <div id="app">
        <el-menu :default-active="curr_nav" class="top-nav" mode="horizontal" :router=true>
            <template v-if="login">
                <el-menu-item index="/HttpAccessLog">
                    HTTP 日志
                </el-menu-item>
                <el-menu-item index="/HttpRule">
                    HTTP 规则
                </el-menu-item>
                <el-menu-item index="/UploadFile">
                    文件管理
                </el-menu-item>
                <el-menu-item index="/DNSLog">
                    DNS 日志
                </el-menu-item>
                <el-menu-item index="/Logout" @click.native="logout" class="float-right">
                    退出
                </el-menu-item>
                <el-menu-item index="/Config" class="float-right">
                    设置
                </el-menu-item>
                <el-menu-item index="/User" class="float-right">
                    用户
                </el-menu-item>
                <el-menu-item index="/SystemLog" class="float-right">
                    系统日志
                </el-menu-item>
            </template>
            <template v-else>
                <el-menu-item index="/Login">
                    登陆
                </el-menu-item>
            </template>
        </el-menu>

        <div class="main-container">
            <router-view></router-view>
        </div>
    </div>
</template>

<script>
import user from "./class/User";
import router from "./router";
import access_log from "./class/HttpAccessLog";
import request from "@/class/Request";
import utils from "@/class/Utils";

export default {
    name: 'App',
    data() {
        return {
            curr_nav: "/Login",
            login: false
        };
    },
    async mounted() {
        router.beforeEach(async (to, from, next) => {
            if (to.path === '/Login') {
                next();
            } else {
                if (await user.is_login()) {
                    this.login = true;
                    next();
                } else {
                    next({
                        'path': '/Login'
                    });
                }
            }
        });

        if (await user.is_login()) {
            this.login = true;
            // user.renew_token();
            router.push({'path': '/HttpAccessLog'});
        } else {
            this.login = false;
            router.push({'path': '/Login'});
        }
        this.get_websocket();
    },
    methods: {
        async get_websocket() {
            let ws = await request.open_websocket();
            ws.onmessage = this.websocket_on_message;
            ws.onclose = this.websocket_on_close;
        },
        async websocket_on_message(event) {
            if (event.data) {
                let msg = JSON.parse(event.data);
                if (msg.msg_type === utils.websocket_message_type.NEW_HTTP_ACCESS_LOG) {
                    if (utils.load_localstorage(utils.localstorage_keys.HTTP_ACCESS_LOG_NOTIFICATION, true)) {
                        document.title = '[新消息] 管理面板'
                        this.$notify({
                            title: 'HTTP 新请求',
                            message: msg.msg_content,
                            type: 'warning',
                            position: 'top-left',
                            offset: 50,
                            duration: 1500
                        });
                    }
                } else if (msg.msg_type === utils.websocket_message_type.NEW_DNS_LOG) {
                    if (utils.load_localstorage(utils.localstorage_keys.DNS_LOG_NOTIFICATION, true)) {
                        document.title = '[新消息] 管理面板'
                        this.$notify({
                            title: 'DNS 新请求',
                            message: msg.msg_content,
                            type: 'warning',
                            position: 'top-left',
                            offset: 50,
                            duration: 1500
                        });
                    }
                }
            }
        },
        async websocket_on_close(event) {
            setTimeout(this.get_websocket, 3000);
        },
        logout() {
            this.login = false;
            user.logout();
            router.push({'path': '/Login'});
        }
    }
};
</script>

<style>
.float-right {
    float: right !important;
}

.less-table-padding td, .less-table-padding th {
    padding: 5px !important;
}

.file_dialog > .el-dialog__body {
    padding-top: 0px !important;
}
.el-table__placeholder {
    width: 0 !important;
}
</style>
