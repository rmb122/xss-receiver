<template>
    <div style="padding-right: 10px; padding-left: 10px; padding-top: 10px;" class="log_table">
        <el-table
            :data="this.logs"
            border
            style="width: 100%;"
            v-loading="log_loading">
            <el-table-column
                prop="log_id"
                label="ID"
                align="center"
                class-name="log_col"
                width="70">
            </el-table-column>
            <el-table-column
                prop="log_time"
                label="时间"
                align="center"
                class-name="log_col"
                width="180">
            </el-table-column>
            <el-table-column
                prop="client_ip"
                align="center"
                class-name="log_col"
                label="IP"
                width="160">
            </el-table-column>
            <el-table-column
                prop="region"
                align="center"
                class-name="log_col"
                label="地区"
                width="185">
            </el-table-column>
            <el-table-column
                prop="transaction_id"
                align="center"
                class-name="log_col"
                label="TID"
                width="80">
            </el-table-column>
            <el-table-column
                prop="dns_type"
                align="center"
                class-name="log_col"
                label="Type"
                width="100">
            </el-table-column>
            <el-table-column
                prop="dns_class"
                align="center"
                class-name="log_col"
                label="Class"
                width="100">
            </el-table-column>
            <el-table-column
                prop="domain"
                align="left"
                class-name="log_col"
                label="请求域名">
                <template slot="header">
                    请求域名 <a href="javascript:" style="color: dodgerblue; " @click="show_filter">过滤</a>
                    <a href="#/DNSLog" style="color: dodgerblue; margin-left: 5px" @click="get_logs(0)">刷新</a>
                </template>
            </el-table-column>
        </el-table>

        <el-dialog
            title="预览"
            :visible.sync="preview_dialog_visible"
            :close-on-click-modal="false"
            width="80%">
            <el-input
                type="textarea"
                :rows="20"
                placeholder=""
                v-model="preview_file_content">
            </el-input>
        </el-dialog>

        <el-dialog
            title="过滤"
            :visible.sync="filter_dialog_visible"
            :close-on-click-modal="false"
            width="30%">
            <div>
                <label>IP</label>:<br>
                <el-input v-model="filter.client_ip" placeholder="1.1.1.1" style="margin-top: 10px"></el-input>
            </div>
            <div style="margin-top: 10px">
                <label>请求域名</label>:<br>
                <el-input v-model="filter.domain" placeholder="aaa.com" style="margin-top: 10px"></el-input>
            </div>
            <div style="margin-top: 10px">
                <label>域名类型</label>:<br>
                <el-input v-model="filter.dns_type" placeholder="TXT" style="margin-top: 10px"></el-input>
            </div>
            <div style="margin-top: 10px">
                <label>在这之前</label>:<br>
                <el-date-picker v-model="filter.time_before" type="datetime" placeholder="选择日期时间"
                                style="margin-top: 10px"></el-date-picker>
            </div>
            <div style="margin-top: 10px">
                <label>在这之后</label>:<br>
                <el-date-picker v-model="filter.time_after" type="datetime" placeholder="选择日期时间"
                                style="margin-top: 10px"></el-date-picker>
            </div>
            <div style="margin-top: 30px; text-align: center">
                <el-button @click="clear_filter">清空</el-button>
                <el-button type="primary" @click="set_filter">确定</el-button>
            </div>
        </el-dialog>

        <el-row type="flex" justify="center" align="middle">
            <el-col :span="16">
                <el-pagination
                    background
                    layout="sizes, prev, pager, next, jumper"
                    style="margin-top: 20px; margin-bottom: 20px; text-align: center"
                    :page-count="this.total_page"
                    :current-page="this.curr_page + 1"
                    :page-sizes="[30, 50, 100, 200]"
                    :page-size="this.log_per_page"
                    @prev-click="prev_page"
                    @next-click="next_page"
                    @size-change="change_log_per_page"
                    @current-change="change_page">
                </el-pagination>
            </el-col>
        </el-row>
    </div>
</template>

<script>
import dns_log from "../class/DNSLog";
import time from '../class/Utils';
import utils from "../class/Utils";

export default {
    name: 'DNSLog',
    data() {
        return {
            logs: [],
            curr_page: 0,
            log_per_page: 30,
            total_page: 0,
            log_last_id: null,
            log_loading: true,
            filter_dialog_visible: false,
            filter: {
                client_ip: null,
                domain: null,
                dns_type: null,
                time_before: null,
                time_after: null
            },
        };
    },
    async mounted() {
        this.curr_page = 0;
        this.log_per_page = utils.load_localstorage(utils.localstorage_keys.DNS_LOG_PER_PAGE, 30);
        this.get_logs(0);
    },
    methods: {
        async get_logs(page) {
            document.title = "管理面板";

            this.log_loading = true;
            let temp_filter = {};

            for (let key in this.filter) {
                if (this.filter[key] !== null) {
                    if (typeof (this.filter[key]) === 'string' && this.filter[key].trim() !== '') {
                        temp_filter[key] = this.filter[key].trim();
                    } else if (typeof (this.filter[key]) === 'object') {
                        temp_filter[key] = time.to_utc_time(this.filter[key]);
                    }
                }
            }

            if (temp_filter.hasOwnProperty("dns_type")) {
                temp_filter['dns_type'] = utils.dns_type_reverse_map[temp_filter['dns_type'].toUpperCase()] || -1;
            }

            let paged = await dns_log.get_logs(page, this.log_per_page, temp_filter);

            this.curr_page = paged.curr_page;
            if (paged.total_page === 0) {
                this.total_page = 1;
            } else {
                this.total_page = paged.total_page;
            }

            this.logs = paged.payload.map((e) => {
                e.transaction_id = '0x' + e.transaction_id.toString(16);
                e.dns_type = utils.dns_type_map[e.dns_type] || "UNKNOWN";
                e.dns_class = utils.dns_class_map[e.dns_class] || "UNKNOWN";
                return e
            });
            this.log_loading = false;
        },
        next_page() {
            this.curr_page += 1;
            this.get_logs(this.curr_page);
        },
        prev_page() {
            this.curr_page -= 1;
            this.get_logs(this.curr_page);
        },
        change_page(page) {
            page = page - 1;
            if (page != this.curr_page) {
                this.curr_page = page;
                this.get_logs(this.curr_page);
            }
        },
        change_log_per_page(size) {
            this.log_per_page = size;
            utils.save_localstorage(utils.localstorage_keys.DNS_LOG_PER_PAGE, size);
            this.get_logs(0);
        },
        show_filter() {
            this.filter_dialog_visible = true;
        },
        clear_filter() {
            this.filter.time_after = null;
            this.filter.time_before = null;
            this.filter.dns_type = null;
            this.filter.domain = null;
            this.filter.client_ip = null;
        },
        set_filter() {
            this.filter_dialog_visible = false;
            this.get_logs(0);
        }
    }
};
</script>

<style>
.log_col {
    padding: 0px !important;
    color: #303133;
    font-size: small;
}
</style>
