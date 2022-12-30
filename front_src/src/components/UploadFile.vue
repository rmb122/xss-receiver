<template>
    <div>
        <el-row type="flex" justify="center" style="margin-top: 20px; margin-bottom: 100px">
            <el-col :span="22">
                <div class="grid-content">
                    <el-card v-loading="file_loading">
                        <template>
                            <el-button type="primary" size="mini" style="margin-left: 10px; display: inline" @click="new_directory">
                                新建文件夹
                            </el-button>
                            <el-upload
                                action=""
                                :data="''"
                                :show-file-list="false"
                                :http-request="upload_file"
                                style="display: inline; margin-left: 10px">
                                <el-button type="primary" size="mini">上传文件</el-button>
                            </el-upload>
                            <el-button type="primary" size="mini" style="margin-left: 10px; display: inline" @click="new_file">
                                新建文件
                            </el-button>
                            <el-button type="primary" size="mini" style="display: inline; margin-left: 10px"  @click="refresh_file">刷新
                            </el-button>

                            <el-table
                                ref="table"
                                :data="this.files"
                                :tree-props="{children: 'children'}"
                                :indent="48"
                                @expand-change="this.row_expand_change"
                                @row-dblclick="this.switch_row_expand"
                                default-expand-all
                                row-key="path"
                                row-class-name="less-table-padding"
                                style="width: 100%;">
                                <el-table-column
                                    prop="filename"
                                    label="文件名">
                                    <template slot-scope="scope">
                                        <template v-if="!scope.row.dir">
                                            <div style="padding-left: 23px; display: inline-block"></div>
                                            {{ scope.row.filename }}
                                        </template>
                                        <template v-else>
                                            <template v-if="scope.row.children !== undefined && scope.row.children.length === 0 ">
                                                <div class="el-table__expand-icon el-table__expand-icon--expanded" style="display: inline-block; width: 20px; line-height: 20px; height: 20px; text-align: center; margin-right: 3px">
                                                    <i class="el-icon-arrow-right"></i>
                                                </div>
                                            </template>
                                            {{ scope.row.filename }}/
                                        </template>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="size"
                                    label="大小"
                                    align="center"
                                    class-name=""
                                    width="100">
                                    <template slot-scope="scope">
                                        <template v-if="!scope.row.dir">
                                           {{ scope.row.size }}
                                        </template>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="mttime"
                                    align="center"
                                    label="修改日期"
                                    class-name=""
                                    width="200">
                                    <template slot-scope="scope">
                                        <template v-if="!scope.row.dir">
                                            {{ scope.row.mttime }}
                                        </template>
                                    </template>
                                </el-table-column>
                                <el-table-column label="操作" width="380" align="center">
                                    <template slot-scope="scope">
                                        <template v-if="!scope.row.dir">
                                            <el-button type="primary" size="mini" @click="edit_file(scope.row)">编辑
                                            </el-button>
                                            <el-button type="success" size="mini" @click="download_file(scope.row)">下载
                                            </el-button>
                                            <el-button type="danger" size="mini" @click="delete_file(scope.row)">删除
                                            </el-button>
                                        </template>
                                        <template v-else>
                                            <el-upload
                                                action=""
                                                :data="scope.row.filename"
                                                :show-file-list="false"
                                                :http-request="upload_file"
                                                style="display: inline; margin-right: 10px">
                                              <el-button type="primary" size="mini">上传文件</el-button>
                                            </el-upload>
                                            <el-button type="primary" size="mini" @click="new_file_with_directory(scope.row)">新建文件
                                            </el-button>
                                            <el-button type="primary" size="mini" @click="modify_directory(scope.row)">重命名
                                            </el-button>
                                            <el-button type="danger" size="mini" @click="delete_directory(scope.row)">删除
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
            title="编辑文件"
            :visible.sync="editor_file_dialog_visible"
            :close-on-click-modal="false"
            width="90%" top="30px"
            custom-class="file_dialog">
            <el-row type="flex" justify="space-between">
                <el-col :span="20">
                    <el-input v-model="editor_curr_filename" style="margin-bottom: 10px"></el-input>
                </el-col>
                <el-col :span="4" style="text-align: right">
                    <el-button type="primary" style="display: inline" @click="submit_file(false)">保存</el-button>
                    <el-button type="primary" style="display: inline" @click="submit_file(true)">保存并退出</el-button>
                </el-col>
            </el-row>

          <MonacoEditor ref="editor" v-model="editor_content" v-loading="editor_loading"
                        :filename="editor_curr_filename" :amd-require="editor_require"
                        style="min-height: 80vh; border: 1px solid #DCDFE6;"
                        :readonly="editor_readonly"
                        :options="{automaticLayout: true, scrollBeyondLastLine: true}" />
        </el-dialog>
    </div>
</template>

<script>
import file from "../class/UploadFile";
import request from "../class/Request";
import utils from "@/class/Utils";

export default {
    name: "UploadFile",
    data() {
        return {
            file_loading: false,
            files: [],

            editor_new_file: false,
            editor_file_dialog_visible: false,
            editor_loading: false,
            editor_curr_filename: "",
            editor_original_filename: "",
            editor_content: "",
            editor_require: window.monacoRequire,
            editor_readonly: false,
        };
    },
    async mounted() {
        this.refresh_file();
    },
    methods: {
        async refresh_file() {
            this.file_loading = true;

            let files = await file.get_files();

            let process_file_list = (files) => {
                for (let key in files) {
                    files[key].size = this.convert_size(files[key].size);
                    let time = new Date(files[key].mttime * 1000);
                    files[key].mttime = time.toLocaleDateString() + " " + time.toLocaleTimeString();

                    if (files[key].children) {
                        files[key].children = process_file_list(files[key].children)
                    }
                }
                return files
            }

            this.files = process_file_list(files);

            let no_expand_row_key = this.get_no_expand_row_keys();
            this.files.forEach((row) => {
                // 记忆折叠的历史
                if (no_expand_row_key.indexOf(row.path) !== -1) {
                    setTimeout(() => {
                        if (this.$refs.table) {
                            this.$refs.table.toggleRowExpansion(row, false);
                        }
                    }, 0);
                }
            });

            this.file_loading = false;
        },
        async upload_file(req) {
            if (req.data !== "") {
                // rename file
                req.file = new File([req.file], req.data + "/" + req.file.name, {
                  type: req.file.type,
                  lastModified: req.file.lastModified,
                });
            }

            let res = await file.upload_file(req.file);
            if (res.code === request.CODE_SUCCESS) {
                this.$message.success(res.msg);
            } else {
                this.$message.error(res.msg);
            }
            this.refresh_file();
        },
        get_no_expand_row_keys() {
          return Object.keys(utils.load_localstorage(utils.localstorage_keys.FILE_NO_EXPAND_ROW_KEYS, {}));
        },
        row_expand_change(row, expanded) {
            let current_no_expand_rows = utils.load_localstorage(utils.localstorage_keys.FILE_NO_EXPAND_ROW_KEYS, {});
            if (!expanded) {
                current_no_expand_rows[row.path] = true;
            } else {
                delete current_no_expand_rows[row.path];
            }
            utils.save_localstorage(utils.localstorage_keys.FILE_NO_EXPAND_ROW_KEYS, current_no_expand_rows);
        },
        switch_row_expand(row) {
          this.$refs.table.toggleRowExpansion(row);
        },
        convert_size(size) {
            let i = -1;
            let units = [' KB', ' MB', ' GB', ' TB', 'PB', 'EB', 'ZB', 'YB'];
            do {
                size = size / 1024;
                i++;
            } while (size > 1024);
            return Math.max(size, 0.1).toFixed(1) + units[i];
        },
        async edit_file(row) {
            this.editor_original_filename = row.path;
            this.editor_curr_filename = row.path;

            this.editor_loading = true;
            this.editor_file_dialog_visible = true;
            this.editor_new_file = false;

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

            if (this.editor_new_file) {
                let f = new File([new Blob([this.editor_content])], this.editor_curr_filename);
                let res = await file.upload_file(f);
                if (res.code === request.CODE_SUCCESS) {
                    if (exit) {
                      this.editor_file_dialog_visible = false;
                    } else {
                      // 如果不退出, 切换到编辑模式
                      this.editor_original_filename = this.editor_curr_filename;
                      this.editor_new_file = false;
                    }
                    this.refresh_file();
                    this.$message.success(res.msg);
                } else {
                    this.$message.error(res.msg);
                }
            } else {
                let new_filename = "";
                if (this.editor_original_filename === this.editor_curr_filename) {
                    new_filename = null;
                } else {
                    new_filename = this.editor_curr_filename;
                }
                let content = this.editor_content;
                if (this.editor_readonly) {
                    content = null;
                }
                let res = await file.modify_file(this.editor_original_filename, new_filename, content);
                if (res.code === request.CODE_SUCCESS) {
                    if (exit) {
                        this.editor_file_dialog_visible = false;
                    } else {
                        this.editor_original_filename = this.editor_curr_filename;
                    }

                    this.refresh_file();
                    this.$message.success(res.msg);
                } else {
                    this.$message.error(res.msg);
                }
            }
        },
        new_file() {
            this.editor_new_file = true;
            this.editor_curr_filename = "";
            this.editor_file_dialog_visible = true;
            this.editor_content = "";
            this.editor_readonly = false;
        },
        new_file_with_directory(row) {
            this.editor_new_file = true;
            this.editor_curr_filename = row.path + "/";
            this.editor_file_dialog_visible = true;
            this.editor_content = "";
            this.editor_readonly = false;
        },
        async delete_file(row) {
            this.$confirm('确定删除该文件?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                let filename = row.path;
                let res = await file.delete_file(filename);
                if (res.code === request.CODE_SUCCESS) {
                    this.refresh_file();
                    this.$message.success(res.msg);
                } else {
                    this.$message.error(res.msg);
                }
            }).catch(() => {
            });
        },
        async download_file(row) {
            let filename = row.path;
            let ret = await request.download_file('/upload_file/download', {'filename': filename}, {}, filename);
            if (!ret) {
                this.$message.error("文件不存在");
            }
        },
        async new_directory() {
            this.$prompt('请输入文件夹名称<br>注意: 只支持创建一层文件夹', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                closeOnClickModal: false,
                dangerouslyUseHTMLString: true
            }).then(async ({ value }) => {
                let res = await file.add_directory(value)
                if (res.code === request.CODE_SUCCESS) {
                    this.refresh_file();
                    this.$message.success(res.msg);
                } else {
                    this.$message.error(res.msg);
                }
            }).catch(() => {
            });
        },
        async delete_directory(row) {
            this.$confirm('确定删除该文件夹? <br>注意该文件夹下的文件也会被删除.', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning',
                dangerouslyUseHTMLString: true
            }).then(async () => {
                if (await file.delete_directory(row.filename)) {
                    this.refresh_file();
                    this.$message.success("删除成功");
                } else {
                    this.$message.error("删除失败");
                }
            }).catch(() => {
            });
        },
        async modify_directory(row) {
            this.$prompt('请输入新文件夹名称', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                closeOnClickModal: false,
            }).then(async ({ value }) => {
                let res = await file.modify_directory(row.filename, value)
                if (res.code === request.CODE_SUCCESS) {
                    this.refresh_file();
                    this.$message.success(res.msg);
                } else {
                    this.$message.error(res.msg);
                }
            }).catch(() => {
            });
        }
    }
};
</script>

<style>
</style>
