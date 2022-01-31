<template>
    <div>
        <el-row justify="center" style="margin-top: 20px;" type="flex">
            <el-col :lg="12" :sm="16">
                <div class="grid-content">
                    <el-card v-loading="this.loading">
                        <h2>系统设置</h2>
                        注意: 值为 JSON 格式
                        <el-table
                            row-class-name="less-table-padding"
                            style="width: 100%;"
                            :data="this.config.configs">
                            <el-table-column
                                label="配置名"
                                prop="key">
                            </el-table-column>
                            <el-table-column
                                label="备注"
                                prop="comment">
                            </el-table-column>
                            <el-table-column
                                label="值"
                                prop="value">
                                <template slot-scope="scope">
                                    <template v-if="scope.row.editing">
                                        <el-input v-model="config.last_edit_value" size="mini"></el-input>
                                    </template>
                                    <template v-else>
                                        {{ JSON.stringify(scope.row.value) }}
                                    </template>
                                </template>
                            </el-table-column>
                            <el-table-column label="操作" width="250" align="center">
                                <template slot-scope="scope">
                                    <template v-if="!scope.row.editing">
                                        <el-button type="primary" size="mini" @click="start_config_edit(scope.row)">编辑
                                        </el-button>
                                    </template>
                                    <template v-else>
                                        <el-button type="success" size="mini" @click="save_config(scope.row)">保存
                                        </el-button>
                                    </template>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-card>
                </div>
            </el-col>
        </el-row>

        <el-row justify="center" style="margin-top: 20px;" type="flex">
            <el-col :lg="12" :sm="16">
                <div class="grid-content">
                    <el-card>
                        <h2>通知管理</h2>
                        <el-form>
                            <el-switch v-model="notification.http_access_log" active-text="开启 HTTP 日志通知" @change="change_http_access_log_notification"></el-switch>
                            <br>
                            <el-switch  v-model="notification.dns_log" active-text="开启 DNS 日志通知" @change="change_dns_log_notification" style="margin-top: 15px"></el-switch>
                        </el-form>
                    </el-card>
                </div>
            </el-col>
        </el-row>

        <el-row justify="center" style="margin-top: 20px; margin-bottom: 100px" type="flex">
            <el-col :lg="12" :sm="16">
                <div class="grid-content">
                    <el-card>
                        <h2>数据管理</h2>
                        <el-form>
                            <el-form-item label="清空临时上传文件">
                                <br>
                                <el-button type="danger" @click="clean_temp_file">清空</el-button>
                            </el-form-item>
                            <el-form-item label="清空 HTTP 日志">
                                <br>
                                <el-button type="danger" @click="clean_http_access_log">清空</el-button>
                            </el-form-item>
                            <el-form-item label="清空 DNS 日志">
                                <br>
                                <el-button type="danger" @click="clean_dns_log">清空</el-button>
                            </el-form-item>
                        </el-form>
                    </el-card>
                </div>
            </el-col>
        </el-row>
    </div>
</template>

<script>
import config from "../class/Config";
import {sha256} from "js-sha256";
import request from "../class/Request";
import utils from "@/class/Utils";

export default {
    name: "Config",
    data() {
        return {
            loading: false,
            config: {
                configs: [],
                last_edit_index: null,
                last_edit_value: null,
            },
            notification: {
                http_access_log: true,
                dns_log: true
            }
        };
    },
    async mounted() {
        this.notification.http_access_log = utils.load_localstorage(utils.localstorage_keys.HTTP_ACCESS_LOG_NOTIFICATION, true);
        this.notification.dns_log = utils.load_localstorage(utils.localstorage_keys.DNS_LOG_NOTIFICATION, true);

        this.loading = true;
        await this.load_config();
        this.loading = false;
    },
    methods: {
        async load_config() {
            let res = await config.get_config();
            if (res.code === request.CODE_SUCCESS) {
                let configs = res.payload;
                configs.filter((config, index) => {
                    config.editing = false, config.index = index;
                });
                this.config.configs = configs;
            } else {
                this.$message.error("配置文件获取失败");
            }
        },
        async clean_temp_file() {
            this.$confirm('确定清空所有临时文件?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                let res = await config.clean_temp_file();
                if (res.code === request.CODE_SUCCESS) {
                    this.$message.success("清除成功");
                } else {
                    this.$message.error(res.msg);
                }
            }).catch(() => {
            });
        },
        async clean_http_access_log() {
            this.$confirm('确定清空所有 HTTP 日志?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                let res = await config.clean_http_access_log();
                if (res.code === request.CODE_SUCCESS) {
                    this.$message.success("清除成功");
                } else {
                    this.$message.error(res.msg);
                }
            }).catch(() => {
            });
        },
        async clean_dns_log() {
            this.$confirm('确定清空所有 DNS 日志?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                let res = await config.clean_dns_log();
                if (res.code === request.CODE_SUCCESS) {
                    this.$message.success("清除成功");
                } else {
                    this.$message.error(res.msg);
                }
            }).catch(() => {
            });
        },
        async start_config_edit(row) {
            if (this.config.last_edit_index != null && this.config.last_edit_index !== row.index) {
                this.config.configs[this.config.last_edit_index].editing = false;
            }
            if (this.config.last_edit_index != row.index) {
                this.config.last_edit_value = JSON.stringify(row.value);
            }
            row.editing = true;
            this.config.last_edit_index = row.index;
        },
        async save_config(row) {
            if (row.editing) {
                if (this.config.last_edit_value !== JSON.stringify(row.value)) {
                    let value = null;
                    try {
                        value = JSON.parse(this.config.last_edit_value);
                    } catch (e) {
                        this.$message.warning("输入值不是有效的 JSON");
                        return;
                    }

                    let result = await config.modify_config(row.key, value);
                    if (result.code === request.CODE_SUCCESS) {
                        this.$message.success('修改成功');
                        row.editing = false;
                        await this.load_config();
                    } else {
                        this.$message.error(result.msg);
                    }
                } else {
                    row.editing = false;
                    this.$message.warning("没有检测到变化");
                }
            }
        },
        async change_http_access_log_notification(value) {
            utils.save_localstorage(utils.localstorage_keys.HTTP_ACCESS_LOG_NOTIFICATION, value);
        },
        async change_dns_log_notification(value) {
            utils.save_localstorage(utils.localstorage_keys.DNS_LOG_NOTIFICATION, value);
        }
    }
};
</script>

<style scoped>

</style>