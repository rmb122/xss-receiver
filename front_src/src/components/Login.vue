<template>
    <el-row type="flex" justify="center" style="margin-top: 100px;">
        <el-col :lg="12" :sm="16">
            <div class="grid-content">
                <el-card>
                    <h2>登录</h2>
                    <el-form @keyup.enter.native="login" v-loading="loading">
                        <el-form-item label="账号">
                            <el-input type="text" placeholder="账号" v-model="form.username"></el-input>
                        </el-form-item>
                        <el-form-item label="密码">
                            <el-input type="password" placeholder="密码" v-model="form.password"></el-input>
                        </el-form-item>
                        <el-form-item>
                            <el-button @click.prevent="login" type="primary" style="float: right">提交</el-button>
                        </el-form-item>
                    </el-form>
                </el-card>
            </div>
        </el-col>
    </el-row>
</template>

<script>
import user from "../class/User";
import request from "../class/Request";
import router from "../router";

export default {
    name: 'Login',
    data() {
        return {
            form: {
                username: "",
                password: ""
            },
            loading: false,
        };
    },
    async mounted() {
        if (await user.is_login()) {
            router.push({'path': '/HttpAccessLog'});
        }
    },
    methods: {
        async login() {
            if (this.form.username !== "" && this.form.password !== "") {
                let status = await user.login(this.form.username, this.form.password);
                if (status) {
                    router.push({'path': '/HttpAccessLog'});
                } else {
                    this.$message.error("账号或密码错误");
                }
            } else {
                this.$message.error("请输入账号密码!");
            }
        }
    }
};
</script>
