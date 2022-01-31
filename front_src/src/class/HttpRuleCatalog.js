import request from "@/class/Request";

class HttpRuleCatalog {
    async get_catalogs() {
        return (await request.get('/http_rule_catalog/list')).payload;
    }

    async delete_catalog(catalog_id) {
        return (await request.post('/http_rule_catalog/delete', {'catalog_id': catalog_id}));
    }

    async add_catalog(catalog_name) {
        return (await request.post('/http_rule_catalog/add', {'catalog_name': catalog_name}));
    }
}

let http_rule_catalog = new HttpRuleCatalog();
export default http_rule_catalog;