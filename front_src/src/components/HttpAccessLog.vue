<template>
    <div style="padding-right: 10px; padding-left: 10px; padding-top: 10px;" class="log_table">
        <el-table
            :data="this.logs"
            border
            style="width: 100%;"
            @row-click="popover_show"
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
                prop="ua"
                align="center"
                class-name="log_col"
                label="User-Agent"
                width="260">
            </el-table-column>
            <el-table-column
                prop="method"
                align="center"
                class-name="log_col"
                label="方法"
                width="55">
            </el-table-column>
            <el-table-column
                prop="data"
                class-name="log_col"
                min-width="500">
                <template slot="header">
                    数据 <a href="javascript:" style="color: dodgerblue; " @click="show_filter">过滤</a>
                    <a href="#/HttpAccessLog" style="color: dodgerblue; margin-left: 5px" @click="get_logs(0)">刷新</a>
                </template>
                <template slot-scope="scope">
                    <el-popover
                        placement="top-start"
                        trigger="manual"
                        v-model="popover_visible[scope.row.index]">
                        <div style="width: 100%" slot="reference">
                            {{ scope.row.data }}
                        </div>
                        <div slot>
                            <el-row type="flex" justify="space-between" align="middle">
                                <el-col :span="8">
                                    <span style="text-align: center; vertical-align: center"><b>详细数据</b></span>
                                </el-col>
                                <el-col :span="8" style="text-align: right">
                                    <el-button type="danger" size="mini" @click="popover_close(scope.row)">关闭
                                    </el-button>
                                </el-col>
                            </el-row>
                            <el-divider content-position="left">MISC</el-divider>
                            <json-viewer
                                :value="scope.row.misc"
                                :expand-depth="5"
                                copyable
                                boxed
                                sort
                            ></json-viewer>
                            <el-divider content-position="left">HEADER</el-divider>
                            <json-viewer
                                :value="scope.row.header"
                                :expand-depth="5"
                                copyable
                                boxed
                                sort
                            ></json-viewer>
                            <template v-if="Object.keys(scope.row.arg).length !== 0">
                                <el-divider content-position="left">GET</el-divider>
                                <json-viewer
                                    :value="scope.row.arg"
                                    :expand-depth="5"
                                    copyable
                                    boxed
                                    sort
                                ></json-viewer>
                            </template>
                            <template v-if="scope.row.body_type === utils.body_type.BODY_TYPE_NORMAL">
                                <template v-if="scope.row.raw_data">
                                    <el-divider content-position="left">POST</el-divider>
                                    <el-row type="flex" justify="center">
                                        <el-col :span="16" style="text-align: center">
                                            {{ scope.row.body_json['RAW_DATA'] }}
                                        </el-col>
                                    </el-row>
                                </template>
                                <template v-else>
                                    <template
                                        v-if="scope.row.body_json !== '' && typeof(scope.row.body_json) === 'object' && Object.keys(scope.row.body_json).length !== 0">
                                        <el-divider content-position="left">POST</el-divider>
                                        <json-viewer
                                            :value="scope.row.body_json"
                                            :expand-depth="5"
                                            copyable
                                            boxed
                                            sort
                                        ></json-viewer>
                                    </template>
                                </template>
                            </template>
                            <template v-if="scope.row.body_type === utils.body_type.BODY_TYPE_ESCAPED">
                                <el-divider content-position="left">POST</el-divider>
                                <el-row type="flex" justify="center">
                                    <el-col :span="16" style="text-align: center">
                                        <a href="javascript:" style="color: dodgerblue;"
                                           v-clipboard:success="copy_success"
                                           v-clipboard:copy="scope.row.body_json['ESCAPED_DATA']">数据存在无法解码内容, 点击复制 base64 后内容</a>
                                    </el-col>
                                </el-row>
                            </template>
                            <template v-if="scope.row.body_type === utils.body_type.BODY_TYPE_TOO_LONG">
                                <el-divider content-position="left">POST</el-divider>
                                <el-row type="flex" justify="center">
                                    <el-col :span="16" style="text-align: center">
                                      <a href="javascript:" style="color: dodgerblue;"
                                         v-clipboard:success="copy_success"
                                         v-clipboard:copy="scope.row.body_json['TOO_LONG_DATA']">数据过长, 点击复制截断后内容</a>
                                    </el-col>
                                </el-row>
                            </template>

                            <template v-if="Object.keys(scope.row.file).length !== 0">
                                <el-divider content-position="left">FILE</el-divider>
                                <template v-for="(item, key, index) in scope.row.file">
                                    <el-row type="flex" justify="center" :key="index">
                                        <el-col :span="16" style="text-align: center">
                                            key = [{{ key }}] | filename = [{{ item.filename }}]
                                            <template v-if="item.save_name !== null">
                                                : <a href="javascript:" style="color: dodgerblue"
                                                     @click="download_file(item.save_name, item.filename)">下载</a>
                                                <a href="javascript:" style="color: dodgerblue; margin-left: 10px"
                                                   @click="preview_file(item.save_name)">预览</a>
                                            </template>
                                            <template v-else>
                                                : 未开启文件保存
                                            </template>
                                        </el-col>
                                    </el-row>
                                </template>
                            </template>
                            <div style="margin-top: 10px"></div>
                        </div>
                    </el-popover>
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
                <label>路径</label>:<br>
                <el-input v-model="filter.path" placeholder="/" style="margin-top: 10px"></el-input>
            </div>
            <div style="margin-top: 10px">
                <label>方法</label>:<br>
                <el-input v-model="filter.method" placeholder="GET" style="margin-top: 10px"></el-input>
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
import http_access_log from "../class/HttpAccessLog";
import UAParser from "ua-parser-js";
import qs from "querystring";
import request from "../class/Request";
import Vue from 'vue';
import time from '../class/Utils';
import utils from "../class/Utils";

export default {
    name: 'HttpAccessLog',
    data() {
        return {
            logs: [],
            curr_page: 0,
            log_per_page: 30,
            total_page: 0,
            preview_file_content: "",
            preview_dialog_visible: false,
            filter_dialog_visible: false,
            popover_visible: [],
            curr_popover_index: null,
            log_last_id: null,
            log_loading: true,
            filter: {
                client_ip: null,
                path: null,
                method: null,
                time_before: null,
                time_after: null
            },
            utils: utils
        };
    },
    async mounted() {
        this.curr_page = 0;
        this.log_per_page = utils.load_localstorage(utils.localstorage_keys.HTTP_ACCESS_LOG_PER_PAGE, 30);
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

            let paged = await http_access_log.get_logs(page, this.log_per_page, temp_filter);

            this.curr_page = paged.curr_page;
            if (paged.total_page === 0) {
                this.total_page = 1;
            } else {
                this.total_page = paged.total_page;
            }

            this.popover_visible = [];
            for (let key in paged.payload) {
                this.popover_visible.push(false);

                let log = paged.payload[key];
                log.log_time = time.to_local_time(log.log_time);

                log.index = key;
                log.misc = {
                    'client_ip': log.client_ip,
                    'client_port': log.client_port,
                    'time': log.log_time,
                    'region': log.region,
                    'path': log.path,
                    'log_id': log.log_id
                };

                log.ua = this.format_ua(log.header['User-Agent']);

                let data = {};
                if (Object.keys(log.arg).length) {
                    data['GET'] = Object.keys(log.arg);
                }
                if (Object.keys(log.file).length) {
                    data['FILE'] = Object.keys(log.file);
                }
                if (log.header['Cookie']) {
                    data['COOKIE'] = this.format_cookie(log.header['Cookie']);
                }

                let content_type = log.header['Content-Type'];
                let body_keys = log.body;
                let body_raw = log.body;
                let body_json = {};

                switch (log.body_type) {
                    case utils.body_type.BODY_TYPE_NORMAL:
                        if (content_type) {
                            content_type = content_type.toLowerCase().split(";")[0].trim();

                            switch (content_type) {
                                case "application/x-www-form-urlencoded":
                                    try {
                                        body_json = qs.parse(body_raw);
                                        body_keys = Object.keys(qs.parse(body_raw));
                                    } catch (e) {
                                        body_json = {"QS_PARSE_ERROR": body_raw};
                                        body_keys = ["QS_PARSE_ERROR"];
                                    }
                                    break;
                                case "multipart/form-data":
                                case "application/json":
                                    try {
                                        body_json = JSON.parse(body_raw);
                                        body_keys = Object.keys(body_json);
                                    } catch (e) {
                                        body_json = {"JSON_PARSE_ERROR": body_raw};
                                        body_keys = ["JSON_PARSE_ERROR"];
                                    }
                                    break;
                                default:
                                    if (body_raw.length > 0) {
                                        // Content-Type 没有识别出来
                                        log.raw_data = true;
                                        body_json = {"RAW_DATA": body_raw};
                                        body_keys = ["RAW_DATA"];
                                    }
                            }
                        } else {
                            if (body_raw.length > 0) {
                                // Content-Type 不存在
                                log.raw_data = true;
                                body_json = {"RAW_DATA": body_raw};
                                body_keys = ["RAW_DATA"];
                            }
                        }
                        break;
                    case utils.body_type.BODY_TYPE_ESCAPED:
                        body_json = {"ESCAPED_DATA": body_raw};
                        body_keys = ["ESCAPED_DATA"];
                        break;
                    case utils.body_type.BODY_TYPE_TOO_LONG:
                        body_json = {"TOO_LONG_DATA": body_raw};
                        body_keys = ["TOO_LONG_DATA"];
                        break;
                }

                if (body_keys.length > 0) {
                    data['POST'] = body_keys;
                }
                log.data = JSON.stringify(data);
                log.body_json = body_json;
            }
            this.logs = paged.payload;
            this.log_loading = false;
        },
        format_ua(ua) {
            if (ua) {
                let result = '';
                let parser = new UAParser(ua);
                let browser = parser.getBrowser();
                let os = parser.getOS();
                if (os['name']) {
                    result += os['name'];
                    if (os['version']) {
                        result += '/';
                        result += os['version'];
                    }
                }
                if (browser['name']) {
                    if (result !== '') {
                        result += ' ';
                    }
                    result += browser['name'];
                    if (browser['version']) {
                        result += '/';
                        result += browser['version'];
                    }
                }
                if (result === '') {
                    result = '未知浏览器';
                }
                return result;
            } else {
                return '未知浏览器';
            }
        },
        format_cookie(cookies) {
            cookies = cookies.split(';');
            let keys = [];
            cookies.map(function (cookie) {
                if (cookie.length > 0) {
                    let index = cookie.indexOf('=');
                    if (index !== -1) {
                        keys = keys.concat(cookie.slice(0, index));
                    } else {
                        keys = keys.concat(cookie);
                    }
                }
            });
            return keys;
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
            utils.save_localstorage(utils.localstorage_keys.HTTP_ACCESS_LOG_PER_PAGE, size);
            this.get_logs(0);
        },
        async download_file(filename, original_filename) {
            let ret = await request.download_file('/temp_file/download', {'filename': filename}, {}, original_filename);
            if (!ret) {
                this.$message.error("文件不存在");
            }
        },
        async preview_file(filename) {
            let ret = await request.post('/temp_file/preview', {'filename': filename}, {}, filename);
            if (ret.code === request.CODE_SUCCESS) {
                this.preview_file_content = ret.payload;
                this.preview_dialog_visible = true;
            } else {
                this.$message.error("文件存在无法解码内容, 无法预览");
            }
        },
        popover_show(row) {
            if (this.curr_popover_index !== null) {
                Vue.set(this.popover_visible, String(this.curr_popover_index), false);
            }
            if (this.curr_popover_index !== row.index) {
                Vue.set(this.popover_visible, row.index, true);
                this.curr_popover_index = row.index;
            } else {
                this.curr_popover_index = null;
            }
        },
        popover_close(row) {
            Vue.set(this.popover_visible, row.index, false);
        },
        show_filter() {
            this.filter_dialog_visible = true;
        },
        clear_filter() {
            this.filter.time_after = null;
            this.filter.time_before = null;
            this.filter.method = null;
            this.filter.path = null;
            this.filter.client_ip = null;
        },
        set_filter() {
            this.filter_dialog_visible = false;
            this.get_logs(0);
        },
        copy_success() {
            this.$message.success("复制成功");
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
