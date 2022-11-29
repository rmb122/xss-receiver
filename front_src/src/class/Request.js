import axios from 'axios';
import utils from "@/class/Utils";
import user from "@/class/User";

class Request {
    base

    instance;

    jwt = false;
    blocked = [];

    CODE_SUCCESS = 200;
    CODE_FAILED = 201;
    CODE_INVALID = 400;

    constructor() {
        if (!process.env.NODE_ENV || process.env.NODE_ENV === 'development') {
            this.base = 'http://127.0.0.1:5000/admin/api';
        } else {
            this.base = './api';
        }

        this.instance = axios.create({
            baseURL: this.base,
            timeout: 10000,
        });
    }

    set_jwt(jwt) {
        this.jwt = jwt;
        utils.save_localstorage(utils.localstorage_keys.AUTHORIZATION, jwt);
    }

    load_jwt() {
        let jwt = utils.load_localstorage(utils.localstorage_keys.AUTHORIZATION, false);
        if (jwt) {
            this.jwt = jwt;
            return true;
        } else {
            return false;
        }
    }

    get(path, data = {}, config = {}) {
        return new Promise(async (resolve) => {
            if (!this.jwt) {
                this.load_jwt();
            }

            if (config['headers'] === undefined) {
                config['headers'] = {};
            }
            if (this.jwt) {
                config['headers']['Authorization'] = this.jwt;
            }
            config['params'] = data;
            try {
                let res = await this.instance.get(path, config);
                resolve(res.data);
            } catch (e) {
                let res = {"data": {"code": 400, "msg": "系统内部错误"}};
                resolve(res.data);
            }
        });
    }

    post(path, data = {}, config = {}) {
        return new Promise(async (resolve) => {
            if (!this.jwt) {
                this.load_jwt();
            }

            if (config['headers'] === undefined) {
                config['headers'] = {};
            }
            if (this.jwt) {
                config['headers']['Authorization'] = this.jwt;
            }
            try {
                let res = await this.instance.post(path, data, config);
                resolve(res.data);
            } catch (e) {
                let res = {"data": {"code": 400, "msg": "系统内部错误"}};
                resolve(res.data);
            }
        });
    }

    download_file(path, data = {}, config = {}, filename) {
        return new Promise(async (resolve) => {
            if (!this.jwt) {
                this.load_jwt();
            }

            if (config['headers'] === undefined) {
                config['headers'] = {};
            }
            if (this.jwt) {
                config['headers']['Authorization'] = this.jwt;
            }
            config['responseType'] = 'arraybuffer'

            try {
                let res = await this.instance.post(path, data, config);
                if (res.status === 200) {
                    let blob = new Blob([res.data], {
                        type: res.headers['content-type']
                    });
                    let link = document.createElement('a');
                    link.href = window.URL.createObjectURL(blob);
                    link.download = filename;
                    link.click();
                    window.URL.revokeObjectURL(link.href);
                    resolve(true);
                } else {
                    resolve(false);
                }
            } catch (e) {
                resolve(false);
            }
        });
    }

    async open_websocket() {
        let base_url = utils.parse_url(this.base);
        let protocol = "";

        if (base_url.protocol === "http:") {
            protocol = "ws://";
        } else if (base_url.protocol === "https:") {
            protocol = "wss://";
        }

        return new WebSocket(protocol + base_url.host + base_url.pathname + "/websocket?token=" + encodeURIComponent(user.get_jwt()));
    }
}

let request = new Request();
export default request;
