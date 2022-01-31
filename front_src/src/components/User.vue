<template>
    <div>
        <el-row justify="center" style="margin-top: 20px;" type="flex">
            <el-col :lg="12" :sm="16">
                <div class="grid-content">
                    <el-card>
                        <h2>密码</h2>
                        <el-form>
                            <el-input v-model="password.original_password" placeholder="原密码" type="password"></el-input>
                            <el-input v-model="password.new_password" placeholder="新密码" style="margin-top: 10px"
                                      type="password"></el-input>
                            <el-input v-model="password.new_password_repeat" placeholder="重新输入" style="margin-top: 10px"
                                      type="password"></el-input>
                            <el-form-item>
                                <el-button style="margin-top: 10px; float: right" type="primary"
                                           @click="modify_password">提交
                                </el-button>
                            </el-form-item>
                        </el-form>
                    </el-card>
                </div>
            </el-col>
        </el-row>

        <el-row v-if="user.is_admin" justify="center" style="margin-top: 20px;" type="flex">
            <el-col :lg="12" :sm="16">
                <div class="grid-content">
                    <el-card>
                        <el-row type="flex" justify="space-between" align="middle">
                            <el-col :span="16">
                                <h2>用户列表</h2>
                            </el-col>
                            <el-col :span="4" :offset="10">
                                <el-button type="primary" size="mini" style="margin-right: 45px" @click="register_user_form_show">
                                    新建用户
                                </el-button>
                            </el-col>
                        </el-row>

                        <el-table
                            row-class-name="less-table-padding"
                            style="width: 100%;"
                            :data="this.user.users">
                            <el-table-column
                                label="用户名"
                                prop="username"
                                show-overflow-tooltip>
                            </el-table-column>
                            <el-table-column
                                label="用户类型"
                                prop="user_type">
                            </el-table-column>
                            <el-table-column label="操作" width="250" align="center">
                                <template slot-scope="scope">
                                    <el-button :disabled="!scope.row.editable" type="primary" size="mini"
                                               @click="change_other_user_password_form_show(scope.row)">
                                        修改密码
                                    </el-button>
                                    <el-button :disabled="!scope.row.editable" type="danger" size="mini"
                                               @click="delete_user(scope.row)">
                                        删除
                                    </el-button>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-card>
                </div>
            </el-col>
        </el-row>

        <el-dialog
            :title="user.form_title"
            :visible.sync="user.form_visible"
            :close-on-click-modal="false"
            width="30%">
            <div>
                <label>用户名</label>:<br>
                <el-input :readonly="user.form_username_disabled" v-model="user.form_username" placeholder="" style="margin-top: 10px"></el-input>
            </div>
            <div style="margin-top: 10px">
                <label>密码</label>:<br>
                <el-input v-model="user.form_password" placeholder="" type="password" style="margin-top: 10px"></el-input>
            </div>
            <div style="margin-top: 30px; text-align: right">
                <el-button @click="cancel_form">取消</el-button>
                <el-button type="primary" @click="user.form_submit_handler()">确定</el-button>
            </div>
        </el-dialog>
    </div>
</template>

<script>
import request from "@/class/Request";
import config from "@/class/Config";
import user from "@/class/User";
import utils from "@/class/Utils";
import http_rule from "@/class/HttpRule";
import Vue from "vue";

export default {
    name: "User",
    data() {
        return {
            password: {
                original_password: "",
                new_password: "",
                new_password_repeat: ""
            },
            user: {
                is_admin: false,
                users: [],

                form_submit_handler: () => {},
                form_title: '',
                form_visible: false,
                form_username: '',
                form_password: '',
                form_username_disabled: false
            },
        }
    },
    async mounted() {
        this.user.is_admin = user.is_admin();
        if (this.user.is_admin) {
            await this.get_user();
        }
    },
    methods: {
        async get_user() {
            let users = (await user.list_user()).payload;
            users = users.map((u) => {
                if (u.user_type === utils.user_type.USER_TYPE_ADMIN) {
                    u.user_type = '管理员';
                    u.editable = false;
                } else {
                    u.user_type = '普通用户';
                    u.editable = true;
                }
                return u;
            })
            this.user.users = users;
        },
        async modify_password() {
            let password = this.password.new_password.trim();
            let password_repeat = this.password.new_password_repeat.trim();
            let original_password = this.password.original_password.trim();

            if (original_password === "") {
                this.$message.error("请输入原密码");
                return;
            }

            if (password !== password_repeat) {
                this.$message.error("两次密码不一致");
                return;
            }
            if (password === "") {
                this.$message.error("新密码不能为空");
                return;
            }

            // original_password !== "" && password !== "" && password === password_repeat
            let username = utils.load_localstorage(utils.localstorage_keys.CURRENT_USERNAME);
            password = utils.pbkdf2(password, username);
            original_password = utils.pbkdf2(original_password, username);

            let res = await user.change_password(original_password, password);
            if (res.code === request.CODE_SUCCESS) {
                this.$message.success("修改成功");
            } else {
                this.$message.error(res.msg);
            }
        },
        async change_other_user_password(row) {
            let username = this.user.form_username;
            let password = this.user.form_password;
            password = utils.pbkdf2(password, username);

            let res = await user.change_other_user_password(username, password);
            if (res.code === request.CODE_SUCCESS) {
                this.$message.success("修改成功");
                this.user.form_visible = false;
                await this.get_user();
            } else {
                this.$message.error(res.msg);
            }
        },
        async change_other_user_password_form_show(row) {
            this.user.form_username = '';
            this.user.form_password = '';

            this.user.form_submit_handler = this.change_other_user_password;
            this.user.form_visible = true;
            this.user.form_username_disabled = true;
            this.user.form_title = '编辑用户';

            this.user.form_username = row.username;
        },
        async register_user() {
            let res = await user.register_user(this.user.form_username, this.user.form_password);
            if (res.code === request.CODE_SUCCESS) {
                this.$message.success("注册成功");
                this.user.form_visible = false;
                await this.get_user();
            } else {
                this.$message.error(res.msg);
            }
        },
        async register_user_form_show() {
            this.user.form_username = '';
            this.user.form_password = '';

            this.user.form_submit_handler = this.register_user;
            this.user.form_visible = true;
            this.user.form_username_disabled = false;
            this.user.form_title = '注册用户';
        },
        async delete_user(row) {
            this.$confirm('确定删除该用户?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                let username = row.username;

                let res = await user.delete_user(username);
                if (res.code === request.CODE_SUCCESS) {
                    this.$message.success("删除成功");
                    await this.get_user();
                } else {
                    this.$message.error(res.msg);
                }
            }).catch(() => {
            });
        },
        cancel_form() {
            this.user.form_visible = false;
        }
    }
};
</script>

<style scoped>

</style>