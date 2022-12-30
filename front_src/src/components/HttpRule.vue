<template>
    <div>
        <el-row type="flex" justify="center" style="margin-top: 20px; margin-bottom: 100px">
            <el-col :span="22">
                <div class="grid-content">
                    <el-card v-loading="rule_loading">
                        <template>
                            <div style="text-align: left; margin-left: 10px">
                                <el-button type="primary" size="mini" @click="add_catalog">新建分类
                                </el-button>
                                <el-button type="primary" size="mini" @click="refresh_rules">刷新
                                </el-button>
                            </div>

                            <el-table
                                ref="table"
                                :data="this.rules"
                                :tree-props="{children: 'rules'}"
                                :indent="0"
                                @expand-change="this.row_expand_change"
                                @row-dblclick="this.switch_row_expand"
                                style="width: 100%;"
                                row-key="index"
                                default-expand-all
                                row-class-name="less-table-padding">
                                <el-table-column
                                    prop="catalog_name"
                                    label="分类"
                                    class-name="rule_col"
                                    show-overflow-tooltip>
                                    <template slot-scope="scope">
                                        <template v-if="!scope.row.is_catalog">
                                            <template v-if="scope.row.editing">
                                                <el-select v-model="scope.row.catalog_id" placeholder="" size="mini" :disabled="!scope.row.editing">
                                                    <el-option
                                                        v-for="item in catalog_options"
                                                        :key="item.value"
                                                        :label="item.label"
                                                        :value="item.value">
                                                    </el-option>
                                                </el-select>
                                            </template>
                                        </template>
                                        <template v-else>
                                            <template v-if="scope.row.rules !== undefined && scope.row.rules.length === 0 ">
                                                <div class="el-table__expand-icon" style="display: inline-block; width: 20px; line-height: 20px; height: 20px; text-align: center; margin-right: 3px" onclick="this.class">
                                                    <i class="el-icon-arrow-down"></i>
                                                </div>
                                            </template>
                                            {{ scope.row.catalog_name }}
                                        </template>
                                    </template>
                                </el-table-column>
                                <!--
                                <el-table-column
                                    prop="create_time"
                                    align="center"
                                    label="创建日期"
                                    class-name="rule_col"
                                    width="180">
                                </el-table-column>
                                -->
                                <el-table-column
                                    prop="path"
                                    label="路径"
                                    class-name="rule_col"
                                    min-width="225px"
                                    show-overflow-tooltip>
                                    <template slot-scope="scope">
                                        <template v-if="scope.row.editing">
                                            <el-input v-model="scope.row.path" size="mini"></el-input>
                                        </template>
                                        <template v-else>
                                            {{ scope.row.path }}
                                        </template>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="filename"
                                    class-name="rule_col"
                                    label="文件名"
                                    show-overflow-tooltip
                                    min-width="200px">
                                    <template slot-scope="scope">
                                        <template v-if="scope.row.editing">
                                            <el-autocomplete v-model="scope.row.filename" :fetch-suggestions="fetch_upload_files" size="mini"></el-autocomplete>
                                        </template>
                                        <template v-else>
                                            {{ scope.row.filename }}
                                        </template>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="comment"
                                    class-name="rule_col"
                                    label="备注"
                                    show-overflow-tooltip>
                                    <template slot-scope="scope">
                                        <template v-if="scope.row.editing">
                                            <el-input v-model="scope.row.comment" size="mini"></el-input>
                                        </template>
                                        <template v-else>
                                            {{ scope.row.comment }}
                                        </template>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="write_log"
                                    align="center"
                                    class-name="rule_col"
                                    label="记录日志"
                                    width="110px">
                                    <template slot-scope="scope">
                                        <template v-if="!scope.row.is_catalog">
                                            <el-switch v-model="scope.row.write_log" :disabled="!scope.row.editing">
                                            </el-switch>
                                        </template>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="send_mail"
                                    align="center"
                                    class-name="rule_col"
                                    label="发送邮件"
                                    width="110px">
                                    <template slot-scope="scope">
                                        <template v-if="!scope.row.is_catalog">
                                            <el-switch v-model="scope.row.send_mail" :disabled="!scope.row.editing">
                                            </el-switch>
                                        </template>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="dynamic_template"
                                    align="center"
                                    class-name="rule_col"
                                    label="规则类型"
                                    width="140px">
                                    <template slot-scope="scope">
                                        <template v-if="!scope.row.is_catalog">
                                            <el-select v-model="scope.row.rule_type" placeholder="" size="mini" :disabled="!scope.row.editing">
                                                <el-option
                                                    v-for="item in rule_type_options"
                                                    :key="item.value"
                                                    :label="item.label"
                                                    :value="item.value">
                                                </el-option>
                                            </el-select>
                                        </template>
                                    </template>
                                </el-table-column>
                                <el-table-column label="操作" width="300" align="center">
                                    <template slot-scope="scope">
                                        <template v-if="!scope.row.is_catalog">
                                            <el-button type="primary" size="mini" @click="edit_file(scope.row)">编辑文件
                                            </el-button>
                                            <template v-if="!scope.row.editing">
                                                <el-button type="primary" size="mini" @click="start_edit(scope.row)">编辑规则
                                                </el-button>
                                            </template>
                                            <template v-else>
                                                <el-button type="success" size="mini" @click="commit_edit(scope.row)">保存规则
                                                </el-button>
                                            </template>
                                            <el-button type="danger" size="mini" @click="delete_rule(scope.row)">删除
                                            </el-button>
                                        </template>
                                        <template v-else>
                                            <el-button type="primary" size="mini" @click="show_add_rule(scope.row)">新建规则
                                            </el-button>
                                            <el-button type="danger" size="mini" @click="delete_catalog(scope.row)">删除
                                            </el-button>
                                        </template>
                                    </template>
                                </el-table-column>
                            </el-table>
                        </template>
                    </el-card>
                </div>
            </el-col>
        </el-row>

        <el-dialog
            title="新建规则"
            :visible.sync="add_rule_dialog_visible"
            :close-on-click-modal="false"
            width="30%"
            >
            <div>
                <label>路径</label>:<br>
                <el-input v-model="add_rule_form.path" placeholder="/test" style="margin-top: 10px"></el-input>
            </div>
            <div style="margin-top: 10px">
                <label>映射文件</label>:<br>
                <el-autocomplete v-model="add_rule_form.filename" :fetch-suggestions="fetch_upload_files"></el-autocomplete>
            </div>
            <div style="margin-top: 10px">
                <label>记录日志</label>:<br>
                <el-switch v-model="add_rule_form.write_log" style="margin-top: 10px"></el-switch>
            </div>
            <div style="margin-top: 10px">
                <label>发送邮件</label>:<br>
                <el-switch v-model="add_rule_form.send_mail" style="margin-top: 10px"></el-switch>
            </div>
            <div style="margin-top: 10px">
                <label>规则类型</label>:<br>
                <el-select v-model="add_rule_form.rule_type" style="margin-top: 10px" placeholder="请选择">
                    <el-option
                        v-for="item in rule_type_options"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value">
                    </el-option>
                </el-select>
            </div>
            <div style="margin-top: 10px">
                <label>备注</label>:<br>
                <el-input v-model="add_rule_form.comment" style="margin-top: 10px"></el-input>
            </div>
            <div style="margin-top: 30px; text-align: right">
                <el-button @click="cancel_add_rule">取消</el-button>
                <el-button type="primary" @click="add_rule">确定</el-button>
            </div>
        </el-dialog>

        <el-dialog
            title="编辑文件"
            :visible.sync="editor_file_dialog_visible"
            :close-on-click-modal="false"
            width="90%" top="30px"
            custom-class="no_upper_padding">
            <el-row type="flex" justify="space-between" style="margin-bottom: 10px">
                <el-col :span="20" style="align-self: center">
                  {{ editor_curr_filename }}
                </el-col>
                <el-col :span="4" style="text-align: right">
                    <el-button type="primary" style="display: inline" @click="submit_file(false)">保存</el-button>
                    <el-button type="primary" style="display: inline" @click="submit_file(true)">保存并退出</el-button>
                </el-col>
            </el-row>

            <MonacoEditor ref="editor" v-model="editor_content" v-loading="editor_loading"
                          :filename="editor_curr_filename" :amd-require="editor_require"
                          style="min-height: 80vh; border: 1px darkgray solid;"
                          :readonly="editor_readonly"
                          :options="{automaticLayout: true, scrollBeyondLastLine: true}" />
        </el-dialog>
    </div>
</template>

<script>
import http_rule from "../class/HttpRule";
import http_rule_catalog from "@/class/HttpRuleCatalog";
import Vue from "vue";
import file from "../class/UploadFile";
import utils from "../class/Utils";
import request from "../class/Request";
import upload_file from "../class/UploadFile";


export default {
    name: "HttpRule",
    data() {
        return {
            rules: [],
            catalog_options: [],
            last_edit_index: null,
            last_edit_content: {
                path: null,
                comment: null,
                filename: null,
                write_log: null,
                send_mail: null,
                catalog_id: null,
                rule_type: null
            },
            add_rule_dialog_visible: false,
            add_rule_form: {
                path: "",
                comment: "",
                filename: "",
                write_log: true,
                send_mail: false,
                catalog_id: -1,
                rule_type: utils.rule_type.RULE_TYPE_STATIC_FILE
            },
            rule_loading: false,
            rule_type_options: [{
                value: utils.rule_type.RULE_TYPE_STATIC_FILE,
                label: '静态文件'
            }, {
                value: utils.rule_type.RULE_TYPE_DYNAMIC_SCRIPT,
                label: '动态脚本'
            }],
            suggestions_files: null,

            editor_file_dialog_visible: false,
            editor_loading: false,
            editor_curr_filename: "",
            editor_content: "",
            editor_require: window.monacoRequire,
            editor_readonly: false,
        };
    },
    async mounted() {
        this.refresh_rules();
    },
    methods: {
        async refresh_rules() {
            this.rule_loading = true;
            this.catalog_options = [];

            let rules = await http_rule.get_rules();
            let catalogs = await http_rule_catalog.get_catalogs();

            let catalogs_id_to_object = {};
            let index = 1;
            for (let key in catalogs) {
                let catalog = catalogs[key];

                catalog.index = index;

                catalog.is_catalog = true;
                catalog.rules = [];
                catalogs_id_to_object[catalog.catalog_id] = catalog;
                this.catalog_options.push({'value': catalog.catalog_id, 'label': catalog.catalog_name});

                index += 1;
            }

            for (let key in rules) {
                let rule = rules[key];
                rule.index = index;

                rule.is_catalog = false;
                rule.editing = false;
                catalogs_id_to_object[rule.catalog_id].rules.push(rule);

                index += 1;
            }
            this.rules = catalogs;

            let no_expand_row_key = this.get_no_expand_row_keys();
            this.rules.forEach((row) => {
                // 记忆折叠的历史
                if (no_expand_row_key.indexOf(row.catalog_name) !== -1) {
                    setTimeout(() => {
                        if (this.$refs.table) {
                            this.$refs.table.toggleRowExpansion(row, false);
                        }
                    }, 0);
                }
            });

            this.rule_loading = false;
        },
        get_no_expand_row_keys() {
            return Object.keys(utils.load_localstorage(utils.localstorage_keys.RULE_NO_EXPAND_ROW_KEYS, {}));
        },
        row_expand_change(row, expanded) {
            let current_no_expand_rows = utils.load_localstorage(utils.localstorage_keys.RULE_NO_EXPAND_ROW_KEYS, {});
            if (!expanded) {
                current_no_expand_rows[row.catalog_name] = true;
            } else {
                delete current_no_expand_rows[row.catalog_name];
            }
            utils.save_localstorage(utils.localstorage_keys.RULE_NO_EXPAND_ROW_KEYS, current_no_expand_rows);
        },
        switch_row_expand(row) {
            this.$refs.table.toggleRowExpansion(row);
        },
        start_edit(row) {
            if (this.last_edit_index != null && this.last_edit_index != row.index) {
                this.rules[this.last_edit_index].editing = false;
            }
            if (this.last_edit_index != row.index) {
                for (let key in this.last_edit_content) {
                    this.last_edit_content[key] = row[key];
                }
            }
            row.editing = true;
            this.last_edit_index = row.index;
        },
        async commit_edit(row) {
            if (row.editing) {
                let modified = {};
                modified.rule_id = row.rule_id;
                for (let key in this.last_edit_content) {
                    if (this.last_edit_content[key] !== row[key]) {
                        modified[key] = row[key];
                    }
                }
                if (Object.keys(modified).length > 1) {
                    if (await http_rule.modify_rule(modified)) {
                        this.$message.success("修改成功");
                        this.last_edit_index = null;
                    } else {
                        this.$message.error("修改失败");
                        for (let key in this.last_edit_content) {
                            row[key] = this.last_edit_content[key];
                        }
                    }
                    this.refresh_rules();
                } else {
                    this.$message.warning("没有检测到变化");
                }
                row.editing = false;
            }
        },
        async delete_rule(row) {
            this.$confirm('确定删除该规则?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                if (await http_rule.delete_rule(row.rule_id)) {
                    this.refresh_rules();
                    this.$message.success("删除成功");
                } else {
                    this.$message.error("删除失败");
                }
            }).catch(() => {
            });
        },
        cancel_add_rule() {
            this.add_rule_dialog_visible = false;
        },
        show_add_rule(row) {
            for (let key in this.add_rule_form) {
                this.add_rule_form[key] = "";
            }

            this.add_rule_form.write_log = true;
            this.add_rule_form.send_mail = false;

            this.add_rule_form.rule_type = utils.rule_type.RULE_TYPE_STATIC_FILE;
            this.add_rule_form.catalog_id = row.catalog_id;

            this.add_rule_dialog_visible = true;
        },
        async add_rule() {
            if (this.add_rule_form.path.trim() != "" && this.add_rule_form.filename.trim() != "") {
                let res = await http_rule.add_rule(this.add_rule_form);
                this.add_rule_form.path = this.add_rule_form.path.trim();
                this.add_rule_form.filename = this.add_rule_form.filename.trim();
                if (res.code === request.CODE_SUCCESS) {
                    this.$message.success("创建成功");
                    this.refresh_rules();
                    this.cancel_add_rule();
                    this.add_rule_dialog_visible = false;
                } else {
                    this.$message.error(res.msg);
                }
            } else {
                this.$message.error("请至少填写路径和映射文件");
            }
        },
        async edit_file(row) {
            this.editor_curr_filename = row.filename;
            this.editor_loading = true;
            this.editor_file_dialog_visible = true;
            let resp = (await file.preview_file(this.editor_curr_filename));
            if (resp.code === request.CODE_SUCCESS) {
                this.editor_content = resp.payload;
                this.editor_readonly = false;
            } else {
                this.editor_content = resp.msg;
                this.editor_readonly = true;
            }
            this.editor_loading = false;
        },
        async submit_file(exit) {
            if (this.editor_curr_filename.trim() === "") {
                this.$message.error("文件名不能为空");
                return;
            }
            let content = this.$refs.editor.value;
            if (this.editor_readonly) {
                this.editor_file_dialog_visible = false;
                return;
            }
            let res = await file.modify_file(this.editor_curr_filename, null, content);
            if (res.code === request.CODE_SUCCESS) {
                if (exit) {
                    this.editor_file_dialog_visible = false;
                }
                this.$message.success(res.msg);
            } else {
                this.$message.error(res.msg);
            }
        },
        async add_catalog() {
            this.$prompt('请输入新建分类名称', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                closeOnClickModal: false
            }).then(async ({ value }) => {
                let res = await http_rule_catalog.add_catalog(value);
                if (res.code === request.CODE_SUCCESS) {
                    this.refresh_rules();
                    this.$message.success(res.msg);
                } else {
                    this.$message.error(res.msg);
                }
            }).catch(() => {
            });
        },
        async delete_catalog(row) {
            this.$confirm('确定删除该分类? <br>注意该分类下的规则也会被删除.', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning',
                dangerouslyUseHTMLString: true
            }).then(async () => {
                if (await http_rule_catalog.delete_catalog(row.catalog_id)) {
                    this.refresh_rules();
                    this.$message.success("删除成功");
                } else {
                    this.$message.error("删除失败");
                }
            }).catch(() => {
            });
        },
        async fetch_upload_files(query, cb) {
            function walk_files(files) {
                let result = [];
                for (let key in files) {
                    if (files[key].children) {
                        result = result.concat(walk_files(files[key].children))
                    } else {
                        result.push({"value": files[key].path});
                    }
                }
                return result;
            }

            if (this.suggestions_files === null) {
                let files = await upload_file.get_files();
                this.suggestions_files = walk_files(files);
            }

            let filter = (path) => {
                return (path.value.toLowerCase().indexOf(query.toLowerCase()) === 0);
            };

            let suggestions = query ? this.suggestions_files.filter(filter) : this.suggestions_files;

            // 调用 callback 返回建议列表的数据
            cb(suggestions);
        }
    }
};
</script>

<style>
.no_upper_padding > .el-dialog__body {
    padding-top: 0px !important;
}
</style>
