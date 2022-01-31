import request from "./Request";

class Config {
    async clean_temp_file() {
        return await request.post('/temp_file/delete_all', {'delete': true});
    }

    async clean_http_access_log() {
        return await request.post('/http_access_log/delete_all', {'delete': true});
    }

    async clean_dns_log() {
        return await request.post('/dns_log/delete_all', {'delete': true});
    }

    async get_config() {
        return await request.get('/config/list');
    }

    async modify_config(key, value) {
        return await request.post('/config/modify', {'key': key, 'value': value});
    }
}

let config = new Config();
export default config;