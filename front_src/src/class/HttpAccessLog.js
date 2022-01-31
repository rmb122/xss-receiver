import request from "./Request";

class HttpAccessLog {


    async get_logs(page, page_size, filter) {
        return (await request.post('/http_access_log/list', {
            'page': page,
            'page_size': page_size,
            'filter': filter
        })).payload;
    }

    async get_last_id() {
        return (await request.get('/http_access_log/get_last_id')).payload;
    }
}

let http_access_log = new HttpAccessLog();
export default http_access_log;
