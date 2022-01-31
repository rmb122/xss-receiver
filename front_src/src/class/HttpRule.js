import request from "./Request";

class HttpRule {
    async get_rules() {
        return (await request.get('/http_rule/list')).payload;
    }

    async modify_rule(modified) {
        let res = await request.post('/http_rule/modify', modified);
        return res.code === 200;
    }

    async delete_rule(rule_id) {
        let res = await request.post('/http_rule/delete', {'rule_id': rule_id});
        return res.code === 200;
    }

    async add_rule(rule) {
        return await request.post('/http_rule/add', rule);
    }
}

let http_rule = new HttpRule();
export default http_rule;
