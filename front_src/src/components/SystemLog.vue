<template>
    <el-row type="flex" justify="center" style="margin-top: 20px; margin-bottom: 100px">
        <el-col :span="22">
            <div class="grid-content">
                <el-card v-loading="loading">
                    <template>
                        <el-input v-model="search" size="mini" placeholder="输入关键字搜索"/>
                        <el-table
                            :data="this.system_logs.filter(data => !search || data.log_content.toLowerCase().includes(search.toLowerCase()))"
                            style="width: 100%;"
                            row-class-name="less-table-padding">
                            <el-table-column
                                prop="log_id"
                                label="ID"
                                align="center"
                                width="70">
                            </el-table-column>
                            <el-table-column
                                prop="log_content"
                                align="center"
                                label="内容"
                                show-overflow-tooltip>
                            </el-table-column>
                            <el-table-column
                                prop="log_time"
                                align="center"
                                label="创建日期"
                                width="180">
                            </el-table-column>
                        </el-table>
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
                    </template>
                </el-card>
            </div>
        </el-col>
    </el-row>
</template>

<script>
import request from "../class/Request";
import utils from "../class/Utils";

export default {
    name: "SystemLog",
    data() {
        return {
            loading: false,
            search: "",
            system_logs: [],
            total_page: 0,
            log_per_page: 30,
            curr_page: 1
        };
    },
    async mounted() {
        this.loading = true;

        this.log_per_page = utils.load_localstorage(utils.localstorage_keys.SYSTEM_LOG_PER_PAGE, 30);
        await this.get_page(0);

        this.loading = false;
    },
    methods: {
        change_page(page) {
            this.curr_page = page - 1;
            this.get_page(this.curr_page);
        },
        async get_page(page_number) {
            let paged_result = (await request.post('/system_log/list', {
                'page': page_number,
                'page_size': this.log_per_page
            })).payload;
            let logs = paged_result.payload;
            for (let key in logs) {
                logs[key].log_time = utils.to_local_time(logs[key].log_time);
            }
            this.system_logs = logs;
            this.curr_page = paged_result.curr_page;
            this.total_page = paged_result.total_page;
        },
        prev_page() {
            this.curr_page -= 1;
            this.get_page(this.curr_page);
        },
        next_page() {
            this.curr_page += 1;
            this.get_page(this.curr_page);
        },
        change_log_per_page(size) {
            this.log_per_page = size;
            utils.save_localstorage(utils.localstorage_keys.SYSTEM_LOG_PER_PAGE, size);
            this.get_page(this.curr_page);
        }
    }
};
</script>

<style scoped>

</style>