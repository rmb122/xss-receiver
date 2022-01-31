import request from "./Request";

class DNSLog {


    async get_logs(page, page_size, filter) {
        return (await request.post('/dns_log/list', {
            'page': page,
            'page_size': page_size,
            'filter': filter
        })).payload;
    }

    async get_last_id() {
        return (await request.get('/dns_log/get_last_id')).payload;
    }
}

let dns_log = new DNSLog();
export default dns_log;